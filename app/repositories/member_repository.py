from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.member import Member


class MemberRepository:

    def __init__(self, db: Session):
        self.db = db
#=========================================================
# CREATE THE MEMBER
#=========================================================
    def create(self, member: Member) -> Member:
        self.db.add(member)
        self.db.flush()
        return member
#=========================================================
# GET BY MEMBER ID FOR THE ORGANIZATION
#=========================================================
    def get_by_id_for_organization(
        self,
        member_id: int,
        organization_id: int,
    ) -> Member | None:

        stmt = select(Member).where(
            Member.id == member_id,
            Member.organization_id == organization_id,
        )

        return self.db.scalars(stmt).first()

#=========================================================
# BY ORGANIZATION ID GETTING ALL THE MEMBERS
#=========================================================
    def list_by_organization(
        self,
        organization_id: int,
    ) -> list[Member]:

        stmt = (
            select(Member)
            .where(Member.organization_id == organization_id)
            .order_by(Member.created_at.desc())
        )

        return list(self.db.scalars(stmt).all())
