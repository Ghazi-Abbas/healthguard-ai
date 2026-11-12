from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Organization(Base):
    __tablename__="organizations"

    id:Mapped[int]=mapped_column(
        primary_key=True
    )

    name:Mapped[str]=mapped_column(
        String(100),
        nullable=False
    )
    # An Organization object has access to its related User objects through the users attribute.
    users=relationship(
        "User",
        back_populates="organization"
    )

    # user:Mapped[list["User"]]=relationship(
    #     back_populates="organization"
    # )

    # authorizations:Mapped[list["Autherization"]]=relationship(
    #     back_populates="organization"
    # )
    members = relationship(
    "Member",
    back_populates="organization",
)
