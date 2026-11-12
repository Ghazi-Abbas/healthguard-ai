
import asyncio
from io import BytesIO
from datetime import date
from unittest.mock import Mock
from pypdf import PdfWriter
from app.models.document import Document
import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.models.organization import Organization
from app.models.user import User
from app.models.member import Member
from app.models.authorization import Authorization

from app.repositories.autharization_repository import AuthorizationRepository
from app.repositories.document_repository import DocumentRepository

from app.services.document_service import DocumentService


def create_document_service(db_session):
    # Create an organization
    organization = Organization(name="Test Organization")
    db_session.add(organization)
    db_session.flush()

    # Create a provider
    user = User(
        email="provider@example.com",
        username="provider",
        password_hash="test_hash",
        role="PROVIDER",
        organization_id=organization.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create a member
    member = Member(
        organization_id=organization.id,
        external_member_id="MEM-001",
        name="Test Member",
        date_of_birth=date(1990, 1, 1),
    )
    db_session.add(member)
    db_session.flush()

    # Create an authorization
    authorization = Authorization(
        member_id=member.external_member_id,
        member_record_id=member.id,
        procedure_code="PROC-001",
        diagnosis_code="DIAG-001",
        clinical_summary="Test clinical summary",
        status="DRAFT",
        user_id=user.id,
        service_date=date(2026, 11, 6),
    )
    db_session.add(authorization)
    db_session.commit()

    # Mock storage so tests never contact S3
    storage_service = Mock()

    service = DocumentService(
        authorization_repository=AuthorizationRepository(db_session),
        document_reposetory=DocumentRepository(db_session),
        storage_service=storage_service,
        workflow_repository=None,
        graph=None,
        db=db_session,
    )

    return service, user, organization, authorization, storage_service


def create_upload_file(content, content_type="application/pdf"):
    return UploadFile(
        file=BytesIO(content),
        filename="test.pdf",
        headers=Headers({
            "content-type": content_type
        }),
    )


def test_empty_pdf_upload_is_rejected(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    upload_file = create_upload_file(b"")

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 400
    assert error.value.detail == "File is empty"

    # Storage must not be called for an empty file
    storage.upload_file.assert_not_called()

def test_invalid_pdf_signature_is_rejected(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # File contains text, not actual PDF data
    upload_file = create_upload_file(
        b"This is not a PDF file"
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Invalid PDF file"

    # Invalid files must never reach S3
    storage.upload_file.assert_not_called()
def test_oversized_pdf_upload_is_rejected(db_session, monkeypatch):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # Set maximum file size to 1 MB for this test
    monkeypatch.setattr(
        "app.services.document_service.settings.MAX_FILE_SIZE_MB",
        1
    )

    # Create a PDF-like file larger than 1 MB
    file_content = b"%PDF-" + (b"x" * (1024 * 1024))

    upload_file = create_upload_file(file_content)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 413
    assert error.value.detail == "File size cannot exceed 1 MB"

    # Oversized files must never reach S3
    storage.upload_file.assert_not_called()

def test_non_pdf_content_type_is_rejected(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # The content looks like a PDF, but the MIME type is text/plain.
    upload_file = create_upload_file(
        b"%PDF-1.4\nTest content",
        content_type="text/plain",
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Only PDF files are allowed"

    storage.upload_file.assert_not_called()


def test_malformed_pdf_is_rejected(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # Has a PDF signature but is not a valid PDF document.
    upload_file = create_upload_file(
        b"%PDF-1.4\nThis is not a valid PDF document."
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 422
    assert error.value.detail == "Unable to process the PDF. Please upload another document."


def test_valid_pdf_upload_is_processed_successfully(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # Generate a real PDF in memory with one blank page.
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=72, height=72)

    pdf_buffer = BytesIO()
    pdf_writer.write(pdf_buffer)

    pdf_content = pdf_buffer.getvalue()

    upload_file = create_upload_file(pdf_content)

    document = asyncio.run(
        service.upload_document(
            authorization_id=authorization.id,
            user_id=user.id,
            organization_id=organization.id,
            file=upload_file,
        )
    )

    # 1. Verify the document was uploaded to storage.
    storage.upload_file.assert_called_once()

    storage.upload_file.assert_called_once_with(
        file_bytes=pdf_content,
        object_key=document.storage_path,
        content_type="application/pdf",
    )

    # 2. Verify the document record.
    assert document.id is not None
    assert document.authorization_id == authorization.id
    assert document.filename == "test.pdf"

    # 3. Verify PDF processing.
    assert document.processing_status == "PROCESSED"
    assert document.page_count == 1

    # 4. Verify the extracted page was saved in the database.
    db_session.expire(document, ["pages"])

    assert len(document.pages) == 1
    assert document.pages[0].page_number == 1

def test_zero_page_pdf_is_marked_as_failed(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # Generate a valid PDF structure containing zero pages.
    pdf_writer = PdfWriter()

    pdf_buffer = BytesIO()
    pdf_writer.write(pdf_buffer)

    upload_file = create_upload_file(pdf_buffer.getvalue())

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    assert error.value.status_code == 422
    assert error.value.detail == (
        "Unable to process the PDF. Please upload another document."
    )

    # Storage was called before PDF page validation.
    storage.upload_file.assert_called_once()

    # The document record should remain, marked as FAILED.
    failed_document = (
        db_session.query(Document)
        .filter_by(authorization_id=authorization.id)
        .one()
    )

    assert failed_document.processing_status == "FAILED"
    assert failed_document.page_count == 0

def test_s3_cleanup_failure_does_not_hide_pdf_error(db_session):
    service, user, organization, authorization, storage = (
        create_document_service(db_session)
    )

    # Generate a valid PDF with zero pages.
    pdf_writer = PdfWriter()
    pdf_buffer = BytesIO()
    pdf_writer.write(pdf_buffer)

    upload_file = create_upload_file(pdf_buffer.getvalue())

    # Simulate S3 deletion failure.
    storage.delete_file.side_effect = Exception(
        "S3 service unavailable"
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            service.upload_document(
                authorization_id=authorization.id,
                user_id=user.id,
                organization_id=organization.id,
                file=upload_file,
            )
        )

    # Original PDF processing error must be preserved.
    assert error.value.status_code == 422
    assert error.value.detail == (
        "Unable to process the PDF. Please upload another document."
    )

    # Verify cleanup was attempted.
    storage.delete_file.assert_called_once()

    # Verify document status was preserved.
    failed_document = (
        db_session.query(Document)
        .filter_by(authorization_id=authorization.id)
        .one()
    )

    assert failed_document.processing_status == "FAILED"
