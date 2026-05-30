from pydantic import BaseModel


class OnboardingStatusOut(BaseModel):
    google_connected: bool
    last_sync_at: str | None
    onboarding_complete: bool
