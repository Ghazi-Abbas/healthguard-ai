
import logging
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.cache.cache_keys import (
    policy_metadata_key,
    policy_search_prefix,
)
from app.cache.cache_service import CacheService
from app.core.config import settings
from app.models.policy import Policy, PolicyDocument, PolicyDocumentPage
from app.repositories.policy_repository import PolicyRepository
from app.services.policy_ingestion_service import PolicyIngestionService
from app.services.storage_service import S3StorageService


logger = logging.getLogger(__name__)


class PolicyService:

    def __init__(
        self,
        policy_repository: PolicyRepository,
        storage_service: S3StorageService,
        db: Session,
        cache: CacheService,
        policy_ingestion_service: PolicyIngestionService,
    ):
        self.policy_repository = policy_repository
        self.storage_service = storage_service
        self.db = db
        self.cache = cache
        self.policy_ingestion_service = policy_ingestion_service

    # =====================================
    # CREATE POLICY
    # =====================================

    def create_policy(
        self,
        name: str,
        version: str,
        description: str | None,
        organization_id: int,
    ):
        policy = Policy(
            organization_id=organization_id,
            name=name,
            version=version,
            description=description,
        )

        self.policy_repository.create_policy(
            policy=policy
        )

        self.db.commit()
        self.db.refresh(policy)

        return policy

    # =====================================
    # GET POLICY METADATA (REDIS CACHE)
    # =====================================

    def get_policy_metadata(
        self,
        policy_id: int,
        organization_id: int,
    ) -> dict:

        cache_key = policy_metadata_key(
            organization_id=organization_id,
            policy_id=policy_id,
        )

        # 1. Check Redis first.
        cached_policy = self.cache.get_json(cache_key)

        if cached_policy is not None:
            return cached_policy

        # 2. Cache miss: get policy from PostgreSQL.
        # The repository query must enforce tenant isolation.

        policy = (
            self.policy_repository.get_by_id_for_organization(
                policy_id=policy_id,
                organization_id=organization_id,
            )
        )

        if policy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )

        # 3. Cache only required metadata.
        result = {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
        }

        # 4. Store metadata for 120 seconds.
        self.cache.set_json(
            key=cache_key,
            value=result,
            ttl_seconds=120,
        )

        return result

    # =====================================
    # UPLOAD POLICY DOCUMENT
    # =====================================

    async def upload_policy_document(
        self,
        policy_id: int,
        file: UploadFile,
        organization_id: int,
    ):

        # ---------------------------------
        # 1. FIND POLICY IN SAME TENANT
        # ---------------------------------

        policy = (
            self.policy_repository.get_by_id_for_organization(
                policy_id=policy_id,
                organization_id=organization_id,
            )
        )

        if policy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )

        # ---------------------------------
        # 2. VALIDATE MIME TYPE
        # ---------------------------------

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed",
            )

        # ---------------------------------
        # 3. READ FILE
        # ---------------------------------

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        # ---------------------------------
        # 4. VALIDATE FILE SIZE
        # ---------------------------------

        max_size = (
            settings.MAX_FILE_SIZE_MB
            * 1024
            * 1024
        )

        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File size cannot exceed "
                    f"{settings.MAX_FILE_SIZE_MB} MB"
                ),
            )

        # ---------------------------------
        # 5. VALIDATE PDF SIGNATURE
        # ---------------------------------

        if not file_bytes.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file",
            )

        # ---------------------------------
        # 6. PREPARE FILENAME
        # ---------------------------------

        original_filename = file.filename or "policy.pdf"

        extension = Path(original_filename).suffix.lower()

        if extension != ".pdf":
            extension = ".pdf"

        unique_filename = f"{uuid4()}{extension}"

        # ---------------------------------
        # 7. CREATE S3 OBJECT KEY
        # ---------------------------------

        s3_key = (
            f"organization/{organization_id}/"
            f"policies/{policy_id}/"
            f"documents/{unique_filename}"
        )

        # ---------------------------------
        # 8. UPLOAD FILE TO S3
        # ---------------------------------

        self.storage_service.upload_file(
            file_bytes=file_bytes,
            object_key=s3_key,
            content_type="application/pdf",
        )

        # ---------------------------------
        # 9. CREATE DATABASE RECORD
        # ---------------------------------

        document = PolicyDocument(
            policy_id=policy_id,
            filename=original_filename,
            content_type="application/pdf",
            storage_path=s3_key,
            processing_status="PROCESSING",
            indexing_status="PENDING",
            page_count=0,
        )

        self.policy_repository.create_document(document)

        self.db.commit()
        self.db.refresh(document)

        document_id = document.id

        # ---------------------------------
        # 10. EXTRACT PDF AND SAVE ALL PAGES
        # ---------------------------------

        try:
            reader = PdfReader(BytesIO(file_bytes))

            page_count = len(reader.pages)

            if page_count == 0:
                raise ValueError("PDF contains no pages")

            for page_index, page in enumerate(
                reader.pages,
                start=1,
            ):

                page_text = page.extract_text() or " "

                document_page = PolicyDocumentPage(
                    document_id=document_id,
                    page_number=page_index,
                    text=page_text,
                )

                # Save every page inside the loop.
                self.policy_repository.create_page(
                    document_page
                )

            document.page_count = page_count
            document.processing_status = "PROCESSED"

            self.db.commit()
            self.db.refresh(document)

            logger.info(
                "Processed policy document %s: %s pages",
                document_id,
                page_count,
            )

        except Exception:

            self.db.rollback()

            failed_document = self.db.get(
                PolicyDocument,
                document_id,
            )

            if failed_document is not None:
                failed_document.processing_status = "FAILED"
                self.db.commit()

            logger.error(
                "Policy PDF processing failed for document %s",
                document_id,
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Policy PDF processing failed",
            ) from None

        # ---------------------------------
        # 11. START POLICY INGESTION
        # ---------------------------------

        try:
            document = self.db.get(
                PolicyDocument,
                document_id,
            )

            document.indexing_status = "INDEXING"

            self.db.commit()

            # Create chunks and store embeddings in the vector store.
            chunk_count = (
                self.policy_ingestion_service.index_policy_documents(
                    organization_id=organization_id,
                    policy_version_id=policy_id,
                    document_id=document_id,
                )
            )

            # ---------------------------------
            # 12. MARK INDEXING AS COMPLETED
            # ---------------------------------

            document = self.db.get(
                PolicyDocument,
                document_id,
            )

            document.indexing_status = "INDEXED"

            self.db.commit()
            self.db.refresh(document)

            logger.info(
                "Indexed policy document %s: %s chunks",
                document_id,
                chunk_count,
            )

            # ---------------------------------
            # 13. INVALIDATE POLICY SEARCH CACHE
            # ---------------------------------

            search_cache_prefix = policy_search_prefix(
                organization_id=organization_id,
                policy_version_id=policy_id,
            )

            cache_cleared = self.cache.delete_pattern(
                f"{search_cache_prefix}*"
            )

            if not cache_cleared:
                logger.warning(
                    "Could not invalidate policy search cache "
                    "for policy %s in organization %s",
                    policy_id,
                    organization_id,
                )

            return document

        except Exception:

            self.db.rollback()

            failed_document = self.db.get(
                PolicyDocument,
                document_id,
            )

            if failed_document is not None:
                failed_document.indexing_status = "FAILED"
                self.db.commit()

            logger.error(
                "Policy document ingestion failed for document %s",
                document_id,
            )

            return failed_document

    # =====================================
    # GET POLICY DOCUMENTS
    # =====================================

    def get_policy_documents(
        self,
        policy_id: int,
        organization_id: int,
    ):

        # Verify that the policy belongs to this organization.
        policy = (
            self.policy_repository.get_by_id_for_organization(
                policy_id=policy_id,
                organization_id=organization_id,
            )
        )

        if policy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found",
            )

        return (
            self.policy_repository.get_Documents(policy_id)
        )
