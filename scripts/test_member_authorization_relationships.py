
from datetime import date

from app.db.session import sessionlocal

from app.models.organization import Organization
from app.models.user import User
from app.models.member import Member
from app.models.member_coverage import MemberCoverage
from app.models.authorization import Authorization


def test_member_authorization_relationships():

    db = sessionlocal()

    try:
        # 1. Create an organization
        organization = Organization(
            name="HealthGuard Test Organization"
        )

        db.add(organization)
        db.flush()

        print("Organization created:", organization.id)

        # 2. Create a user belonging to the organization
        user = User(
            email="testuser@healthguard.local",
            username="testuser",
            password_hash="dummy_test_hash",
            role="ADMIN",
            organization_id=organization.id
        )

        db.add(user)
        db.flush()

        print("User created:", user.id)

        # 3. Create a member belonging to the organization
        member = Member(
            organization_id=organization.id,
            external_member_id="MEM001",
            name="John Smith",
            date_of_birth=date(1990, 5, 15)
        )

        db.add(member)
        db.flush()

        print("Member created:", member.id)

        # 4. Create member coverage
        coverage = MemberCoverage(
            member_id=member.id,
            plan_id="PLAN-A",
            member_number="MEM001",
            coverage_status="ACTIVE",
            effective_date=date(2026, 1, 1)
        )

        db.add(coverage)
        db.flush()

        print("Coverage created:", coverage.id)

        # 5. Create authorization
        authorization = Authorization(
            member_id=member.external_member_id,
            member_record_id=member.id,
            member_coverage_id=coverage.id,
            procedure_code="MRI001",
            diagnosis_code="M54.5",
            clinical_summary="Patient requires an MRI scan.",
            service_date=date(2026, 11, 5),
            user_id=user.id,
            status="DRAFT"
        )

        db.add(authorization)
        db.flush()

        print("Authorization created:", authorization.id)

        # 6. Verify relationships
        db.refresh(authorization)

        # Verify member relationship
        assert authorization.member.id == member.id
        assert authorization.member.external_member_id == "MEM001"

        # Verify coverage relationship
        assert authorization.member_coverage.id == coverage.id
        assert authorization.member_coverage.member_id == member.id

        # Verify user relationship
        assert authorization.user.id == user.id
        assert authorization.user.email == user.email

        print("Member relationship:", authorization.member.name)
        print("Coverage relationship:", authorization.member_coverage.plan_id)
        print("User relationship:", authorization.user.username)

        print("All database relationship tests passed!")

        # Roll back test data
        db.rollback()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    test_member_authorization_relationships()
