"""Slack extractor stub — interface only, no sync in MVP."""

from app.extractors.base import BaseExtractor, ExtractedContact, ExtractedTask


class SlackExtractor(BaseExtractor):
    name = "slack"

    async def extract_contacts(self) -> list[ExtractedContact]:
        return []

    async def extract_tasks(self) -> list[ExtractedTask]:
        return []
