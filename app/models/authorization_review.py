from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuthorizationReview(Base):

    __tablename__ = "authorization_reviews"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    authorization_id: Mapped[int] = mapped_column(
        ForeignKey("authorizations.id"),
        nullable=False,
        index=True
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    authorization = relationship("Authorization")
    reviewer = relationship(
    "User",
    back_populates="reviews"
)
    organization = relationship("Organization")
