from fastapi import HTTPException , status
from langchain_core.documents import Document
from app.repositories.policy_repository import PolicyRepository

from app.rag.constants import DEFAULT_TOP_K, MAX_TOP_K
from app.rag.retriever import(
    create_keyword_retriver,
    get_hybrid_retriever,
    get_semantic_retriever
)
from app.rag.vector_store import get_semantic_vector_store

MAX_BM25_CORPUS=10_000

class PolicyREtrievalService:
    def __init__(self, policy_repository:PolicyRepository):
        self.policy_repository=policy_repository
    def _resolve_scope(
            self,
            *,
            organization_id:int,
            policy_version_id:int |None
    )->tuple[list[int], dict]:
        active_version_ids=(
            self.policy_repository.get_active_policy_version_ids(
                organization_id=organization_id
            )
        )
        if policy_version_id is not None:
            if policy_version_id not in active_version_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Policy version not found",

                )

            active_version_ids=[policy_version_id]

        if not active_version_ids:
            return [], {}

        metadata_filter={
            "$and":[
                {
                "organization_id":organization_id
            },
            {
                "policy_version_id":{
                    "$in":active_version_ids
                },
            }
        ]
        }

        return active_version_ids, metadata_filter

    def _load_keyword_documents(
            self,
            *,
            metadata_filter:dict,
    )-> list[Document]:
        # Use the LangChain vector-store retrieval API to
        # load stored text and metadata, not hand-written SQL.
        stored=get_semantic_vector_store().get(
            where=metadata_filter,
            limit=MAX_BM25_CORPUS,
            include=["documents", "metadatas"]
        )

        texts=stored.get("documents") or []
        metadatas=stored.get("metadatas") or []

        documents:list[Document]=[]

        for index, text in enumerate(texts):
            if not text or not text.strip():
                continue

            metadata=(
                metadatas[index]
                if index <len(metadatas) and metadatas[index]
                else{}
            )

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata
                )
            )

        if len(text)> MAX_BM25_CORPUS:
            raise HTTPException(
                status_code= status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "The policy corpus is too large for the "
                    "Day 14 in-memory BM25 comparison. Use the "
                    "persistent hybrid retriever or build a "
                    "properly managed lexical-search index."
                )

            )

        return documents

    def search(
            self,
            *,
            query:str,
            method:str,
            organization_id:int,
            policy_version_id:int |None=None,
            top_k:int=DEFAULT_TOP_K,
    )->list[Document]:
        top_k=max(1, min(top_k, MAX_TOP_K))

        active_version_ids, metadata_filter=self._resolve_scope(
            organization_id=organization_id,
            policy_version_id=policy_version_id
        )

        if not active_version_ids:
            return []

        if method =="semantic":
            retriver = get_semantic_retriever(
                top_k=top_k,
                metadata_filter=metadata_filter
            )

            return retriver.invoke(query)

        if method =="hybrid":
            retriver=get_hybrid_retriever(
                top_k=top_k,
                metadata_filter=metadata_filter
            )

            return retriver.invoke(query)

        if method == "keyword":
            documents= self._load_keyword_documents(
                metadata_filter=metadata_filter
            )

            if not documents:
                return []

            retriver= create_keyword_retriver(
                documents,
                top_k=top_k
            )

            return retriver.invoke(query)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported retrieval method"
        )
