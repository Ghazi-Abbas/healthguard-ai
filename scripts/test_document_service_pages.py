
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.document_service import DocumentService


def test_get_processed_clinical_pages():

    # Mock repositories and dependencies
    auth_repo = MagicMock()
    document_repo = MagicMock()
    storage_service = MagicMock()
    db = MagicMock()

    # Mock processed document pages
    document_repo.get_processed_documents_with_pages.return_value = [
        SimpleNamespace(
            id=15,
            filename="medical_report.pdf",
            pages=[
                SimpleNamespace(
                    page_number=1,
                    text="Patient clinical history."
                ),
                SimpleNamespace(
                    page_number=2,
                    text="Patient treatment details."
                )
            ]
        )
    ]

    service = DocumentService(
        authorization_repository=auth_repo,
        document_reposetory=document_repo,
        storage_service=storage_service,
        workflow_repository=MagicMock(),
        graph=MagicMock(),
        db=db
    )

    pages = service._get_processed_clinical_pages(
        authorization_id=101,
        organization_id=10
    )

    assert len(pages) == 2

    assert pages[0]["evidence_id"] == "DOC-15-PAGE-1"
    assert pages[1]["evidence_id"] == "DOC-15-PAGE-2"

    assert pages[0]["text"] == "Patient clinical history."

    document_repo.get_processed_documents_with_pages.assert_called_once_with(
        authorization_id=101,
        organization_id=10
    )

    print("Clinical pages preparation test passed!")


if __name__ == "__main__":
    test_get_processed_clinical_pages()
