
import logging

from langchain_core.documents import Document

from app.models.policy import PolicyDocument
from app.rag.chunking import split_policy_pages
from app.rag.vector_store import get_semantic_vector_store
from app.repositories.policy_repository import PolicyRepository
from app.ai.gateway.provider_authorization import (
    validate_embedding_authorization,
)


logger = logging.getLogger(__name__)


class PolicyIngestionService:

    def __init__(
        self,
        policy_repository: PolicyRepository,
    ):
        self.policy_repository = policy_repository


    def index_policy_documents(
        self,
        *,
        organization_id: int,
        policy_version_id: int,
        document_id: int,
    ) -> int:

        # Step 1: Load the document.
        logger.info(
            "Step 1: Loading policy document. Document ID: %s",
            document_id,
        )

        document = self.policy_repository.get_document_for_ingestion(
            organization_id=organization_id,
            policy_version_id=policy_version_id,
            document_id=document_id,
        )

        if document is None:
            raise ValueError(
                "Policy document was not found for this organization."
            )

        if document.processing_status != "PROCESSED":
            raise ValueError(
                "The policy document must be processed before indexing."
            )

        # Step 2: Load extracted pages.
        pages = [
            {
                "page_number": page.page_number,
                "text": page.text,
            }
            for page in document.pages
        ]

        logger.info("Step 2: Loaded %s pages.", len(pages))

        # Step 3: Create chunks.
        chunks: list[Document] = split_policy_pages(
            pages,
            organization_id=organization_id,
            policy_version_id=policy_version_id,
            document_id=document_id,
        )

        if not chunks:
            raise ValueError(
                "No text was extracted from the policy document."
            )

        logger.info("Step 3: Created %s chunks.", len(chunks))

        # Step 4: Validate embedding authorization.
        for chunk in chunks:
            validate_embedding_authorization(
                {
                    "policy_document_text": chunk.page_content,
                }
            )

        logger.info("Step 4: Embedding authorization passed.")

        # Step 5: Mark document as INDEXING.
        self.policy_repository.update_document_indexing_status(
            organization_id=organization_id,
            policy_version_id=policy_version_id,
            document_id=document_id,
            indexing_status="INDEXING",
        )

        try:
            # Step 6: Initialize vector store.
            logger.info("Step 5: Initializing vector store.")

            vector_store = get_semantic_vector_store()

            logger.info("Step 5 completed.")

            # Step 7: Delete previous vectors.
            vector_store.delete(
                filter={
                    "organization_id": organization_id,
                    "document_id": document_id,
                }
            )

            logger.info("Step 6: Previous vectors deleted.")

            # Step 8: Generate unique chunk IDs.
            ids = [
                f"org-{organization_id}-doc-{document_id}-chunk-{index}"
                for index in range(len(chunks))
            ]

            # Step 9: Insert chunks and embeddings.
            logger.info(
                "Step 7: Inserting %s chunks.",
                len(chunks),
            )

            vector_store.add_documents(
                documents=chunks,
                ids=ids,
            )

            logger.info("Step 7 completed successfully.")

        except Exception:
            logger.exception(
                "Policy indexing failed for document_id=%s",
                document_id,
            )

            self.policy_repository.update_document_indexing_status(
                organization_id=organization_id,
                policy_version_id=policy_version_id,
                document_id=document_id,
                indexing_status="FAILED",
            )

            raise

        # Step 10: Mark indexing as successful.

        updated_document = (
            self.policy_repository.update_document_indexing_status(
                organization_id=organization_id,
                policy_version_id=policy_version_id,
                document_id=document_id,
                indexing_status="INDEXED",
            )
        )

        if updated_document is None:
            raise ValueError(
                "Document not found while updating indexing status."
            )

        logger.info(
            "Document status updated: ID=%s, status=%s",
            updated_document.id,
            updated_document.indexing_status,
        )
        return len(chunks)



"""
PostgreSQL: Policy tables

Policy 101 → Document 501 → 3 extracted pages

PolicyIngestionService

Validate → Load pages → Split into chunks → Generate embeddings → Save

POLICY_VECTOR_TABLE

Stores searchable chunks, embeddings and metadata

PolicySearchService

Retrieves relevant chunks for a reviewer's question
"""

# from langchain_core.documents import Document
# from app.models.policy import PolicyDocument
# from app.rag.chunking import split_policy_pages
# from app.rag.vector_store import get_semantic_vector_store
# from app.repositories.policy_repository import PolicyRepository
# from app.ai.gateway.provider_authorization import (
#     validate_embedding_authorization,
# )
# import logging

# logger = logging.getLogger(__name__)

# class PolicyIngestionService:
#     def __init__(self,
#                 policy_repository:PolicyRepository):
#         self.policy_repository=policy_repository

#     def index_policy_documents(
#             self,
#             *,
#             organization_id:int,
#             policy_version_id:int,
#             document_id:int,
#     )->int:
#         # 1. Load the document though the SQLALchemy repository.

#         document:PolicyDocument=self.policy_repository.get_document_for_ingestion(
#             organization_id=organization_id,
#             policy_version_id=policy_version_id,
#             document_id=document_id
#         )

#         if document is None:
#             raise ValueError(
#                 "Policy document was not found for thus organization"
#             )

#         if document.processing_status !="PROCESSED":
#             raise ValueError(
#                 "The policy documents must be processed before indexing"
#             )
#          # 2. Convert your SQLAlchemy page records to simple dictionaries.
#         pages=[
#             {
#                 "page_number":page.page_number,
#                 "text":page.text
#             }

#             for page in document.pages
#         ]

#         # 3. Chunk the extracted page text.
#         chunks:list[Document]=split_policy_pages(
#             pages,
#             organization_id=organization_id,
#             policy_version_id=policy_version_id,
#             document_id=document_id

#         )

#         if not chunks:
#             raise ValueError(
#                 "No text was extracted from the policy document."
#             )

#         for chunk in chunks:
#              validate_embedding_authorization(
#         {
#             "policy_document_text": chunk.page_content
#         }
#         )

#         # 4. Get the LangChain vector store.
#         vector_store=get_semantic_vector_store()

#         # 5. Remove the previous index for this document.
#         vector_store.delete(
#             filter={
#                 "organization_id":organization_id,
#                 "document_id":document_id
#             }

#         )
#         # 6. Generate embeddings and save the chunks.
#         ids=[
#             f"org-{organization_id}-doc-{document_id}-chunk-{index}"
#             for index in range(len(chunks))
#         ]

#         vector_store.add_documents(
#             documents=chunks,
#             ids=ids
#         )

#         return len(chunks)
