
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.member import Member
from app.models.member_coverage import MemberCoverage


class MemberCoverageRepository:

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE MEMBER COVERAGE
    # =========================================================

    def create(
        self,
        coverage: MemberCoverage,
    ) -> MemberCoverage:

        self.db.add(coverage)
        self.db.flush()

        return coverage

    # =========================================================
    # GET MEMBER FOR ORGANIZATION
    # Uses internal member ID
    # =========================================================

    def get_member_for_organization(
        self,
        member_id: int,
        organization_id: int,
    ) -> Member | None:

        stmt = select(Member).where(
            Member.id == member_id,
            Member.organization_id == organization_id,
        )

        return self.db.scalars(stmt).first()

    # =========================================================
    # GET COVERAGE BY ID FOR ORGANIZATION
    # =========================================================

    def get_by_id_for_organization(
        self,
        coverage_id: int,
        organization_id: int,
    ) -> MemberCoverage | None:

        stmt = (
            select(MemberCoverage)
            .join(
                Member,
                MemberCoverage.member_id == Member.id,
            )
            .where(
                MemberCoverage.id == coverage_id,
                Member.organization_id == organization_id,
            )
        )

        return self.db.scalars(stmt).first()

    # =========================================================
    # GET ALL COVERAGES FOR A MEMBER
    # Uses internal member ID
    # =========================================================

    def list_by_member_for_organization(
        self,
        member_id: int,
        organization_id: int,
    ) -> list[MemberCoverage]:

        stmt = (
            select(MemberCoverage)
            .join(
                Member,
                MemberCoverage.member_id == Member.id,
            )
            .where(
                MemberCoverage.member_id == member_id,
                Member.organization_id == organization_id,
            )
            .order_by(
                MemberCoverage.effective_date.desc()
            )
        )

        return list(self.db.scalars(stmt).all())

    # =========================================================
    # GET COVERAGE BY MEMBER ID AND PLAN ID
    # =========================================================

    def get_by_member_and_plan_for_organization(
        self,
        member_id: int,
        plan_id: str,
        organization_id: int,
    ) -> list[MemberCoverage]:

        stmt = (
            select(MemberCoverage)
            .join(
                Member,
                MemberCoverage.member_id == Member.id,
            )
            .where(
                MemberCoverage.member_id == member_id,
                MemberCoverage.plan_id == plan_id,
                Member.organization_id == organization_id,
            )
            .order_by(
                MemberCoverage.effective_date.desc()
            )
        )

        return list(self.db.scalars(stmt).all())

    # =========================================================
    # GET ACTIVE COVERAGE FOR SERVICE DATE
    # Uses external member ID
    # =========================================================

    def get_active_coverage_for_service_date(
        self,
        member_id: str,
        plan_id: str,
        service_date: date,
        organization_id: int,
    ) -> MemberCoverage | None:

        stmt = (
            select(MemberCoverage)
            .join(
                Member,
                MemberCoverage.member_id == Member.id,
            )
            .where(
                Member.external_member_id == member_id,
                MemberCoverage.plan_id == plan_id,
                MemberCoverage.coverage_status == "ACTIVE",
                MemberCoverage.effective_date <= service_date,
                (
                    MemberCoverage.termination_date.is_(None)
                    | (
                        MemberCoverage.termination_date
                        >= service_date
                    )
                ),
                Member.organization_id == organization_id,
            )
            .order_by(
                MemberCoverage.effective_date.desc()
            )
        )

        return self.db.scalars(stmt).first()

    # =========================================================
    # GET COVERAGE FOR ELIGIBILITY AGENT
    # Uses internal member ID
    # =========================================================

    def get_coverage_for_eligibility(
        self,
        *,
        organization_id: int,
        member_id: int,
    ) -> list[dict]:

        statement = (
            select(MemberCoverage)
            .join(
                Member,
                MemberCoverage.member_id == Member.id,
            )
            .where(
                Member.organization_id == organization_id,
                MemberCoverage.member_id == member_id,
            )
            .order_by(
                MemberCoverage.effective_date.desc()
            )
        )

        records = self.db.scalars(statement).all()

        return [
            {
                "member_id": record.member_id,
                "plan_id": record.plan_id,
                "coverage_status": record.coverage_status,
                "effective_date": record.effective_date.isoformat(),
                "termination_date": (
                    record.termination_date.isoformat()
                    if record.termination_date
                    else None
                ),
            }
            for record in records
        ]
