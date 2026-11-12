from sqlalchemy.orm import Session

from app.models.member import Member
from app.repositories.member_repository import MemberRepository
from app.schemas.member import MemberCreate


class MemberService:

    def __init__(
        self,
        db: Session,
        repository: MemberRepository,
    ):
        self.db = db
        self.repository = repository
#=========================================================
# CREATE THE MEMBER
#=========================================================
    def create_member(
        self,
        payload: MemberCreate,
        organization_id: int,
    ) -> Member:

        try:
            member = Member(
                organization_id=organization_id,
                name=payload.name.strip(),
                external_member_id=payload.external_member_id,
                date_of_birth=payload.date_of_birth,
            )

            created = self.repository.create(member)

            self.db.commit()
            self.db.refresh(created)

            return created

        except Exception:
            self.db.rollback()
            raise

#=========================================================
# GET THE MEMBER BY MEMBER ID
#=========================================================
    def get_member(
        self,
        member_id: int,
        organization_id: int,
    ) -> Member | None:

        return self.repository.get_by_id_for_organization(
            member_id=member_id,
            organization_id=organization_id,
        )
#=========================================================
# GET THE LIST OF TEH MEMBERS BY ORGANIZATION_ID
#=========================================================
    def list_members(
        self,
        organization_id: int,
    ) -> list[Member]:

        return self.repository.list_by_organization(
            organization_id=organization_id,
        )
