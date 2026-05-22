from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    ollama: str
    google_connected: bool
    app_version: str = "unknown"
    auth_enabled: bool = False


class MessageResponse(BaseModel):
    message: str
