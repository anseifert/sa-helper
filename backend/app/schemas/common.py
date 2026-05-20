from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    ollama: str
    google_connected: bool


class MessageResponse(BaseModel):
    message: str
