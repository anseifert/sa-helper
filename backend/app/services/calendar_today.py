import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.extractors.calendar import _calendar_http_error_message, _parse_event_start
from app.schemas.dashboard import TodayMeetingOut
from app.services.google_client import calendar_service, get_google_credentials
from app.utils.calendar_filter import (
    external_attendee_emails,
    internal_email_domain,
    meeting_has_external_attendee,
)
from app.utils.datetime_util import DEFAULT_TIMEZONE, ensure_utc, resolve_timezone

logger = structlog.get_logger()


def _parse_event_end(end: dict) -> datetime | None:
    if "dateTime" in end:
        raw = end["dateTime"]
        try:
            return ensure_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError:
            return None
    if "date" in end:
        try:
            return ensure_utc(datetime.fromisoformat(end["date"] + "T23:59:59+00:00"))
        except ValueError:
            return None
    return None


def _today_bounds(tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    now_local = datetime.now(tz)
    start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def _list_today_events(
    service: Resource,
    *,
    day_start: datetime,
    day_end: datetime,
    tz_name: str,
) -> dict:
    return (
        service.events()
        .list(
            calendarId="primary",
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
            timeZone=tz_name,
        )
        .execute()
    )


def _meeting_from_event(ev: dict, internal_domain: str) -> TodayMeetingOut | None:
    if ev.get("status") == "cancelled":
        return None
    if not meeting_has_external_attendee(ev, internal_domain):
        return None
    start_at = _parse_event_start(ev.get("start", {}))
    if not start_at:
        return None
    externals = external_attendee_emails(ev, internal_domain)
    if not externals:
        return None
    end_dt = _parse_event_end(ev.get("end") or {})
    return TodayMeetingOut(
        event_id=ev.get("id") or "",
        title=(ev.get("summary") or "Untitled meeting").strip(),
        start_at=start_at.isoformat(),
        end_at=end_dt.isoformat() if end_dt else None,
        external_emails=externals,
        html_link=ev.get("htmlLink"),
    )


async def fetch_today_external_meetings(
    session: AsyncSession,
) -> tuple[list[TodayMeetingOut], str | None]:
    """
    List today's calendar events that include at least one non-internal email.
    Meetings where every participant is @redhat.com (or there are no emails) are omitted.
    """
    creds = await get_google_credentials(session)
    if not creds:
        return [], "Connect Google in Settings to see today's calendar."

    settings = get_settings()
    internal_domain = internal_email_domain(settings.user_email)
    tz_name = resolve_timezone(settings.user_timezone)

    try:
        day_start, day_end = _today_bounds(tz_name)
    except Exception as e:
        logger.warning("today_meetings_timezone_failed", tz=tz_name, error=str(e))
        return [], (
            f"Invalid timezone '{settings.user_timezone or DEFAULT_TIMEZONE}'. "
            "Set USER_TIMEZONE to an IANA name like America/New_York."
        )

    service = calendar_service(creds)
    try:
        result = await asyncio.to_thread(
            _list_today_events,
            service,
            day_start=day_start,
            day_end=day_end,
            tz_name=tz_name,
        )
    except HttpError as exc:
        logger.warning("today_meetings_list_failed", status=exc.resp.status)
        return [], _calendar_http_error_message(exc)
    except Exception as e:
        logger.exception("today_meetings_list_failed")
        return [], f"Could not load today's calendar: {e}"

    meetings: list[TodayMeetingOut] = []
    for ev in result.get("items", []):
        try:
            meeting = _meeting_from_event(ev, internal_domain)
            if meeting:
                meetings.append(meeting)
        except Exception:
            logger.warning(
                "today_meeting_event_skipped",
                event_id=ev.get("id"),
                exc_info=True,
            )

    meetings.sort(key=lambda m: m.start_at)
    logger.info("today_external_meetings", count=len(meetings), domain=internal_domain, tz=tz_name)
    return meetings, None
