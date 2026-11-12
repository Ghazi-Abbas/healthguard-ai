
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Date,
    DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.member_coverage import MemberCoverage
    from app.models.member import Member


class Authorization(Base):
    __tablename__ = "authorizations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # External member identifier: MEM001, MEM002
    member_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Internal database relationship: members.id
    member_record_id: Mapped[int] = mapped_column(
        ForeignKey("members.id"),
        nullable=False,
        index=True
    )

    procedure_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    diagnosis_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    clinical_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DRAFT"
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    service_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # User relationship
    user = relationship(
        "User",
        back_populates="authorizations"
    )

    # Authorization -> Documents
    documents = relationship(
        "Document",
        back_populates="authorization"
    )

    # Selected coverage record
    member_coverage_id: Mapped[int | None] = mapped_column(
        ForeignKey("member_coverages.id"),
        nullable=True
    )

    member_coverage: Mapped[MemberCoverage | None] = relationship(
        "MemberCoverage",
        back_populates="authorizations"
    )

    # Authorization -> Member
    # Uses member_record_id, NOT the external member_id
    member: Mapped[Member] = relationship(
        "Member",
        back_populates="authorizations",
        foreign_keys=[member_record_id]
    )



# ForeignKey       → connects database tables
# relationship()   → gives Python objects a way to navigate
# back_populates   → connects the two navigation directions
