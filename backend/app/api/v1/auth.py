from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    SESSION_USER_KEY,
    is_authenticated,
    login_session,
    logout_session,
    verify_app_credentials,
)
from app.config import get_settings
from app.schemas.auth import AuthStatusOut, LoginRequest

router = APIRouter()


@router.post("/login", response_model=AuthStatusOut)
async def login(body: LoginRequest, request: Request) -> AuthStatusOut:
    settings = get_settings()
    if not settings.app_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login disabled: set APP_PASSWORD in .env",
        )
    if not verify_app_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    login_session(request, body.username)
    return AuthStatusOut(
        authenticated=True,
        username=body.username,
        login_configured=True,
    )


@router.post("/logout", response_model=AuthStatusOut)
async def logout(request: Request) -> AuthStatusOut:
    logout_session(request)
    return AuthStatusOut(
        authenticated=False,
        username=None,
        login_configured=bool(get_settings().app_password),
    )


@router.get("/me", response_model=AuthStatusOut)
async def auth_me(request: Request) -> AuthStatusOut:
    settings = get_settings()
    configured = bool(settings.app_password)
    if is_authenticated(request):
        return AuthStatusOut(
            authenticated=True,
            username=str(
                request.session.get(SESSION_USER_KEY) or settings.app_username
            ),
            login_configured=configured,
        )
    return AuthStatusOut(
        authenticated=False,
        username=None,
        login_configured=configured,
    )
