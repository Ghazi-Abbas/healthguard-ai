from app.rag.constants import DEFAULT_TOP_K, MAX_TOP_K
from app.rag.vector_store import get_semantic_vector_store
from app.repositories.policy_repository import PolicyRepository
class PolicySearchService:
    def __init__(self,
                 policy_repository:PolicyRepository):
        self.policy_repository=policy_repository

    def search_active_policies(
            self,
            *,
            organization_id,
            query:str,
            top_k:int=DEFAULT_TOP_K,
    )->list[dict]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        top_k=max(1,min(top_k, MAX_TOP_K))

        #1. Resolve allowed active version from canonical SQL records

        active_version_ids=(
            self.policy_repository.get_active_policy_version_ids(
                organization_id=organization_id
            )
        )

        if not active_version_ids:
            return []

         # 2. Restrict vector retrieval to this organization's active versions.
        vector_filter={
            "$and":[
                {"organization_id":organization_id},
                {"policy_version_id":{"$in":active_version_ids}}
            ]

        }
        # 3. Retrieve matching LangChain Documents.
        vector_store=get_semantic_vector_store()

        documents=vector_store.similarity_search(
            query,
            k=top_k,
            filter=vector_filter
        )

        # 4- REturn text plus provenance.

        return[
            {
                "text":doc.page_content,
                "policy_version_id":doc.metadata.get("policy_version_id"),
                "document_id":doc.metadata.get("document_id"),
                "page_number":doc.metadata.get("page_number"),
                "section":doc.metadata.get("section"),
                "source":doc.metadata.get("source")
            }

            for doc in documents
        ]

# the retrieval service is more upto the mark use them
