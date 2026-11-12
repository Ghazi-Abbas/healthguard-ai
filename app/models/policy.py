from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text
)

from datetime import datetime
class Policy(Base):
    __tablename__="policies"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True
        )

    organization_id:Mapped[int]=mapped_column(
        ForeignKey("organizations.id"),
        nullable=False
    )

    name:Mapped[str]=mapped_column(
        String(255),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
    )


    version:Mapped[str]=mapped_column(
        String(100),
        nullable=False
    )

    description:Mapped[str | None]=mapped_column(
        Text,
        nullable=True
    )

    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    documents: Mapped[list["PolicyDocument"]] = relationship(
        "PolicyDocument",
        back_populates="policy",
        cascade="all, delete-orphan",
    )

class PolicyDocument(Base):

    __tablename__ = "policy_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    processing_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UPLOADED"
    )

    indexing_status: Mapped[str] = mapped_column(
    String(30),
    default="PENDING",
    nullable=False,
    )

    page_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    policy: Mapped["Policy"] = relationship(
        "Policy",
        back_populates="documents",
    )



    pages = relationship(
        "PolicyDocumentPage",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class PolicyDocumentPage(Base):

    __tablename__ = "policy_document_pages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("policy_documents.id"),
        nullable=False
    )

    page_number: Mapped[int] = mapped_column(
        nullable=False
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    document = relationship(
        "PolicyDocument",
        back_populates="pages"
    )
