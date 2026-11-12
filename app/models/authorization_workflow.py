from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuthorizationWorkflow(Base):

    __tablename__ = "authorization_workflows"

    __table_args__ = (
        UniqueConstraint(
            "authorization_id",
            name="uq_workflow_authorization"
        ),
        UniqueConstraint(
            "thread_id",
            name="uq_workflow_thread"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    authorization_id: Mapped[int] = mapped_column(
        ForeignKey("authorizations.id"),
        nullable=False
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False
    )

    thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    workflow_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RUNNING"
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

    authorization = relationship("Authorization")
    organization = relationship("Organization")
