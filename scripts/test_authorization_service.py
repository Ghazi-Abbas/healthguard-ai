
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.authorization_service import AuthorizationService


def test_create_authorization_maps_member_ids():

    repository = MagicMock()
    db = MagicMock()
    coverage_repository = MagicMock()
    user_repository = MagicMock()

    workflow_repository = MagicMock()
    policy_repository = MagicMock()
    document_repository = MagicMock()
    graph = MagicMock()

    # Mock user belonging to the requested organization
    user_repository.get_by_id_for_organization.return_value = (
        SimpleNamespace(
            id=7,
            organization_id=3
        )
    )

    # Mock active member coverage
    coverage_repository.get_active_coverage_for_service_date.return_value = (
        SimpleNamespace(
            id=55,
            member_id=12
        )
    )

    # Return the authorization object passed to create()
    repository.create.side_effect = lambda authorization: authorization

    service = AuthorizationService(
        repository=repository,
        db=db,
        coverage_repository=coverage_repository,
        workflow_repository=workflow_repository,
        policy_repository=policy_repository,
        document_repository=document_repository,
        graph=graph,
        user_repository=user_repository
    )

    request = SimpleNamespace(
        member_id="MEM001",
        plan_id=101,
        service_date=date(2026, 11, 5),
        procedure_code="PROC001",
        diagnosis_code="DIAG001",
        clinical_summary="Test clinical summary"
    )

    result = service.create(
        request=request,
        user_id=7,
        organization_id=3
    )

    # Verify member ID mapping
    assert result.member_id == "MEM001"
    assert result.member_record_id == 12
    assert result.member_coverage_id == 55
    assert result.status == "DRAFT"

    # Verify user organization validation
    user_repository.get_by_id_for_organization.assert_called_once_with(
        user_id=7,
        organization_id=3
    )

    # Verify database commit
    db.commit.assert_called_once()

    print("External member ID:", result.member_id)
    print("Internal member ID:", result.member_record_id)
    print("Coverage ID:", result.member_coverage_id)
    print("Authorization creation test passed.")
