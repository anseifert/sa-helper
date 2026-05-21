import secrets

from fastapi import HTTPException, Request, status

from app.config import get_settings

SESSION_AUTH_KEY = "authenticated"
SESSION_USER_KEY = "username"


def verify_app_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    if not settings.app_password:
        return False
    user_ok = secrets.compare_digest(
        (username or "").encode("utf-8"),
        settings.app_username.encode("utf-8"),
    )
    pass_ok = secrets.compare_digest(
        (password or "").encode("utf-8"),
        settings.app_password.encode("utf-8"),
    )
    return user_ok and pass_ok


def login_session(request: Request, username: str) -> None:
    request.session[SESSION_AUTH_KEY] = True
    request.session[SESSION_USER_KEY] = username


def logout_session(request: Request) -> None:
    request.session.clear()


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_AUTH_KEY))


async def require_auth(request: Request) -> str:
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return str(request.session.get(SESSION_USER_KEY) or get_settings().app_username)
