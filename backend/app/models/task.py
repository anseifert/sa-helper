from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_task_source"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    origin_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    badge_source: Mapped[str] = mapped_column(String(32), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_manual: Mapped[bool] = mapped_column(default=False, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company | None"] = relationship(back_populates="tasks")
    contacts: Mapped[list["TaskContact"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskContact(Base):
    __tablename__ = "task_contacts"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), primary_key=True)
    role: Mapped[str | None] = mapped_column(String(32), nullable=True)

    task: Mapped["Task"] = relationship(back_populates="contacts")
    contact: Mapped["Contact"] = relationship(back_populates="task_links")
