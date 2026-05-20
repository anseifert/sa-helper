from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rec_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    company_id: Mapped[int | None] = mapped_column(nullable=True)
    task_id: Mapped[int | None] = mapped_column(nullable=True)
    contact_id: Mapped[int | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
