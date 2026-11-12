from functools import lru_cache
from langchain_postgres import PGEngine , PGVectorStore
from langchain_postgres.v2.hybrid_search_config import (
    HybridSearchConfig,
    reciprocal_rank_fusion
)

from app.core.config import settings
# Reciprocal Rank Fusion (RRF)

# Combines the rankings from the two searches


from app.rag.constants import POLICY_VECTOR_TABLE
from app.rag.embeddings import get_embidding_service

@lru_cache(maxsize=1)
def get_pg_engine()->PGEngine:
    return PGEngine.from_connection_string(
        url=settings.DATABASE_URL
    )

@lru_cache(maxsize=1)
def get_semantic_vector_store() -> PGVectorStore:
    return PGVectorStore.create_sync(
        engine=get_pg_engine(),
        table_name=POLICY_VECTOR_TABLE,
        embedding_service=get_embidding_service(),
        content_column="content",
        embedding_column="embedding",
        id_column="langchain_id",
        metadata_columns=[
            "organization_id",
            "policy_version_id",
            "document_id",
            "page_number",
            "chunk_index",
            "section",
            "source",
        ],
    )

@lru_cache(maxsize=1)
def get_hybrid_vector_store()->PGVectorStore:
    hybrid_config=HybridSearchConfig(
    fusion_function=reciprocal_rank_fusion,
    fusion_function_parameters={
        "rrf_k": 10,
    },
    primary_top_k=10,
    secondary_top_k=10,
)


    return PGVectorStore.create_sync(

        engine=get_pg_engine(),
        table_name=POLICY_VECTOR_TABLE,
        embedding_service=get_embidding_service(),
        content_column="content",
        embedding_column="embedding",
        id_column="langchain_id",
        metadata_columns=[
            "organization_id",
            "policy_version_id",
            "document_id",
            "page_number",
            "chunk_index",
            "section",
            "source",
        ],
        hybrid_search_config=hybrid_config
    )


"""
One important detail: Both functions return a PGVectorStore, so either can be used to add documents. However, HybridSearchConfig configures hybrid-search behavior;
it does not itself guarantee that every search call uses hybrid retrieval. You must invoke the appropriate hybrid-search method.

For HealthGuard AI, your architecture can be:
- Ingestion: split policy PDFs and store chunks once.
- Retrieval: choose semantic search or hybrid search depending on the use case.
"""
