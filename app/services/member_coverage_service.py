from sqlalchemy.orm import Session

from app.models.member_coverage import MemberCoverage
from app.repositories.member_coverage_repository import (
    MemberCoverageRepository,
)
from app.schemas.member_coverage import MemberCoverageCreate


class MemberCoverageService:

    def __init__(
        self,
        db: Session,
        repository: MemberCoverageRepository,
    ):
        self.db = db
        self.repository = repository
#=========================================================
# CREATE THE COVERAGE
#=========================================================
    def create_coverage(
        self,
        payload: MemberCoverageCreate,
        organization_id: int,
    ) -> MemberCoverage:

        try:
            # Step 1: Validate member ownership.
            member = self.repository.get_member_for_organization(
                member_id=payload.member_id,
                organization_id=organization_id,
            )

            if member is None:
                raise LookupError(
                    "Member not found or access denied."
                )

            # Step 2: Look for existing coverage records.
            existing_coverages = (
                self.repository
                .get_by_member_and_plan_for_organization(
                    member_id=payload.member_id,
                    plan_id=payload.plan_id,
                    organization_id=organization_id,
                )
            )

            # Step 3: Avoid creating an exact duplicate.
            for existing in existing_coverages:
                same_period = (
                    existing.effective_date == payload.effective_date
                    and existing.termination_date
                    == payload.termination_date
                )

                same_member_number = (
                    existing.member_number.strip()
                    == payload.member_number.strip()
                )

                if same_period and same_member_number:
                    return existing

            # Step 4: Create a pending coverage record.
            coverage = MemberCoverage(
                member_id=payload.member_id,
                plan_id=payload.plan_id,
                member_number=payload.member_number.strip(),
                effective_date=payload.effective_date,
                termination_date=payload.termination_date,

            )

            created = self.repository.create(coverage)

            # Step 5: Commit the transaction.
            self.db.commit()
            self.db.refresh(created)

            return created

        except Exception:
            self.db.rollback()
            raise
#=========================================================
# GET THE MEMBER COVERAGE FROM MEMBER COVERAGE ID
#=========================================================
    def get_coverage(
        self,
        coverage_id: int,
        organization_id: int,
    ) -> MemberCoverage | None:

        return self.repository.get_by_id_for_organization(
            coverage_id=coverage_id,
            organization_id=organization_id,
        )
#=========================================================
# GET THE MEMBER COVERAGES FROM MEMBER ID
#=========================================================
    def get_member_coverages(
        self,
        member_id: int,
        organization_id: int,
    ) -> list[MemberCoverage]:

        member = self.repository.get_member_for_organization(
            member_id=member_id,
            organization_id=organization_id,
        )

        if member is None:
            raise LookupError(
                "Member not found or access denied."
            )

        return (
            self.repository
            .list_by_member_for_organization(
                member_id=member_id,
                organization_id=organization_id,
            )
        )
