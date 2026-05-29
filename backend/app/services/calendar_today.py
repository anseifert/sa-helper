from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
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
from app.utils.datetime_util import ensure_utc

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


def _today_bounds(tz_name: str) -> tuple[datetime, datetime, ZoneInfo]:
    tz = ZoneInfo(tz_name)
    now_local = datetime.now(tz)
    start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end, tz


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
    tz_name = settings.user_timezone or "America/New_York"
    day_start, day_end, _ = _today_bounds(tz_name)

    service = calendar_service(creds)
    try:
        result = (
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
    except HttpError as exc:
        logger.warning("today_meetings_list_failed", status=exc.resp.status)
        return [], _calendar_http_error_message(exc)

    meetings: list[TodayMeetingOut] = []
    for ev in result.get("items", []):
        if ev.get("status") == "cancelled":
            continue
        if not meeting_has_external_attendee(ev, internal_domain):
            continue
        start_at = _parse_event_start(ev.get("start", {}))
        if not start_at:
            continue
        externals = external_attendee_emails(ev, internal_domain)
        if not externals:
            continue
        meetings.append(
            TodayMeetingOut(
                event_id=ev.get("id") or "",
                title=(ev.get("summary") or "Untitled meeting").strip(),
                start_at=start_at.isoformat(),
                end_at=_parse_event_end(ev.get("end", {})).isoformat()
                if ev.get("end")
                else None,
                external_emails=externals,
                html_link=ev.get("htmlLink"),
            )
        )

    meetings.sort(key=lambda m: m.start_at)
    logger.info("today_external_meetings", count=len(meetings), domain=internal_domain)
    return meetings, None
