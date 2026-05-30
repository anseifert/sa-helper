from fastapi import APIRouter, Depends

from app.api.v1 import (
    assets,
    auth,
    companies,
    contacts,
    dashboard,
    health,
    onboarding,
    oauth,
    recommendations,
    settings,
    sync,
    tasks,
    webhooks,
)
from app.auth import require_auth

router = APIRouter(prefix="/api/v1")

# Public: health probe, login, Google OAuth callback chain
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

# Protected: requires session cookie from POST /api/v1/auth/login
protected = APIRouter(dependencies=[Depends(require_auth)])
protected.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
protected.include_router(assets.router, prefix="/assets", tags=["assets"])
protected.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
protected.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
protected.include_router(companies.router, prefix="/companies", tags=["companies"])
protected.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
protected.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
protected.include_router(sync.router, prefix="/sync", tags=["sync"])
protected.include_router(settings.router, prefix="/settings", tags=["settings"])
protected.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(protected)
