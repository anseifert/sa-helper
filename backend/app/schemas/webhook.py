from pydantic import BaseModel, HttpUrl


class WebhookRegister(BaseModel):
    url: HttpUrl
    events: list[str] = ["sync.completed", "recommendations.updated"]
