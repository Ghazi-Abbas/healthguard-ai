
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    String,
    DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.authorization import Authorization
    from app.models.member import Member


class MemberCoverage(Base):
    __tablename__ = "member_coverages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    member_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    coverage_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    termination_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # MemberCoverage -> Authorization
    authorizations: Mapped[list[Authorization]] = relationship(
        "Authorization",
        back_populates="member_coverage",
    )

    # MemberCoverage -> Member
    member: Mapped[Member] = relationship(
        "Member",
        back_populates="coverages",
    )
