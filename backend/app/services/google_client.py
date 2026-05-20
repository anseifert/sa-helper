from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import decrypt_token, encrypt_token
from app.models.oauth_token import OAuthToken


async def get_google_credentials(session: AsyncSession) -> Credentials | None:
    result = await session.execute(
        select(OAuthToken).where(OAuthToken.provider == "google")
    )
    row = result.scalar_one_or_none()
    if not row:
        return None

    settings = get_settings()
    creds = Credentials(
        token=decrypt_token(row.access_token_enc),
        refresh_token=decrypt_token(row.refresh_token_enc) if row.refresh_token_enc else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=row.scopes.split() if row.scopes else settings.google_scopes.split(),
    )
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request

        creds.refresh(Request())
        row.access_token_enc = encrypt_token(creds.token)
        if creds.expiry:
            row.expires_at = creds.expiry.replace(tzinfo=timezone.utc)
        await session.flush()
    return creds


def gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def calendar_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def drive_service(creds: Credentials):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def is_google_connected(session: AsyncSession) -> bool:
    creds = await get_google_credentials(session)
    return creds is not None
