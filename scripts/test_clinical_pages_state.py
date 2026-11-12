
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.authorization_service import AuthorizationService


def test_clinical_pages_state():

    # Mock all repository dependencies
    auth_repo = MagicMock()
    coverage_repo = MagicMock()
    workflow_repo = MagicMock()
    policy_repo = MagicMock()
    document_repo = MagicMock()
    db = MagicMock()
    graph = MagicMock()

    # Mock authorization
    authorization = SimpleNamespace(
        id=101,
        member_id="MEM001",
        member_record_id=12,
        procedure_code="PROC001",
        diagnosis_code="DIAG001",
        clinical_summary="Patient requires treatment.",
        service_date=date(2026, 11, 6)
    )

    # Mock processed documents and extracted pages
    documents = [
        SimpleNamespace(
            id=501,
            filename="medical_report.pdf",
            pages=[
                SimpleNamespace(
                    page_number=1,
                    text="Patient diagnosis and clinical findings."
                ),
                SimpleNamespace(
                    page_number=2,
                    text="Physician treatment recommendation."
                )
            ]
        )
    ]

    # Configure repository responses
    coverage_repo.get_coverage_for_eligibility.return_value = [
        {"coverage_id": 55}
    ]

    policy_repo.get_active_policy_version_ids.return_value = [10, 11]

    document_repo.get_processed_documents_with_pages.return_value = documents

    # Create service
    service = AuthorizationService(
        repository=auth_repo,
        db=db,
        coverage_repository=coverage_repo,
        workflow_repository=workflow_repo,
        policy_repository=policy_repo,
        document_repository=document_repo,
        graph=graph
    )

    # Build initial graph state
    state = service.build_initial_state(
        authorization=authorization,
        organization_id=10,
        thread_id="test-thread-101"
    )

    # Verify document repository was called with tenant context
    document_repo.get_processed_documents_with_pages.assert_called_once_with(
        authorization_id=101,
        organization_id=10
    )

    # Verify extracted pages entered graph state
    assert len(state["clinical_pages"]) == 2

    assert state["clinical_pages"][0]["evidence_id"] == "DOC-501-PAGE-1"
    assert state["clinical_pages"][0]["text"] == (
        "Patient diagnosis and clinical findings."
    )

    assert state["clinical_pages"][1]["evidence_id"] == "DOC-501-PAGE-2"

    # Verify other initial state fields
    assert state["organization_id"] == 10
    assert state["thread_id"] == "test-thread-101"
    assert state["active_policy_version_ids"] == [10, 11]

    print("Tenant context verified.")
    print("Clinical document pages loaded.")
    print("Evidence IDs generated correctly.")
    print("Initial LangGraph state verified.")
    print("Clinical pages state test passed!")


if __name__ == "__main__":
    test_clinical_pages_state()
