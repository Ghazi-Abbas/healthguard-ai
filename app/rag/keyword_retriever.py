


from app.db.session import sessionlocal


import re

from sqlalchemy import text
from langchain_core.documents import Document


def get_keyword_retriever(
    *,
    search_query: str,
    organization_id: int,
    active_policy_version_ids: list[int],
    top_k: int = 6,
) -> list[Document]:

    """
    Retrieve policy chunks using local PostgreSQL
    full-text keyword search.

    No external LLM or embedding provider is used.
    """

    if not search_query or not search_query.strip():
        raise ValueError("Search query cannot be empty.")

    if not active_policy_version_ids:
        return []

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or not 1 <= top_k <= 20
    ):
        raise ValueError("top_k must be between 1 and 20.")

    # Remove generic words that do not help policy retrieval.
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "what",
        "when",
        "where",
        "which",
        "determine",
        "applicable",
        "procedure",
        "diagnosis",
        "criteria",
        "requirements",
        "policy",
        "search",
    }

    # Extract meaningful alphabetic terms locally.
    words = re.findall(
        r"[a-zA-Z]{3,}",
        search_query.lower(),
    )

    search_terms = list(dict.fromkeys(
        word
        for word in words
        if word not in stop_words
    ))

    if not search_terms:
        return []

    # Build a safe OR-based PostgreSQL query.
    # Tokens contain only alphabetic characters.
    ts_query = " | ".join(search_terms)

    sql = text("""
        SELECT
            langchain_id,
            content,
            organization_id,
            policy_version_id,
            document_id,
            page_number,
            chunk_index,
            section,
            source,

            ts_rank_cd(
                to_tsvector('english', content),
                to_tsquery('english', :ts_query)
            ) AS relevance_score

        FROM policy_vector_chunks

        WHERE
            organization_id = :organization_id

            AND policy_version_id = ANY(
                CAST(:active_policy_version_ids AS integer[])
            )

            AND to_tsvector('english', content)
                @@ to_tsquery('english', :ts_query)

        ORDER BY
            relevance_score DESC,
            page_number ASC,
            chunk_index ASC

        LIMIT :top_k
    """)

    with sessionlocal() as session:

        results = session.execute(
            sql,
            {
                "ts_query": ts_query,
                "organization_id": organization_id,
                "active_policy_version_ids": active_policy_version_ids,
                "top_k": top_k,
            },
        ).mappings().all()

    documents = []

    for row in results:

        documents.append(
            Document(
                page_content=row["content"],
                metadata={
                    "evidence_id": row["langchain_id"],
                    "organization_id": row["organization_id"],
                    "policy_version_id": row["policy_version_id"],
                    "document_id": row["document_id"],
                    "page_number": row["page_number"],
                    "chunk_index": row["chunk_index"],
                    "section": row["section"],
                    "source": row["source"],
                    "relevance_score": float(
                        row["relevance_score"]
                    ),
                },
            )
        )

    return documents
