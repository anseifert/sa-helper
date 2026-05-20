from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_internal: Mapped[bool] = mapped_column(default=False, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="gmail", nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(512), nullable=True)

    company: Mapped["Company | None"] = relationship(back_populates="contacts")
    task_links: Mapped[list["TaskContact"]] = relationship(back_populates="contact")
