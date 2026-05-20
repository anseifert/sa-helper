import re
from datetime import datetime, timedelta, timezone

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.config import get_settings
from app.extractors.base import BaseExtractor, ExtractedContact, ExtractedTask
from app.services.google_client import drive_service
from app.utils.domain import email_domain

logger = structlog.get_logger()

# Comments API only applies to Google Workspace files (Docs/Sheets/Slides).
_WORKSPACE_MIMES = (
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
)
_COMMENTS_FIELDS = "comments(id,content,resolved,createdTime,author(displayName,emailAddress))"
_FILES_FIELDS = "files(id,name,webViewLink,mimeType,modifiedTime)"


def _author_dict(comment: dict) -> dict:
    author = comment.get("author")
    return author if isinstance(author, dict) else {}


def _drive_http_error_message(exc: HttpError) -> str:
    status = exc.resp.status
    if status == 403:
        return (
            "Drive API access denied (403). In Google Cloud Console enable "
            "'Google Drive API' for this project, then disconnect and reconnect "
            "Google in Settings."
        )
    return f"Drive API error ({status}): {exc.reason}"


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
        mime_filter = " or ".join(f"mimeType='{m}'" for m in _WORKSPACE_MIMES)

        try:
            files = (
                self.service.files()
                .list(
                    pageSize=30,
                    fields=f"nextPageToken,{_FILES_FIELDS}",
                    q=mime_filter,
                    orderBy="modifiedTime desc",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
        except HttpError as exc:
            logger.warning("drive_files_list_failed", status=exc.resp.status, reason=exc.reason)
            raise RuntimeError(_drive_http_error_message(exc)) from exc

        for f in files.get("files", []):
            fid = f.get("id")
            if not fid:
                continue
            try:
                tasks.extend(self._tasks_from_file_comments(f, fid, cutoff))
            except Exception:
                logger.warning("drive_file_skipped", file_id=fid, exc_info=True)
                continue

        logger.info("drive_tasks_extracted", count=len(tasks))
        return tasks

    def _tasks_from_file_comments(
        self, file_meta: dict, file_id: str, cutoff: datetime
    ) -> list[ExtractedTask]:
        tasks: list[ExtractedTask] = []
        try:
            comments = (
                self.service.comments()
                .list(
                    fileId=file_id,
                    fields=_COMMENTS_FIELDS,
                    pageSize=100,
                )
                .execute()
            )
        except HttpError as exc:
            # Comments unsupported or no access on this file — skip quietly.
            if exc.resp.status in (400, 403, 404):
                return []
            raise

        for c in comments.get("comments", []):
            try:
                task = self._comment_to_task(c, file_meta, file_id, cutoff)
                if task:
                    tasks.append(task)
            except Exception:
                logger.warning(
                    "drive_comment_skipped",
                    file_id=file_id,
                    comment_id=c.get("id"),
                    exc_info=True,
                )
        return tasks

    def _comment_to_task(
        self, c: dict, file_meta: dict, file_id: str, cutoff: datetime
    ) -> ExtractedTask | None:
        if c.get("resolved"):
            return None

        created = c.get("createdTime")
        if created:
            try:
                ct = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                return None
            if ct < cutoff:
                return None

        content = c.get("content") or ""
        author = _author_dict(c)
        author_email = (author.get("emailAddress") or "").lower()

        mention_hint = f"@{self.user_email.split('@')[0]}"
        if mention_hint not in content.lower() and "@mention" not in content.lower():
            if not re.search(r"@\w+", content):
                return None

        extern_domain = email_domain(author_email) if author_email else None
        if extern_domain and extern_domain == self.user_domain:
            return None

        comment_id = c.get("id")
        if not comment_id:
            return None

        return ExtractedTask(
            source="drive",
            source_id=f"{file_id}:comment:{comment_id}",
            title=f"Drive comment on {file_meta.get('name', 'file')}",
            task_type="drive_mention",
            badge_source="drive",
            description=content[:500],
            origin_url=file_meta.get("webViewLink"),
            contact_emails=[author_email] if author_email else [],
            company_domain=extern_domain,
        )
