from datetime import datetime, timezone
from urllib.parse import urlencode

from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import encrypt_token
from app.models.oauth_token import OAuthToken


def build_google_flow() -> Flow:
    settings = get_settings()
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=settings.google_scopes.split(),
        redirect_uri=settings.google_redirect_uri,
    )


def google_auth_url() -> str:
    flow = build_google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


async def save_google_tokens(session: AsyncSession, code: str) -> None:
    flow = build_google_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials

    result = await session.execute(
        select(OAuthToken).where(OAuthToken.provider == "google")
    )
    row = result.scalar_one_or_none()
    expires = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None

    if row:
        row.access_token_enc = encrypt_token(creds.token)
        row.refresh_token_enc = (
            encrypt_token(creds.refresh_token) if creds.refresh_token else row.refresh_token_enc
        )
        row.expires_at = expires
        row.scopes = " ".join(creds.scopes or [])
    else:
        session.add(
            OAuthToken(
                provider="google",
                access_token_enc=encrypt_token(creds.token),
                refresh_token_enc=encrypt_token(creds.refresh_token) if creds.refresh_token else None,
                expires_at=expires,
                scopes=" ".join(creds.scopes or []),
            )
        )
    await session.flush()
