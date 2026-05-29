from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CompanyAssets(Base, TimestampMixin):
    __tablename__ = "company_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), unique=True, nullable=False, index=True
    )

    sub_ocp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_oke: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_ovm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_rhel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_aap: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_acs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sub_acm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    ansible_nodes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rhel_subscriptions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    hw_hp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hw_dell: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hw_cisco: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hw_palo_alto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hw_fortinet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="assets")
