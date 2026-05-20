import re
from datetime import datetime, timedelta, timezone

import structlog
from google.oauth2.credentials import Credentials

from app.config import get_settings
from app.extractors.base import BaseExtractor, ExtractedContact, ExtractedTask
from app.services.google_client import drive_service
from app.utils.domain import email_domain

logger = structlog.get_logger()


class DriveExtractor(BaseExtractor):
    name = "drive"

    def __init__(self, creds: Credentials, user_email: str):
        self.creds = creds
        self.user_email = user_email.lower()
        self.user_domain = email_domain(user_email) or ""
        self.service = drive_service(creds)
        settings = get_settings()
        self.window_days = settings.task_window_days

    async def extract_contacts(self) -> list[ExtractedContact]:
        return []

    async def extract_tasks(self) -> list[ExtractedTask]:
        tasks: list[ExtractedTask] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)

        files = (
            self.service.files()
            .list(
                pageSize=30,
                fields="files(id,name,webViewLink,modifiedTime)",
                q="mimeType!='application/vnd.google-apps.folder'",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        for f in files.get("files", []):
            fid = f["id"]
            try:
                comments = (
                    self.service.comments()
                    .list(fileId=fid, fields="comments(id,content,author,resolved,createdTime)")
                    .execute()
                )
            except Exception:
                continue

            for c in comments.get("comments", []):
                if c.get("resolved"):
                    continue
                created = c.get("createdTime")
                if created:
                    ct = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if ct < cutoff:
                        continue
                content = c.get("content", "")
                author = c.get("author", {}).get("displayName", "Someone")
                if f"@{self.user_email.split('@')[0]}" not in content.lower() and "@mention" not in content.lower():
                    if not re.search(r"@\w+", content):
                        continue

                author_email = c.get("author", {}).get("emailAddress", "").lower()
                extern_domain = email_domain(author_email) if author_email else None
                if extern_domain == self.user_domain:
                    continue

                tasks.append(
                    ExtractedTask(
                        source="drive",
                        source_id=f"{fid}:comment:{c['id']}",
                        title=f"Drive comment on {f.get('name', 'file')}",
                        task_type="drive_mention",
                        badge_source="drive",
                        description=content[:500],
                        origin_url=f.get("webViewLink"),
                        contact_emails=[author_email] if author_email else [],
                        company_domain=extern_domain,
                    )
                )

        logger.info("drive_tasks_extracted", count=len(tasks))
        return tasks
