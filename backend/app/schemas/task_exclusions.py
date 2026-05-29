from pydantic import BaseModel, Field


class TaskExclusionsOut(BaseModel):
    emails: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)


class TaskExclusionsUpdate(BaseModel):
    emails: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
