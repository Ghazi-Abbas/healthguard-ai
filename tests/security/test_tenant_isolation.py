import asyncio
from io import BytesIO
from fastapi import UploadFile
from datetime import date
from types import SimpleNamespace
from app.services.document_service import DocumentService
import pytest
from app.models.document import Document, DocumentPage

from app.repositories.document_repository import DocumentRepository

from fastapi import HTTPException
from sqlalchemy import select, inspect

from app.models.organization import Organization
from app.models.user import User
from app.models.member import Member
from app.models.member_coverage import MemberCoverage
from app.models.authorization import Authorization
from app.models.authorization_workflow import AuthorizationWorkflow

from app.repositories.autharization_repository import (
    AuthorizationRepository,
)

from app.repositories.member_coverage_repository import (
    MemberCoverageRepository,
)

from app.repositories.user_repository import UserRepository

from app.services.authorization_service import AuthorizationService

from app.schemas.authorization import AuthorisationPatch


# =========================================================
# TEST 1: VERIFY ISOLATED DATABASE
# =========================================================

def test_isolated_database_creates_all_tables(db_session):

    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()

    expected_tables = {
        "organizations",
        "users",
        "members",
        "member_coverages",
        "authorizations",
        "authorization_workflows",
        "authorization_reviews",
        "documents",
        "document_pages",
        "policies",
        "policy_documents",
        "policy_document_pages",
    }

    missing_tables = expected_tables - set(tables)

    assert not missing_tables, (
        f"Missing database tables: {missing_tables}"
    )


# =========================================================
# TEST 2: ORGANIZATION CANNOT ACCESS ANOTHER ORGANIZATION'S
# AUTHORIZATION
# =========================================================

def test_organization_cannot_access_another_organizations_authorization(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    user_a = User(
        email="usera@example.com",
        username="user_a",
        password_hash="test_hash_a",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True,
    )

    user_b = User(
        email="userb@example.com",
        username="user_b",
        password_hash="test_hash_b",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    db_session.add_all([user_a, user_b])
    db_session.flush()

    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-A-001",
        name="Member A",
        date_of_birth=date(1990, 1, 1),
    )

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10),
    )

    db_session.add_all([member_a, member_b])
    db_session.flush()

    authorization_b = Authorization(
        member_id=member_b.external_member_id,
        member_record_id=member_b.id,
        procedure_code="PROC-001",
        diagnosis_code="DIAG-001",
        clinical_summary="Clinical summary for testing tenant isolation.",
        status="DRAFT",
        user_id=user_b.id,
        service_date=date(2026, 11, 6),
    )

    db_session.add(authorization_b)
    db_session.commit()
    db_session.refresh(authorization_b)

    repository = AuthorizationRepository(db_session)

    # Organization B can access its own authorization.
    result_b = repository.get_by_id_for_organization(
        authorization_id=authorization_b.id,
        organization_id=organization_b.id,
    )

    assert result_b is not None

    # Organization A cannot access Organization B's authorization.
    result_a = repository.get_by_id_for_organization(
        authorization_id=authorization_b.id,
        organization_id=organization_a.id,
    )

    assert result_a is None


# =========================================================
# TEST 3: ORGANIZATION CANNOT UPDATE ANOTHER ORGANIZATION'S
# AUTHORIZATION
# =========================================================

def test_organization_cannot_update_another_organizations_authorization(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    user_a = User(
        email="usera@example.com",
        username="user_a",
        password_hash="test_hash_a",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True,
    )

    user_b = User(
        email="userb@example.com",
        username="user_b",
        password_hash="test_hash_b",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    db_session.add_all([user_a, user_b])
    db_session.flush()

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10),
    )

    db_session.add(member_b)
    db_session.flush()

    original_summary = "Original clinical summary for testing."

    authorization_b = Authorization(
        member_id=member_b.external_member_id,
        member_record_id=member_b.id,
        procedure_code="PROC-001",
        diagnosis_code="DIAG-001",
        clinical_summary=original_summary,
        status="DRAFT",
        user_id=user_b.id,
        service_date=date(2026, 11, 6),
    )

    db_session.add(authorization_b)
    db_session.commit()
    db_session.refresh(authorization_b)

    repository = AuthorizationRepository(db_session)

    service = AuthorizationService(
        repository=repository,
        db=db_session,
        coverage_repository=None,
        workflow_repository=None,
        policy_repository=None,
        document_repository=None,
        graph=None,
    )

    request = AuthorisationPatch(
        clinical_summary="Unauthorized attempt to change this record."
    )

    with pytest.raises(HTTPException) as error:
        service.update_authorization(
            authorization_id=authorization_b.id,
            request=request,
            user_id=user_a.id,
            organization_id=organization_a.id,
        )

    assert error.value.status_code == 404

    db_session.expire_all()

    saved_authorization = repository.get_by_id_for_organization(
        authorization_id=authorization_b.id,
        organization_id=organization_b.id,
    )

    assert saved_authorization is not None
    assert saved_authorization.clinical_summary == original_summary


# =========================================================
# TEST 4: REVIEW QUEUE MUST BE ORGANIZATION-SCOPED
# =========================================================

def test_review_queue_only_returns_own_organization_authorizations(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    user_a = User(
        email="usera@example.com",
        username="user_a",
        password_hash="test_hash_a",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True,
    )

    user_b = User(
        email="userb@example.com",
        username="user_b",
        password_hash="test_hash_b",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    db_session.add_all([user_a, user_b])
    db_session.flush()

    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-A-001",
        name="Member A",
        date_of_birth=date(1990, 1, 1),
    )

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10),
    )

    db_session.add_all([member_a, member_b])
    db_session.flush()

    authorization_a = Authorization(
        member_id=member_a.external_member_id,
        member_record_id=member_a.id,
        procedure_code="PROC-A",
        diagnosis_code="DIAG-A",
        clinical_summary="Clinical summary for Organization A.",
        status="SUBMITTED",
        user_id=user_a.id,
        service_date=date(2026, 11, 6),
    )

    authorization_b = Authorization(
        member_id=member_b.external_member_id,
        member_record_id=member_b.id,
        procedure_code="PROC-B",
        diagnosis_code="DIAG-B",
        clinical_summary="Clinical summary for Organization B.",
        status="SUBMITTED",
        user_id=user_b.id,
        service_date=date(2026, 11, 6),
    )

    db_session.add_all([authorization_a, authorization_b])
    db_session.flush()

    workflow_a = AuthorizationWorkflow(
        authorization_id=authorization_a.id,
        organization_id=organization_a.id,
        thread_id="thread-org-a",
        workflow_status="WAITING_FOR_REVIEW",
    )

    workflow_b = AuthorizationWorkflow(
        authorization_id=authorization_b.id,
        organization_id=organization_b.id,
        thread_id="thread-org-b",
        workflow_status="WAITING_FOR_REVIEW",
    )

    db_session.add_all([workflow_a, workflow_b])
    db_session.commit()

    repository = AuthorizationRepository(db_session)

    queue_a = repository.get_review_queue(organization_a.id)
    queue_b = repository.get_review_queue(organization_b.id)

    assert len(queue_a) == 1
    assert queue_a[0].id == authorization_a.id

    assert len(queue_b) == 1
    assert queue_b[0].id == authorization_b.id

    assert authorization_b.id not in [item.id for item in queue_a]
    assert authorization_a.id not in [item.id for item in queue_b]


# =========================================================
# TEST 5: ORGANIZATION CANNOT ACCESS ANOTHER ORGANIZATION'S
# MEMBER COVERAGE
# =========================================================

def test_organization_cannot_access_another_organizations_coverage(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-A-001",
        name="Member A",
        date_of_birth=date(1990, 1, 1),
    )

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10),
    )

    db_session.add_all([member_a, member_b])
    db_session.flush()

    coverage_a = MemberCoverage(
        member_id=member_a.id,
        plan_id="PLAN-A",
        member_number="NUMBER-A",
        coverage_status="ACTIVE",
        effective_date=date(2026, 1, 1),
    )

    coverage_b = MemberCoverage(
        member_id=member_b.id,
        plan_id="PLAN-B",
        member_number="NUMBER-B",
        coverage_status="ACTIVE",
        effective_date=date(2026, 1, 1),
    )

    db_session.add_all([coverage_a, coverage_b])
    db_session.commit()

    repository = MemberCoverageRepository(db_session)

    own_coverage = repository.get_by_id_for_organization(
        coverage_id=coverage_b.id,
        organization_id=organization_b.id,
    )

    assert own_coverage is not None

    foreign_coverage = repository.get_by_id_for_organization(
        coverage_id=coverage_b.id,
        organization_id=organization_a.id,
    )

    assert foreign_coverage is None

    foreign_member_coverages = (
        repository.list_by_member_for_organization(
            member_id=member_b.id,
            organization_id=organization_a.id,
        )
    )

    assert foreign_member_coverages == []

    foreign_active_coverage = (
        repository.get_active_coverage_for_service_date(
            member_id=member_b.external_member_id,
            plan_id="PLAN-B",
            service_date=date(2026, 11, 6),
            organization_id=organization_a.id,
        )
    )

    assert foreign_active_coverage is None


# =========================================================
# TEST 6: USER CANNOT CREATE AUTHORIZATION USING ANOTHER
# ORGANIZATION'S COVERAGE
# =========================================================

def test_user_cannot_create_authorization_using_another_organizations_coverage(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    user_a = User(
        email="provider-a@example.com",
        username="provider_a",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True,
    )

    db_session.add(user_a)
    db_session.flush()

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10),
    )

    db_session.add(member_b)
    db_session.flush()

    coverage_b = MemberCoverage(
        member_id=member_b.id,
        plan_id="PLAN-B",
        member_number="NUMBER-B",
        coverage_status="ACTIVE",
        effective_date=date(2026, 1, 1),
    )

    db_session.add(coverage_b)
    db_session.commit()

    authorization_repository = AuthorizationRepository(db_session)
    coverage_repository = MemberCoverageRepository(db_session)

    service = AuthorizationService(
        repository=authorization_repository,
        db=db_session,
        coverage_repository=coverage_repository,
        workflow_repository=None,
        policy_repository=None,
        document_repository=None,
        graph=None,
        user_repository=UserRepository(db_session),
    )

    request = SimpleNamespace(
        member_id="MEM-B-001",
        plan_id="PLAN-B",
        service_date=date(2026, 11, 6),
        procedure_code="PROC-001",
        diagnosis_code="DIAG-001",
        clinical_summary="Clinical summary for tenant isolation testing.",
    )

    with pytest.raises(HTTPException) as error:
        service.create(
            request=request,
            user_id=user_a.id,
            organization_id=organization_a.id,
        )

    assert error.value.status_code == 422

    authorizations = db_session.scalars(
        select(Authorization)
    ).all()

    assert authorizations == []


# =========================================================
# TEST 7: USER CANNOT BE RETRIEVED FROM ANOTHER ORGANIZATION
# =========================================================

def test_user_cannot_be_retrieved_from_another_organization(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    user_b = User(
        email="userb@example.com",
        username="user_b",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    db_session.add(user_b)
    db_session.commit()

    repository = UserRepository(db_session)

    # Organization B can retrieve its own user.
    own_user = repository.get_by_id_for_organization(
        user_id=user_b.id,
        organization_id=organization_b.id,
    )

    assert own_user is not None

    # Organization A cannot retrieve Organization B's user.
    foreign_user = repository.get_by_id_for_organization(
        user_id=user_b.id,
        organization_id=organization_a.id,
    )

    assert foreign_user is None

# =========================================================
# TEST 8: USER CANNOT CREATE AUTHORIZATION IN ANOTHER
# ORGANIZATION EVEN WHEN ITS COVERAGE IS VALID
# =========================================================

def test_user_cannot_create_authorization_in_another_organization(
    db_session,
):
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    # User belongs to Organization B.
    user_b = User(
        email="provider-b@example.com",
        username="provider_b",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    # Member belongs to Organization A.
    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-A-001",
        name="Member A",
        date_of_birth=date(1990, 1, 1),
    )

    db_session.add_all([user_b, member_a])
    db_session.flush()

    # Valid coverage belonging to Organization A.
    coverage_a = MemberCoverage(
        member_id=member_a.id,
        plan_id="PLAN-A",
        member_number="NUMBER-A",
        coverage_status="ACTIVE",
        effective_date=date(2026, 1, 1),
    )

    db_session.add(coverage_a)
    db_session.commit()

    authorization_repository = AuthorizationRepository(db_session)
    coverage_repository = MemberCoverageRepository(db_session)

    service = AuthorizationService(
        repository=authorization_repository,
        db=db_session,
        coverage_repository=coverage_repository,
        workflow_repository=None,
        policy_repository=None,
        document_repository=None,
        graph=None,
        user_repository=UserRepository(db_session),
    )

    request = SimpleNamespace(
        member_id="MEM-A-001",
        plan_id="PLAN-A",
        service_date=date(2026, 11, 6),
        procedure_code="PROC-001",
        diagnosis_code="DIAG-001",
        clinical_summary="Tenant isolation security test.",
    )

    # User B attempts to create an authorization in Organization A.
    with pytest.raises(HTTPException) as error:
        service.create(
            request=request,
            user_id=user_b.id,
            organization_id=organization_a.id,
        )

    assert error.value.status_code == 404

    authorizations = db_session.scalars(
        select(Authorization)
    ).all()

    assert authorizations == []

# =========================================================
# TEST 9: ORGANIZATION CANNOT ACCESS ANOTHER ORGANIZATION'S
# DOCUMENTS
# =========================================================

def test_document_repository_enforces_organization_isolation(
    db_session,
):
    # 1. Create two organizations
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    # 2. Create users
    user_a = User(
        email="provider-a@example.com",
        username="provider_a",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True
    )

    user_b = User(
        email="provider-b@example.com",
        username="provider_b",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True
    )

    db_session.add_all([user_a, user_b])
    db_session.flush()

    # 3. Create members
    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-A-001",
        name="Member A",
        date_of_birth=date(1990, 1, 1)
    )

    member_b = Member(
        organization_id=organization_b.id,
        external_member_id="MEM-B-001",
        name="Member B",
        date_of_birth=date(1992, 5, 10)
    )

    db_session.add_all([member_a, member_b])
    db_session.flush()

    # 4. Create authorizations
    authorization_a = Authorization(
        member_id=member_a.external_member_id,
        member_record_id=member_a.id,
        procedure_code="PROC-A",
        diagnosis_code="DIAG-A",
        clinical_summary="Organization A clinical summary",
        status="DRAFT",
        user_id=user_a.id,
        service_date=date(2026, 11, 6)
    )

    authorization_b = Authorization(
        member_id=member_b.external_member_id,
        member_record_id=member_b.id,
        procedure_code="PROC-B",
        diagnosis_code="DIAG-B",
        clinical_summary="Organization B clinical summary",
        status="DRAFT",
        user_id=user_b.id,
        service_date=date(2026, 11, 6)
    )

    db_session.add_all([authorization_a, authorization_b])
    db_session.flush()

    # 5. Create documents
    document_a = Document(
        authorization_id=authorization_a.id,
        filename="document_a.pdf",
        content_type="application/pdf",
        storage_path="organizations/a/document_a.pdf",
        processing_status="PROCESSED",
        page_count=1
    )

    document_b = Document(
        authorization_id=authorization_b.id,
        filename="document_b.pdf",
        content_type="application/pdf",
        storage_path="organizations/b/document_b.pdf",
        processing_status="PROCESSED",
        page_count=1
    )

    db_session.add_all([document_a, document_b])
    db_session.flush()

    # 6. Create clinical pages
    page_a = DocumentPage(
        document_id=document_a.id,
        page_number=1,
        text="Clinical information belonging to Organization A."
    )

    page_b = DocumentPage(
        document_id=document_b.id,
        page_number=1,
        text="Clinical information belonging to Organization B."
    )

    db_session.add_all([page_a, page_b])
    db_session.commit()

    repository = DocumentRepository(db_session)

    # 7. Organization A retrieves its own documents
    documents_a = repository.get_by_authorization(
        authorization_id=authorization_a.id,
        organization_id=organization_a.id
    )

    assert len(documents_a) == 1
    assert documents_a[0].id == document_a.id

    # 8. Organization B cannot retrieve Organization A's documents
    foreign_documents = repository.get_by_authorization(
        authorization_id=authorization_a.id,
        organization_id=organization_b.id
    )

    assert foreign_documents == []

    # 9. Organization A retrieves its processed documents and pages
    processed_documents_a = (
        repository.get_processed_documents_with_pages(
            authorization_id=authorization_a.id,
            organization_id=organization_a.id
        )
    )

    assert len(processed_documents_a) == 1
    assert processed_documents_a[0].id == document_a.id

    assert len(processed_documents_a[0].pages) == 1

    assert (
        processed_documents_a[0].pages[0].text
        == "Clinical information belonging to Organization A."
    )

    # 10. Organization B cannot retrieve Organization A's clinical pages
    foreign_processed_documents = (
        repository.get_processed_documents_with_pages(
            authorization_id=authorization_a.id,
            organization_id=organization_b.id
        )
    )

    assert foreign_processed_documents == []

    print("Document tenant isolation test passed.")

    # 11. Verify DocumentService prevents cross-organization access

    authorization_repository = AuthorizationRepository(db_session)

    document_service = DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=repository,
        storage_service=None,
        workflow_repository=None,
        graph=None,
        db=db_session
    )

    # User B attempts to retrieve Organization A's documents.
    with pytest.raises(HTTPException) as error:
        document_service.get_document(
            authorization_id=authorization_a.id,
            user_id=user_b.id,
            organization_id=organization_b.id
        )

    assert error.value.status_code == 404

    print("DocumentService tenant isolation test passed.")



def test_user_cannot_upload_document_to_another_organization(
    db_session,
):
    # 1. Create organizations
    organization_a = Organization(name="Organization A")
    organization_b = Organization(name="Organization B")

    db_session.add_all([organization_a, organization_b])
    db_session.flush()

    # 2. Create users
    user_a = User(
        email="upload-a@example.com",
        username="upload_a",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_a.id,
        is_active=True,
    )

    user_b = User(
        email="upload-b@example.com",
        username="upload_b",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization_b.id,
        is_active=True,
    )

    db_session.add_all([user_a, user_b])
    db_session.flush()

    # 3. Create a member in Organization A
    member_a = Member(
        organization_id=organization_a.id,
        external_member_id="MEM-UPLOAD-A",
        name="Member A",
        date_of_birth=date(1990, 1, 1),
    )

    db_session.add(member_a)
    db_session.flush()

    # 4. Create authorization owned by User A
    authorization_a = Authorization(
        member_id=member_a.external_member_id,
        member_record_id=member_a.id,
        procedure_code="PROC-A",
        diagnosis_code="DIAG-A",
        clinical_summary="Test authorization",
        status="DRAFT",
        user_id=user_a.id,
        service_date=date(2026, 11, 6),
    )

    db_session.add(authorization_a)
    db_session.commit()

    # 5. Create real repositories
    authorization_repository = AuthorizationRepository(db_session)
    document_repository = DocumentRepository(db_session)

    # 6. Create service
    document_service = DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=document_repository,
        storage_service=None,
        workflow_repository=None,
        graph=None,
        db=db_session,
    )

    # 7. Prepare a PDF upload
    upload_file = UploadFile(
        file=BytesIO(b"%PDF-1.4 test content"),
        filename="test.pdf",
    )

    # 8. User B attempts to upload to Organization A's authorization
    with pytest.raises(HTTPException) as error:
        asyncio.run(
            document_service.upload_document(
                authorization_id=authorization_a.id,
                user_id=user_b.id,
                organization_id=organization_b.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 404

    # 9. Verify no document was created
    documents = db_session.query(Document).all()

    assert documents == []
