
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.services.document_service import DocumentService


def test_workflow_resume_failure():

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

    # 5. Create DocumentService
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

    # 6. Simulate LangGraph failure
    graph.invoke.side_effect = RuntimeError(
        "Simulated graph failure"
    )

    # 7. Execute and verify failure handling
    try:

        service._resume_workflow_after_upload(
            authorization=authorization,
            organization_id=10
        )

        raise AssertionError(
            "Expected HTTPException was not raised"
        )

    except HTTPException as exc:

        assert exc.status_code == 503

        print("HTTP 503 returned successfully.")

    # 8. Verify workflow failure status
    assert workflow.workflow_status == "RESUME_FAILED"

    # 9. Verify rollback and failure commit
    assert db.rollback.call_count == 1

    assert db.commit.call_count == 2

    print("Graph failure caught successfully.")
    print("Workflow marked as RESUME_FAILED.")
    print("Database rollback verified.")
    print("Failure status committed successfully.")

    print("Document workflow failure test passed!")


if __name__ == "__main__":
    test_workflow_resume_failure()
