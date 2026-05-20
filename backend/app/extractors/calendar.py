import re
from datetime import datetime, timedelta, timezone

import structlog
from google.oauth2.credentials import Credentials

from app.config import get_settings
from app.extractors.base import BaseExtractor, ExtractedContact, ExtractedTask
from app.services.google_client import calendar_service
from app.utils.domain import email_domain

logger = structlog.get_logger()

ACTION_PATTERNS = [
    (re.compile(r"\b(action item|todo|to-do|follow up|follow-up)\s*:\s*(.+)", re.I), "action_item"),
    (re.compile(r"^\s*[-*]\s*\[\s*\]\s*(.+)$", re.M), "checkbox_item"),
    (re.compile(r"\b(prepare|send|review|complete|draft)\s+(.{5,60})", re.I), "prep_item"),
]


class CalendarExtractor(BaseExtractor):
    name = "calendar"

    def __init__(self, creds: Credentials, user_email: str):
        self.creds = creds
        self.user_email = user_email.lower()
        self.user_domain = email_domain(user_email) or ""
        self.service = calendar_service(creds)
        settings = get_settings()
        self.window_days = settings.task_window_days

    async def extract_contacts(self) -> list[ExtractedContact]:
        return []

    def _parse_action_items(self, description: str, event_title: str) -> list[str]:
        items: list[str] = []
        text = description or ""
        for pattern, _ in ACTION_PATTERNS:
            for m in pattern.finditer(text):
                item = (m.group(1) if m.lastindex else m.group(0)).strip()
                if len(item) > 3:
                    items.append(item[:200])
        if not items and description and len(description) > 20:
            # fallback: first line as action hint
            first = description.strip().split("\n")[0][:120]
            if re.search(r"\b(action|todo|follow)\b", first, re.I):
                items.append(first)
        return items[:5]

    async def extract_tasks(self) -> list[ExtractedTask]:
        tasks: list[ExtractedTask] = []
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=self.window_days)).isoformat()

        events = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )

        for ev in events.get("items", []):
            eid = ev["id"]
            title = ev.get("summary", "Calendar event")
            desc = ev.get("description", "") or ""
            link = ev.get("htmlLink")
            start = ev.get("start", {})
            due = None
            if "dateTime" in start:
                due = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            elif "date" in start:
                due = datetime.fromisoformat(start["date"] + "T00:00:00+00:00")

            attendees = [
                a.get("email", "").lower()
                for a in ev.get("attendees", [])
                if a.get("email") and a.get("email").lower() != self.user_email
            ]
            externals = [
                e
                for e in attendees
                if email_domain(e) and email_domain(e) != self.user_domain
            ]
            company_domain = email_domain(externals[0]) if externals else None

            action_items = self._parse_action_items(desc, title)
            for i, item in enumerate(action_items):
                tasks.append(
                    ExtractedTask(
                        source="calendar",
                        source_id=f"{eid}:action:{i}",
                        title=f"{title} — {item}",
                        task_type="calendar_action",
                        badge_source="calendar",
                        description=item,
                        origin_url=link,
                        due_at=due,
                        contact_emails=externals[:5],
                        company_domain=company_domain,
                    )
                )

            if externals and due and due < now + timedelta(days=3):
                tasks.append(
                    ExtractedTask(
                        source="calendar",
                        source_id=f"{eid}:upcoming",
                        title=f"Upcoming: {title}",
                        task_type="schedule_meeting",
                        badge_source="calendar",
                        description=desc[:300] if desc else None,
                        origin_url=link,
                        due_at=due,
                        contact_emails=externals[:5],
                        company_domain=company_domain,
                    )
                )

        logger.info("calendar_tasks_extracted", count=len(tasks))
        return tasks
