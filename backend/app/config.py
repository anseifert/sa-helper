from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SA Task Hub"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./data/sa_task_hub.db"
    secret_key: str = "change-me-in-production"
    fernet_key: str = ""  # base64 url-safe 32-byte key; generated on first run if empty

    # App login (required in production — protects UI and API)
    app_username: str = "admin"
    app_password: str = ""
    auth_cookie_secure: bool = False  # auto-enabled when frontend_url uses https

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/oauth/google/callback"
    google_scopes: str = (
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/calendar.readonly "
        "https://www.googleapis.com/auth/drive.readonly"
    )

    slack_bot_token: str = ""
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    sync_interval_minutes: int = 60
    task_window_days: int = 30
    stale_thread_days: int = 7
    user_email: str = ""  # SA user email for internal/external classification

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def cookie_secure(settings: Settings | None = None) -> bool:
    """Whether session cookies require HTTPS (matches production Caddy TLS)."""
    s = settings or get_settings()
    if s.auth_cookie_secure:
        return True
    return s.frontend_url.strip().lower().startswith("https://")
