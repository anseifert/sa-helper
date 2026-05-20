from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedContact:
    email: str
    display_name: str | None = None
    source_id: str | None = None


@dataclass
class ExtractedTask:
    source: str
    source_id: str
    title: str
    task_type: str
    badge_source: str
    description: str | None = None
    origin_url: str | None = None
    due_at: datetime | None = None
    contact_emails: list[str] = field(default_factory=list)
    company_domain: str | None = None


class BaseExtractor(ABC):
    name: str

    @abstractmethod
    async def extract_contacts(self) -> list[ExtractedContact]:
        ...

    @abstractmethod
    async def extract_tasks(self) -> list[ExtractedTask]:
        ...
