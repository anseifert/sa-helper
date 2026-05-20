from fastapi import APIRouter

from app.api.v1 import (
    companies,
    contacts,
    dashboard,
    health,
    oauth,
    recommendations,
    settings,
    sync,
    tasks,
    webhooks,
)

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
router.include_router(companies.router, prefix="/companies", tags=["companies"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(sync.router, prefix="/sync", tags=["sync"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
