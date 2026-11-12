
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.services.policy_ingestion_service import PolicyIngestionService


def test_policy_ingestion_rejects_phi_before_vector_store_delete():
    repository = MagicMock()
    service = PolicyIngestionService(repository)

    document = MagicMock()
    document.processing_status = "PROCESSED"
    document.pages = [
        MagicMock(
            page_number=1,
            text="Policy document text",
        )
    ]

    repository.get_document_for_ingestion.return_value = document

    chunks = [
        Document(
            page_content="Patient diagnosis and clinical history",
            metadata={},
        )
    ]

    with patch(
        "app.services.policy_ingestion_service.split_policy_pages",
        return_value=chunks,
    ), patch(
        "app.services.policy_ingestion_service.get_semantic_vector_store"
    ) as vector_store_factory, patch(
        "app.services.policy_ingestion_service.validate_embedding_authorization",
        side_effect=PermissionError("PHI is not authorized"),
    ):
        with pytest.raises(PermissionError):
            service.index_policy_documents(
                organization_id=1,
                policy_version_id=1,
                document_id=1,
            )

    # The vector store must not be accessed if authorization fails.
    vector_store_factory.assert_not_called()


def test_policy_ingestion_allows_authorized_policy_text():
    repository = MagicMock()
    service = PolicyIngestionService(repository)

    document = MagicMock()
    document.processing_status = "PROCESSED"
    document.pages = [
        MagicMock(
            page_number=1,
            text="Official organizational policy content",
        )
    ]

    repository.get_document_for_ingestion.return_value = document

    chunks = [
        Document(
            page_content="Official organizational policy content",
            metadata={},
        )
    ]

    vector_store = MagicMock()

    with patch(
        "app.services.policy_ingestion_service.split_policy_pages",
        return_value=chunks,
    ), patch(
        "app.services.policy_ingestion_service.get_semantic_vector_store",
        return_value=vector_store,
    ):
        result = service.index_policy_documents(
            organization_id=1,
            policy_version_id=1,
            document_id=1,
        )

    assert result == 1

    # Confirm the previous index is deleted only after authorization.
    vector_store.delete.assert_called_once_with(
        filter={
            "organization_id": 1,
            "document_id": 1,
        }
    )

    # Confirm the authorized chunks are indexed.
    vector_store.add_documents.assert_called_once_with(
        documents=chunks,
        ids=["org-1-doc-1-chunk-0"],
    )
