import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

import structlog
from fastapi import Request
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crypto import encrypt_token
from app.models.oauth_token import OAuthToken

# Google often returns extra scopes (openid, email); avoid token exchange failures.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "0")

logger = structlog.get_logger()


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


def public_callback_url(request: Request) -> str:
    """Canonical OAuth callback URL for token exchange (must match Google Console)."""
    settings = get_settings()
    query = urlsplit(str(request.url)).query
    base = settings.google_redirect_uri.rstrip("/")
    return f"{base}?{query}" if query else base


def google_auth_url() -> str:
    flow = build_google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def _credential_expiry(creds) -> datetime | None:
    expiry = creds.expiry
    if not expiry:
        return None
    if expiry.tzinfo is None:
        return expiry.replace(tzinfo=timezone.utc)
    return expiry.astimezone(timezone.utc)


async def save_google_tokens(session: AsyncSession, authorization_response: str) -> None:
    if not authorization_response or "code=" not in authorization_response:
        raise ValueError("OAuth callback missing authorization code")

    flow = build_google_flow()
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    if not creds or not creds.token:
        raise ValueError("OAuth token exchange returned no access token")

    result = await session.execute(
        select(OAuthToken).where(OAuthToken.provider == "google")
    )
    row = result.scalar_one_or_none()
    expires = _credential_expiry(creds)
    scope_str = " ".join(creds.scopes or [])

    if row:
        row.access_token_enc = encrypt_token(creds.token)
        row.refresh_token_enc = (
            encrypt_token(creds.refresh_token) if creds.refresh_token else row.refresh_token_enc
        )
        row.expires_at = expires
        row.scopes = scope_str
    else:
        session.add(
            OAuthToken(
                provider="google",
                access_token_enc=encrypt_token(creds.token),
                refresh_token_enc=encrypt_token(creds.refresh_token) if creds.refresh_token else None,
                expires_at=expires,
                scopes=scope_str,
            )
        )
    await session.flush()
    logger.info("google_oauth_tokens_saved", scopes=scope_str)
