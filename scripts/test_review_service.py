
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.review_service import ReviewService


def create_service():

    # Mock database
    db = MagicMock()

    # Mock repositories
    auth_repo = MagicMock()
    review_repo = MagicMock()
    workflow_repo = MagicMock()

    # Mock authorization
    authorization = SimpleNamespace(
        id=101,
        status="SUBMITTED"
    )

    # Mock workflow
    workflow = SimpleNamespace(
        id=1,
        thread_id="test-thread-101",
        workflow_status="WAITING_FOR_REVIEW"
    )

    auth_repo.get_by_id_for_organization_for_update.return_value = authorization

    workflow_repo.get_by_authorization_for_update.return_value = workflow
    workflow_repo.get_by_authorization.return_value = workflow

    # Mock LangGraph
    graph = MagicMock()
    graph.invoke.return_value = {
        "human_decision": "APPROVE",
        "workflow_status": "REVIEW_COMPLETED"
    }

    service = ReviewService(
        auth_repo=auth_repo,
        review_repo=review_repo,
        workflow_repo=workflow_repo,
        graph=graph,
        db=db
    )

    return (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    )


# ============================================================
# TEST 1: APPROVE
# ============================================================
def test_approve():

    (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    ) = create_service()

    result = service.approve(
        authorization_id=101,
        organization_id=10,
        reviewer_id=5,
        comments="Evidence verified"
    )

    assert result.status == "APPROVED"
    assert workflow.workflow_status == "REVIEW_COMPLETED"

    review_repo.create.assert_called_once()

    graph.invoke.assert_called_once()

    args, kwargs = graph.invoke.call_args

    assert kwargs["config"]["configurable"]["thread_id"] == "test-thread-101"

    assert args[0].resume == {
        "decision": "APPROVE",
        "notes": "Evidence verified"
    }

    assert db.commit.call_count == 2

    print("APPROVE test passed")


# ============================================================
# TEST 2: REJECT
# ============================================================
def test_reject():

    (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    ) = create_service()

    result = service.reject(
        authorization_id=101,
        organization_id=10,
        reviewer_id=5,
        comments="Criteria not satisfied"
    )

    assert result.status == "REJECTED"
    assert workflow.workflow_status == "REVIEW_COMPLETED"

    graph.invoke.assert_called_once()

    print("REJECT test passed")


# ============================================================
# TEST 3: REQUEST INFORMATION
# ============================================================
def test_request_information():

    (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    ) = create_service()

    # Simulate LangGraph pausing for provider documents
    graph.invoke.return_value = {
        "__interrupt__": ["Waiting for provider documents"]
    }

    result = service.request_information(
        authorization_id=101,
        organization_id=10,
        reviewer_id=5,
        message="Please provide additional clinical evidence"
    )

    assert result.status == "REQUEST_INFORMATION"

    assert workflow.workflow_status == "AWAITING_PROVIDER_INFORMATION"

    args, kwargs = graph.invoke.call_args

    assert args[0].resume == {
        "decision": "REQUEST_INFORMATION",
        "notes": "Please provide additional clinical evidence"
    }

    assert kwargs["config"]["configurable"]["thread_id"] == "test-thread-101"

    graph.invoke.assert_called_once()

    print("REQUEST_INFORMATION test passed")

# ============================================================
# TEST 4: GRAPH FAILURE
# ============================================================
def test_graph_failure():

    (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    ) = create_service()

    graph.invoke.side_effect = RuntimeError(
        "Simulated graph failure"
    )

    with pytest.raises(HTTPException) as error:

        service.approve(
            authorization_id=101,
            organization_id=10,
            reviewer_id=5
        )

    assert error.value.status_code == 503

    assert workflow.workflow_status == "RESUME_FAILED"

    # Decision was committed before graph invocation.
    assert db.commit.call_count == 2

    print("GRAPH FAILURE test passed")





# ============================================================
# TEST 5: PREVENT DUPLICATE REVIEW DECISIONS
# ============================================================
def test_duplicate_review_decision():

    (
        service,
        authorization,
        workflow,
        auth_repo,
        review_repo,
        workflow_repo,
        graph,
        db
    ) = create_service()

    # First reviewer approves
    service.approve(
        authorization_id=101,
        organization_id=10,
        reviewer_id=5,
        comments="Approved"
    )

    assert authorization.status == "APPROVED"

    # Second reviewer attempts to reject the same authorization
    with pytest.raises(HTTPException) as error:

        service.reject(
            authorization_id=101,
            organization_id=10,
            reviewer_id=6,
            comments="Attempted duplicate decision"
        )

    assert error.value.status_code == 400

    # Only the first decision should be saved and processed
    review_repo.create.assert_called_once()
    graph.invoke.assert_called_once()

    print("DUPLICATE REVIEW DECISION test passed")


# ============================================================
# RUN TESTS
# ============================================================
if __name__ == "__main__":

    test_approve()
    test_reject()
    test_request_information()
    test_graph_failure()
    test_duplicate_review_decision()

    print("\nAll review service tests passed!")
