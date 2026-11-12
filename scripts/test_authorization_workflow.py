from unittest.mock import MagicMock

import pytest

from app.services.authorization_service import AuthorizationService


@pytest.fixture
def service():
    repository = MagicMock()
    db = MagicMock()
    coverage_repository = MagicMock()
    workflow_repository = MagicMock()
    policy_repository = MagicMock()
    document_repository = MagicMock()
    graph = MagicMock()

    service = AuthorizationService(
        repository=repository,
        db=db,
        coverage_repository=coverage_repository,
        workflow_repository=workflow_repository,
        policy_repository=policy_repository,
        document_repository=document_repository,
        graph=graph
    )

    return service


def test_workflow_pauses_for_human_review(service):
    # Arrange
    authorization = MagicMock()
    authorization.id = 101
    authorization.status = "DRAFT"

    service.repository.get_by_id_for_user.return_value = authorization
    service.workflow_repository.get_by_authorization.return_value = None

    service.build_initial_state = MagicMock(return_value={
        "authorization_id": 101,
        "thread_id": "test-thread-123"
    })

    service.graph.invoke.return_value = {
        "__interrupt__": ["Human review required"]
    }

    # Act
    result = service.start_authorization_workflow(
        authorization_id=101,
        user_id=1,
        organization_id=5
    )

    # Assert
    assert result.workflow_status == "WAITING_FOR_REVIEW"
    assert authorization.status == "SUBMITTED"

    service.graph.invoke.assert_called_once()
    service.db.commit.assert_called()

def test_duplicate_submission_does_not_start_graph(service):
    # Arrange
    authorization = MagicMock()
    authorization.id = 101
    authorization.status = "SUBMITTED"

    existing_workflow = MagicMock()
    existing_workflow.workflow_status = "WAITING_FOR_REVIEW"
    existing_workflow.thread_id = "existing-thread-123"

    service.repository.get_by_id_for_user.return_value = authorization

    service.workflow_repository.get_by_authorization.return_value = (
        existing_workflow
    )

    # Act
    result = service.start_authorization_workflow(
        authorization_id=101,
        user_id=1,
        organization_id=5
    )

    # Assert
    assert result is existing_workflow

    service.graph.invoke.assert_not_called()

    service.workflow_repository.create.assert_not_called()


def test_workflow_is_marked_failed_when_graph_fails(service):
    # Arrange
    authorization = MagicMock()
    authorization.id = 101
    authorization.status = "DRAFT"

    service.repository.get_by_id_for_user.return_value = authorization
    service.workflow_repository.get_by_authorization.return_value = None

    service.build_initial_state = MagicMock(return_value={
        "authorization_id": 101
    })

    service.graph.invoke.side_effect = RuntimeError(
        "Simulated graph execution failure"
    )

    failed_workflow = MagicMock()
    service.workflow_repository.get_by_authorization.return_value = None

    # Return no workflow for the initial check, then the failed record
    service.workflow_repository.get_by_authorization.side_effect = [
        None,
        failed_workflow
    ]

    # Act and Assert
    with pytest.raises(
        RuntimeError,
        match="Simulated graph execution failure"
    ):
        service.start_authorization_workflow(
            authorization_id=101,
            user_id=1,
            organization_id=5
        )

    assert failed_workflow.workflow_status == "FAILED"
    service.graph.invoke.assert_called_once()

from sqlalchemy.exc import IntegrityError


def test_concurrent_submission_returns_existing_workflow(service):
    # Arrange
    authorization = MagicMock()
    authorization.id = 101
    authorization.status = "DRAFT"

    existing_workflow = MagicMock()
    existing_workflow.workflow_status = "RUNNING"
    existing_workflow.thread_id = "existing-thread-123"

    service.repository.get_by_id_for_user.return_value = authorization

    # First lookup: no workflow exists.
    # Second lookup: another request has created it.
    service.workflow_repository.get_by_authorization.side_effect = [
        None,
        existing_workflow
    ]

    # Simulate the database unique constraint rejecting
    # the duplicate workflow during flush().
    service.workflow_repository.create.side_effect = IntegrityError(
        "INSERT INTO authorization_workflows",
        {},
        Exception("Duplicate authorization_id")
    )

    # Act
    result = service.start_authorization_workflow(
        authorization_id=101,
        user_id=1,
        organization_id=5
    )

    # Assert
    assert result is existing_workflow
    assert result.workflow_status == "RUNNING"

    service.db.rollback.assert_called_once()
    service.graph.invoke.assert_not_called()
