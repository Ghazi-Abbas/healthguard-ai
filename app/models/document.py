from sqlalchemy import ForeignKey , String ,DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime

class Document(Base):
    __tablename__="documents"

    id:Mapped[int]=mapped_column(
        primary_key=True,
        autoincrement=True
    )

    authorization_id:Mapped[int]=mapped_column(
        ForeignKey("authorizations.id"),
        nullable=False
    )

    filename:Mapped[str]= mapped_column(
        String(255),
        nullable=False
    )
    content_type:Mapped[str]=mapped_column(
        String(100),
        nullable=False
    )

    storage_path:Mapped[str]=mapped_column(
        String(500),
        nullable=False
    )

    processing_status:Mapped[str]=mapped_column(
        String(50),
        nullable=False,
        default="UPLOADED"
    )

    page_count:Mapped[int]=mapped_column(
        nullable=False,
        default=0
        )

    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    authorization=relationship(
        "Authorization",
        back_populates="documents"
    )

    pages = relationship(
        "DocumentPage",
        back_populates="document",
        cascade="all, delete-orphan"
    )
class DocumentPage(Base):

    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
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
        "Document",
        back_populates="pages"
    )
