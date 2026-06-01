import base64
import re
from datetime import datetime, timedelta, timezone

import structlog
from google.oauth2.credentials import Credentials

from app.config import get_settings
from app.extractors.base import BaseExtractor, ExtractedContact, ExtractedTask
from app.extractors.gmail_patterns import (
    classify_concur_message,
    classify_gmail_thread,
    classify_redhat_direct,
    external_participants,
    is_from_user,
    parse_email_date,
)
from app.services.google_client import gmail_service
from app.utils.domain import email_domain

logger = structlog.get_logger()


class GmailExtractor(BaseExtractor):
    name = "gmail"

    def __init__(self, creds: Credentials, user_email: str):
        self.creds = creds
        self.user_email = user_email.lower()
        self.user_domain = email_domain(user_email) or ""
        self.service = gmail_service(creds)
        settings = get_settings()
        self.window_days = settings.task_window_days
        self.stale_days = settings.stale_thread_days

    async def extract_contacts(self) -> list[ExtractedContact]:
        contacts: dict[str, ExtractedContact] = {}
        after = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y/%m/%d")
        query = f"after:{after}"
        page_token = None
        while True:
            resp = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=100, pageToken=page_token)
                .execute()
            )
            for msg_meta in resp.get("messages", []):
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_meta["id"], format="metadata")
                    .execute()
                )
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                for key in ("From", "To", "Cc"):
                    for match in re.finditer(r"[\w.+-]+@[\w.-]+\.\w+", headers.get(key, "")):
                        email = match.group(0).lower()
                        if email == self.user_email:
                            continue
                        if email not in contacts:
                            name = None
                            raw = headers.get(key, "")
                            name_m = re.search(
                                rf"([^<,]+)\s*<{re.escape(email)}>", raw, re.I
                            )
                            if name_m:
                                name = name_m.group(1).strip().strip('"')
                            contacts[email] = ExtractedContact(
                                email=email,
                                display_name=name,
                                source_id=msg_meta["id"],
                            )
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        logger.info("gmail_contacts_extracted", count=len(contacts))
        return list(contacts.values())

    def _thread_messages(self, thread_id: str) -> list[dict]:
        thread = (
            self.service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
        return thread.get("messages", [])

    async def extract_tasks(self) -> list[ExtractedTask]:
        tasks: list[ExtractedTask] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)
        after = cutoff.strftime("%Y/%m/%d")
        query = f"after:{after} -in:spam -in:trash"
        page_token = None
        seen_threads: set[str] = set()

        while True:
            resp = (
                self.service.users()
                .threads()
                .list(userId="me", q=query, maxResults=50, pageToken=page_token)
                .execute()
            )
            for th_meta in resp.get("threads", []):
                tid = th_meta["id"]
                if tid in seen_threads:
                    continue
                seen_threads.add(tid)
                messages = self._thread_messages(tid)
                if not messages:
                    continue

                messages_sorted = sorted(
                    messages,
                    key=lambda m: int(m.get("internalDate", 0)),
                )
                last = messages_sorted[-1]
                headers = {
                    h["name"]: h["value"]
                    for h in last.get("payload", {}).get("headers", [])
                }
                subject = headers.get("Subject", "(no subject)")
                snippet = last.get("snippet", "")
                from_hdr = headers.get("From", "")
                last_from_user = is_from_user(from_hdr, self.user_email)
                last_dt = datetime.fromtimestamp(
                    int(last.get("internalDate", 0)) / 1000, tz=timezone.utc
                )

                to_hdr = headers.get("To", "")
                externals = external_participants(
                    headers, self.user_email, self.user_domain
                )
                if not externals:
                    for m in messages_sorted:
                        h = {
                            x["name"]: x["value"]
                            for x in m.get("payload", {}).get("headers", [])
                        }
                        externals = external_participants(
                            h, self.user_email, self.user_domain
                        )
                        if externals:
                            break

                origin = f"https://mail.google.com/mail/u/0/#inbox/{tid}"
                now = datetime.now(timezone.utc)

                for task_type, suffix in classify_concur_message(
                    subject=subject, snippet=snippet, from_header=from_hdr
                ):
                    age_days = (now - last_dt).days if last_dt else 0
                    if age_days >= 7:
                        task_type = "concur_overdue"
                        suffix = "Concur / expense overdue"
                    tasks.append(
                        ExtractedTask(
                            source="gmail",
                            source_id=f"{tid}:{task_type}",
                            title=f"{subject} — {suffix}",
                            task_type=task_type,
                            badge_source="gmail",
                            description=snippet[:500],
                            origin_url=origin,
                            contact_emails=[],
                            company_domain=None,
                        )
                    )

                for task_type, suffix in classify_redhat_direct(
                    user_email=self.user_email,
                    from_header=from_hdr,
                    to_header=to_hdr,
                    subject=subject,
                    snippet=snippet,
                    last_from_user=last_from_user,
                ):
                    tasks.append(
                        ExtractedTask(
                            source="gmail",
                            source_id=f"{tid}:{task_type}",
                            title=f"{subject} — {suffix}",
                            task_type=task_type,
                            badge_source="gmail",
                            description=snippet[:500],
                            origin_url=origin,
                            contact_emails=[],
                            company_domain=None,
                        )
                    )

                if not externals:
                    continue

                customer_asked = False
                user_replied_after = False
                for m in messages_sorted:
                    h = {
                        x["name"]: x["value"]
                        for x in m.get("payload", {}).get("headers", [])
                    }
                    frm = h.get("From", "")
                    if not is_from_user(frm, self.user_email):
                        customer_asked = True
                        user_replied_after = False
                    else:
                        if customer_asked:
                            user_replied_after = True

                customer_asked_no_reply = customer_asked and not user_replied_after and last_from_user

                classifications = classify_gmail_thread(
                    user_email=self.user_email,
                    user_domain=self.user_domain,
                    last_from_user=last_from_user,
                    last_message_at=last_dt,
                    subject=subject,
                    snippet=snippet,
                    from_header=from_hdr,
                    has_user_reply_after_customer=user_replied_after,
                    customer_asked_no_reply=customer_asked_no_reply,
                    stale_days=self.stale_days,
                )
                if not classifications:
                    continue

                company_domain = None
                for em in externals:
                    d = email_domain(em)
                    if d and d != self.user_domain:
                        company_domain = d
                        break

                for task_type, suffix in classifications:
                    tasks.append(
                        ExtractedTask(
                            source="gmail",
                            source_id=f"{tid}:{task_type}",
                            title=f"{subject} — {suffix}",
                            task_type=task_type,
                            badge_source="gmail",
                            description=snippet[:500],
                            origin_url=origin,
                            contact_emails=externals[:5],
                            company_domain=company_domain,
                        )
                    )

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info("gmail_tasks_extracted", count=len(tasks))
        return tasks
