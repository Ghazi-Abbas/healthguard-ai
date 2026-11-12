
import logging
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.document_service import DocumentService, logger

import pytest

from app.security.classification import (
    DataClassification,
    classify_field,
)

from app.security.data_classifier import (
    get_highest_classification,
)



def test_document_processing_success_log_is_safe(caplog):

    with caplog.at_level(logging.INFO, logger=logger.name):

        logger.info(
            "Document processing completed successfully"
        )

    assert (
        "Document processing completed successfully"
        in caplog.text
    )

    assert "patient@example.com" not in caplog.text


def test_document_processing_failure_log_is_safe(caplog):

    with caplog.at_level(logging.ERROR, logger=logger.name):

        logger.error(
            "Document processing failed"
        )

    assert "Document processing failed" in caplog.text

    assert "clinical_summary" not in caplog.text


@pytest.mark.anyio
async def test_upload_document_logs_success(caplog, anyio_backend):
    authorization = MagicMock()
    authorization.id = 10
    authorization.status = "DRAFT"

    authorization_repository = MagicMock()
    authorization_repository.get_by_id_for_user.return_value = authorization

    document_repository = MagicMock()

    def create_document(document):
        document.id = 100

    document_repository.create.side_effect = create_document

    storage_service = MagicMock()
    workflow_repository = MagicMock()
    db = MagicMock()

    service = DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=document_repository,
        storage_service=storage_service,
        workflow_repository=workflow_repository,
        graph=MagicMock(),
        db=db,
    )

    fake_page = MagicMock()
    fake_page.extract_text.return_value = "Synthetic clinical information"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page]

    upload = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"%PDF-1.4 synthetic PDF content"),
        headers=Headers({"content-type": "application/pdf"}),
    )

    with patch(
        "app.services.document_service.PdfReader",
        return_value=fake_reader,
    ):
        with caplog.at_level(logging.INFO, logger=logger.name):
            result = await service.upload_document(
                authorization_id=10,
                user_id=1,
                file=upload,
                organization_id=1,
            )

    assert result.processing_status == "PROCESSED"

    assert (
        "Document processing completed successfully"
        in caplog.text
    )

    storage_service.upload_file.assert_called_once()
    document_repository.create_page.assert_called_once()\


@pytest.mark.anyio
async def test_upload_document_logs_failure(caplog, anyio_backend):
    from fastapi import HTTPException

    authorization = MagicMock()
    authorization.id = 10
    authorization.status = "DRAFT"

    authorization_repository = MagicMock()
    authorization_repository.get_by_id_for_user.return_value = authorization

    document_repository = MagicMock()

    def create_document(document):
        document.id = 100

    document_repository.create.side_effect = create_document

    storage_service = MagicMock()
    workflow_repository = MagicMock()
    db = MagicMock()

    service = DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=document_repository,
        storage_service=storage_service,
        workflow_repository=workflow_repository,
        graph=MagicMock(),
        db=db,
    )

    upload = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"%PDF-1.4 synthetic PDF content"),
        headers=Headers({"content-type": "application/pdf"}),
    )

    with patch(
        "app.services.document_service.PdfReader",
        side_effect=ValueError("Synthetic PDF parsing error"),
    ):
        with caplog.at_level(logging.ERROR, logger=logger.name):
            with pytest.raises(HTTPException) as exc_info:
                await service.upload_document(
                    authorization_id=10,
                    user_id=1,
                    file=upload,
                    organization_id=1,
                )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == (
        "Unable to process the PDF. Please upload another document."
    )

    assert "Document processing failed" in caplog.text

    assert "Synthetic PDF parsing error" not in caplog.text

    storage_service.delete_file.assert_called_once()


@pytest.mark.anyio
async def test_s3_cleanup_failure_does_not_expose_details(
    caplog, anyio_backend
):
    from fastapi import HTTPException

    authorization = MagicMock()
    authorization.id = 10
    authorization.status = "DRAFT"

    authorization_repository = MagicMock()
    authorization_repository.get_by_id_for_user.return_value = authorization

    document_repository = MagicMock()

    def create_document(document):
        document.id = 100

    document_repository.create.side_effect = create_document

    storage_service = MagicMock()
    storage_service.delete_file.side_effect = RuntimeError(
        "Synthetic S3 credentials failure"
    )

    service = DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=document_repository,
        storage_service=storage_service,
        workflow_repository=MagicMock(),
        graph=MagicMock(),
        db=MagicMock(),
    )

    upload = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"%PDF-1.4 synthetic PDF content"),
        headers=Headers({"content-type": "application/pdf"}),
    )

    with patch(
        "app.services.document_service.PdfReader",
        side_effect=ValueError("Synthetic PDF parsing error"),
    ):
        with caplog.at_level(logging.ERROR, logger=logger.name):
            with pytest.raises(HTTPException) as exc_info:
                await service.upload_document(
                    authorization_id=10,
                    user_id=1,
                    file=upload,
                    organization_id=1,
                )

    assert exc_info.value.status_code == 422

    assert "Document processing failed" in caplog.text
    assert "Failed to delete uploaded PDF from S3" in caplog.text

    assert "Synthetic S3 credentials failure" not in caplog.text
    assert "Synthetic PDF parsing error" not in caplog.text

    storage_service.delete_file.assert_called_once()


def test_known_field_returns_correct_classification():
    result = classify_field("email")

    assert result == DataClassification.PII


def test_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="Unknown data classification"):
        classify_field("unknown_patient_data")


def test_nested_unknown_field_is_rejected():
    data = {
        "organization_id": 1,
        "patient_information": {
            "unknown_medical_field": "some value"
        },
    }

    with pytest.raises(ValueError, match="Unknown data classification"):
        get_highest_classification(data)


def test_nested_phi_returns_highest_classification():
    data = {
        "organization_id": 1,
        "clinical_summary": "Synthetic clinical summary",
    }

    result = get_highest_classification(data)

    assert result == DataClassification.PHI


def test_secret_has_higher_priority_than_pii():
    data = {
        "email": "test@example.com",
        "password": "synthetic-password",
    }

    result = get_highest_classification(data)

    assert result == DataClassification.SECRET


def test_empty_dictionary_is_rejected():
    with pytest.raises(ValueError):
        get_highest_classification({})


def test_non_string_field_name_is_rejected():
    data = {
        123: "some value"
    }

    with pytest.raises(ValueError):
        get_highest_classification(data)
