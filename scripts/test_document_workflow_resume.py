
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.document_service import DocumentService


def test_workflow_resume_after_upload():

    # 1. Create mocked dependencies
    auth_repo = MagicMock()
    document_repo = MagicMock()
    storage_service = MagicMock()
    workflow_repo = MagicMock()
    graph = MagicMock()
    db = MagicMock()

    # 2. Mock authorization
    authorization = SimpleNamespace(
        id=101,
        status="REQUEST_INFORMATION"
    )

    # 3. Mock workflow
    workflow = SimpleNamespace(
        id=1,
        authorization_id=101,
        organization_id=10,
        thread_id="test-thread-101",
        workflow_status="AWAITING_PROVIDER_INFORMATION"
    )

    workflow_repo.get_by_authorization_for_update.return_value = workflow

    # 4. Mock processed clinical pages
    clinical_pages = [
        {
            "evidence_id": "DOC-15-PAGE-1",
            "document_id": 15,
            "filename": "medical_report.pdf",
            "page_number": 1,
            "text": "Patient clinical history."
        }
    ]

    # 5. Mock LangGraph human-review interruption
    human_review_interrupt = SimpleNamespace(
        value={
            "message": (
                "Human review is required before this "
                "authorization can proceed."
            )
        }
    )

    graph.invoke.return_value = {
        "__interrupt__": [human_review_interrupt]
    }

    # 6. Create DocumentService
    service = DocumentService(
        authorization_repository=auth_repo,
        document_reposetory=document_repo,
        storage_service=storage_service,
        workflow_repository=workflow_repo,
        graph=graph,
        db=db
    )

    service._get_processed_clinical_pages = MagicMock(
        return_value=clinical_pages
    )

    # 7. Resume workflow
    result = service._resume_workflow_after_upload(
        authorization=authorization,
        organization_id=10
    )

    # 8. Verify authorization status
    assert authorization.status == "IN_REVIEW"

    # 9. Verify workflow status
    assert workflow.workflow_status == "WAITING_FOR_REVIEW"

    assert result == workflow

    # 10. Verify graph invocation
    graph.invoke.assert_called_once()

    args, kwargs = graph.invoke.call_args

    resume_command = args[0]

    assert resume_command.resume == {
        "event": "DOCUMENTS_SUBMITTED",
        "clinical_pages": clinical_pages
    }

    assert (
        kwargs["config"]["configurable"]["thread_id"]
        == "test-thread-101"
    )

    # 11. Verify database commits
    assert db.commit.call_count == 2

    print("Clinical pages retrieved successfully.")
    print("Existing LangGraph workflow resumed.")
    print("Human-review interruption verified.")
    print("Authorization status updated to IN_REVIEW.")
    print("Workflow status updated to WAITING_FOR_REVIEW.")
    print("Workflow resume test passed!")


if __name__ == "__main__":
    test_workflow_resume_after_upload()
