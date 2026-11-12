
from uuid import uuid4
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from pypdf import PdfReader
from langgraph.types import Command

from app.repositories.autharization_repository import AuthorizationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.authorization_workflow_repository import (
    AuthorizationWorkflowRepository
)

from app.services.storage_service import S3StorageService

from app.models.document import Document, DocumentPage

from app.core.config import settings
import logging
logger = logging.getLogger(__name__)
class DocumentService:

    def __init__(
        self,
        authorization_repository: AuthorizationRepository,
        document_reposetory: DocumentRepository,
        storage_service: S3StorageService,
        workflow_repository: AuthorizationWorkflowRepository,
        graph,
        db: Session
    ):

        self.authorization_repository = authorization_repository
        self.document_reposetory = document_reposetory
        self.storage_service = storage_service
        self.workflow_repository = workflow_repository
        self.graph = graph
        self.db = db

    # ====================================================
    # PREPARE PROCESSED CLINICAL PAGES
    # ====================================================

    def _get_processed_clinical_pages(
        self,
        authorization_id: int,
        organization_id: int
    ) -> list:

        # 1. Retrieve processed documents and their pages
        documents = (
            self.document_reposetory.get_processed_documents_with_pages(
                authorization_id=authorization_id,
                organization_id=organization_id
            )
        )

        # 2. Prepare clinical evidence for LangGraph
        clinical_pages = []

        for document in documents:

            for page in document.pages:

                clinical_pages.append({
                    "evidence_id": (
                        f"DOC-{document.id}-PAGE-{page.page_number}"
                    ),
                    "document_id": document.id,
                    "filename": document.filename,
                    "page_number": page.page_number,
                    "text": page.text
                })

        return clinical_pages

    # ====================================================
    # RESUME WORKFLOW AFTER PROVIDER UPLOAD
    # ====================================================

    def _resume_workflow_after_upload(
        self,
        authorization,
        organization_id: int
    ):

        # 1. Find and lock the existing workflow
        workflow = (
            self.workflow_repository.get_by_authorization_for_update(
                authorization_id=authorization.id,
                organization_id=organization_id
            )
        )

        if workflow is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization workflow not found"
            )

        # 2. Verify workflow status
        if workflow.workflow_status != "AWAITING_PROVIDER_INFORMATION":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workflow is not waiting for provider information"
            )

        # 3. Verify authorization status
        if authorization.status != "REQUEST_INFORMATION":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Authorization is not waiting for provider information"
            )

        # 4. Retrieve trusted clinical pages from PostgreSQL
        clinical_pages = self._get_processed_clinical_pages(
            authorization_id=authorization.id,
            organization_id=organization_id
        )

        if not clinical_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No processed clinical pages found"
            )

        # 5. Mark workflow as reanalysis
        workflow.workflow_status = "REANALYSIS"

        # Commit before invoking the graph.
        # This also releases the database row lock.
        self.db.commit()

        try:

            # 6. Prepare provider upload event
            resume_payload = {
                "event": "DOCUMENTS_SUBMITTED",
                "clinical_pages": clinical_pages
            }

            # 7. Use the existing LangGraph thread ID
            config = {
                "configurable": {
                    "thread_id": workflow.thread_id
                }
            }

            # 8. Resume the existing PostgreSQL checkpoint
            result = self.graph.invoke(
                Command(resume=resume_payload),
                config=config
            )

            # 9. Verify graph paused again for human review
            interrupts = result.get("__interrupt__", [])

            if not interrupts:
                raise RuntimeError(
                    "Graph did not pause for human review after reanalysis"
                )

            # Get the interruption payload
            interrupt_value = interrupts[0].value

            # Verify that the graph paused at human review
            if interrupt_value.get("message") != (
                "Human review is required before this authorization can proceed."
            ):
                raise RuntimeError(
                    "Graph did not pause at the human review node"
                )

            # 10. Update authorization and workflow status
            authorization.status = "IN_REVIEW"

            workflow.workflow_status = "WAITING_FOR_REVIEW"

            self.db.commit()

            self.db.refresh(workflow)

            return workflow

        except Exception as error:

            # Roll back failed workflow updates
            self.db.rollback()

            # Retrieve workflow again for failure update
            failed_workflow = (
                self.workflow_repository.get_by_authorization_for_update(
                    authorization_id=authorization.id,
                    organization_id=organization_id
                )
            )

            if failed_workflow:

                failed_workflow.workflow_status = "RESUME_FAILED"

                self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Documents were saved, but the authorization "
                    "workflow could not be resumed."
                )
            ) from error

    # ====================================================
    # UPLOAD AUTHORIZATION DOCUMENTS
    # ====================================================

    async def upload_document(
        self,
        authorization_id: int,
        user_id: int,
        file: UploadFile,
        organization_id: int
    ):

        # ====================================================
        # 1. CHECK AUTHORIZATION OWNERSHIP
        # ====================================================

        authorization = (
            self.authorization_repository.get_by_id_for_user(
                authorization_id,
                user_id,
                organization_id
            )
        )

        if authorization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization not found"
            )

        # ====================================================
        # 2. CHECK AUTHORIZATION STATUS
        # ====================================================

        if authorization.status not in (
            "DRAFT",
            "REQUEST_INFORMATION"
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Documents cannot be uploaded for this authorization"
            )

        # ====================================================
        # 3. CHECK MIME TYPE
        # ====================================================

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )

        # ====================================================
        # 4. CALCULATE MAXIMUM FILE SIZE
        # ====================================================
        max_size = (
            settings.MAX_FILE_SIZE_MB
            * 1024
            * 1024
        )


        # ====================================================
        #  5. READ FILE IN SMALL CHUNKS
        # ====================================================

        file_bytes = bytearray()

        chunk_size = 1024 * 1024  # 1 MB

        while True:

            remaining_size = max_size - len(file_bytes)

            chunk = await file.read(
                min(chunk_size, remaining_size + 1)
            )

            if not chunk:
                break

            file_bytes.extend(chunk)

            # Stop immediately if the file exceeds the limit
            if len(file_bytes) > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File size cannot exceed "
                        f"{settings.MAX_FILE_SIZE_MB} MB"
                    )
                )

        # Convert bytearray into bytes
        file_bytes = bytes(file_bytes)


        # ====================================================
        # 6. CHECK EMPTY FILE
        # ====================================================

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # ====================================================
        # 6. CHECK FILE SIZE
        # ====================================================

        max_size = (
            settings.MAX_FILE_SIZE_MB
            * 1024
            * 1024
        )

        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size cannot exceed "
                    f"{settings.MAX_FILE_SIZE_MB} MB"
                )
            )

        # ====================================================
        # 7. CHECK PDF SIGNATURE
        # ====================================================

        if not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # ====================================================
        # 8. ORIGINAL FILE NAME
        # ====================================================

        original_filename = (
            file.filename or "document.pdf"
        )

        # ====================================================
        # 9. CREATE SAFE S3 KEY
        # ====================================================

        extension = Path(original_filename).suffix.lower()

        if extension != ".pdf":
            extension = ".pdf"

        unique_filename = f"{uuid4()}{extension}"

        s3_key = (
            f"organizations/"
            f"{organization_id}/"
            f"authorization_id/"
            f"{authorization_id}/"
            f"documents/"
            f"{unique_filename}"
        )

        # ====================================================
        # 10. UPLOAD FILE TO S3
        # ====================================================

        self.storage_service.upload_file(
            file_bytes=file_bytes,
            object_key=s3_key,
            content_type="application/pdf"
        )

        # ====================================================
        # 11. CREATE DOCUMENT RECORD
        # ====================================================

        document = Document(
            authorization_id=authorization_id,
            filename=original_filename,
            content_type="application/pdf",
            storage_path=s3_key,
            processing_status="PROCESSING",
            page_count=0
        )

        self.document_reposetory.create(document)

        self.db.commit()

        self.db.refresh(document)


        # ====================================================
        # 12. EXTRACT PDF PAGES
        # ====================================================

        try:

            reader = PdfReader(
                BytesIO(file_bytes)
            )

            page_count = len(reader.pages)

            if page_count == 0:
                raise ValueError("PDF contains no pages")

            for page_index, page in enumerate(
                reader.pages,
                start=1
            ):

                text = page.extract_text() or ""

                document_page = DocumentPage(
                    document_id=document.id,
                    page_number=page_index,
                    text=text
                )

                self.document_reposetory.create_page(
                    document_page
                )

            # Mark document as processed
            document.page_count = page_count

            document.processing_status = "PROCESSED"

            self.db.commit()

            self.db.refresh(document)
            logger.info("Document processing completed successfully")

        except Exception as error:

            self.db.rollback()

            document.processing_status = "FAILED"
            self.db.commit()
            logger.error("Document processing failed")

            try:
                self.storage_service.delete_file(s3_key)

            except Exception:
                logger.error(
                    "Failed to delete uploaded PDF from S3",

                )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Unable to process the PDF. "
                    "Please upload another document."
                )
            ) from error

        # ====================================================
        # 13. RESUME WORKFLOW IF INFORMATION WAS REQUESTED
        # ====================================================

        if authorization.status == "REQUEST_INFORMATION":

            self._resume_workflow_after_upload(
                authorization=authorization,
                organization_id=organization_id
            )

        # ====================================================
        # 14. RETURN PROCESSED DOCUMENT
        # ====================================================

        return document

    # ====================================================
    # GET DOCUMENTS
    # ====================================================

    def get_document(
        self,
        authorization_id: int,
        user_id: int,
        organization_id: int
    ):

        # 1. Check authorization ownership
        authorization = (
            self.authorization_repository.get_by_id_for_user(
                authorization_id=authorization_id,
                user_id=user_id,
                organization_id=organization_id
            )
        )

        if authorization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization not found"
            )

        # 2. Retrieve documents
        return self.document_reposetory.get_by_authorization(
            authorization_id=authorization_id,
            organization_id=organization_id
        )





'''
PDF file
   ↓
await file.read()
   ↓
file_bytes
(raw PDF bytes)
   ↓
BytesIO(file_bytes)
   ↓
makes the bytes behave like a file in memory
   ↓
PdfReader(...)
   ↓
understands/parses the PDF structure
   ↓
reader.pages
   ↓
page.extract_text()
   ↓
actual text

'''
