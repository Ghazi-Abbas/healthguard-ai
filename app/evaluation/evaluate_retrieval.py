
import asyncio
import sys

# Psycopg async connections require SelectorEventLoop on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from langchain_core.documents import Document
from ranx import Qrels, Run, evaluate

from app.evaluation.datasets import EVALUATION_DATASET
from app.evaluation.retrieval_metrics import METRICS, TARGETS, TOP_K

from app.rag.retriever import (
    create_keyword_retriver,
    get_hybrid_retriever,
    get_semantic_retriever,
)

from app.rag.vector_store import get_semantic_vector_store


MAX_KEYWORD_DOCUMENTS = 5_000


def load_keyword_documents(metadata_filter: dict) -> list[Document]:
    """Load policy chunks for BM25 keyword retrieval."""

    stored = get_semantic_vector_store().get(
        where=metadata_filter,
        limit=MAX_KEYWORD_DOCUMENTS + 1,
        include=["documents", "metadatas"],
    )

    ids = stored.get("ids") or []
    texts = stored.get("documents") or []
    metadatas = stored.get("metadatas") or []

    if len(ids) > MAX_KEYWORD_DOCUMENTS:
        raise RuntimeError(
            "Keyword evaluation corpus exceeds the configured limit."
        )

    if not (len(ids) == len(texts) == len(metadatas)):
        raise RuntimeError(
            "Vector store returned inconsistent chunk data."
        )

    documents = []

    for chunk_id, text, metadata in zip(ids, texts, metadatas):
        if not text or not text.strip():
            continue

        documents.append(
            Document(
                id=chunk_id,
                page_content=text,
                metadata=metadata or {},
            )
        )

    return documents


def retrieve_documents(sample: dict, method: str) -> list[Document]:
    """Retrieve the top-k policy chunks."""

    metadata_filter = {
        "$and": [
            {"organization_id": sample["organization_id"]},
            {
                "policy_version_id": {
                    "$in": sample["policy_version_ids"]
                }
            },
        ]
    }

    if method == "semantic":
        retriever = get_semantic_retriever(
            top_k=TOP_K,
            metadata_filter=metadata_filter,
        )
        return retriever.invoke(sample["query"])

    if method == "hybrid":
        retriever = get_hybrid_retriever(
            top_k=TOP_K,
            metadata_filter=metadata_filter,
        )
        return retriever.invoke(sample["query"])

    if method == "keyword":
        documents = load_keyword_documents(metadata_filter)

        if not documents:
            return []

        retriever = create_keyword_retriver(
            documents,
            top_k=TOP_K,
        )
        return retriever.invoke(sample["query"])

    raise ValueError(f"Unsupported retrieval method: {method}")


def main():
    qrels = Qrels(
        {
            sample["query_id"]: sample["relevant_chunks"]
            for sample in EVALUATION_DATASET
        }
    )

    methods = ("semantic", "keyword", "hybrid")

    for method in methods:
        print(f"\n{'=' * 15} {method.upper()} {'=' * 15}")

        run_data = {}

        for sample in EVALUATION_DATASET:
            retrieved_documents = retrieve_documents(sample, method)

            print(f"\nQuery: {sample['query_id']}")
            print(f"Question: {sample['query']}")

            expected_ids = set(sample["relevant_chunks"])
            ranked_chunks = {}

            for rank, document in enumerate(
                retrieved_documents,
                start=1,
            ):
                chunk_id = document.id

                if not chunk_id:
                    raise ValueError(
                        f"{method} retrieval did not preserve the "
                        f"original chunk ID for query {sample['query_id']}."
                    )

                relevant = chunk_id in expected_ids

                print(
                    f"Rank {rank} | "
                    f"ID: {chunk_id} | "
                    f"Relevant: {relevant}"
                )

                # Higher score represents a higher ranking.
                ranked_chunks[chunk_id] = float(TOP_K - rank + 1)

            run_data[sample["query_id"]] = ranked_chunks

        scores = evaluate(
            qrels,
            Run(run_data),
            METRICS,
        )

        print(f"\n{method.upper()} METRICS")

        for metric, score in scores.items():
            target = TARGETS.get(metric)

            if target is None:
                print(f"{metric}: {score:.3f}")
            else:
                result = "PASS" if score >= target else "BELOW TARGET"

                print(
                    f"{metric}: {score:.3f} "
                    f"(target: {target:.2f}) - {result}"
                )


if __name__ == "__main__":
    main()


"""
=============== SEMANTIC ===============
recall@5: 0.944 (target: 0.90) - PASS
precision@5: 0.467
mrr@5: 0.889 (target: 0.80) - PASS
ndcg@5: 0.863

=============== KEYWORD ===============
recall@5: 0.472 (target: 0.90) - BELOW TARGET
precision@5: 0.233
mrr@5: 0.500 (target: 0.80) - BELOW TARGET
ndcg@5: 0.391

=============== HYBRID ===============
recall@5: 0.889 (target: 0.90) - BELOW TARGET
precision@5: 0.433
mrr@5: 0.889 (target: 0.80) - PASS
ndcg@5: 0.787
(.venv) PS D:\AI ENGENEERING\Fast-Api\healthguard-ai>
"""


""""
Query: q1
Question: What documents are required for a complete prior authorization request?
Rank 1 | ID: org-43-doc-1-chunk-6 | Relevant: True
Rank 2 | ID: org-43-doc-1-chunk-3 | Relevant: False
Rank 3 | ID: org-43-doc-1-chunk-2 | Relevant: False
Rank 4 | ID: org-43-doc-1-chunk-7 | Relevant: True
Rank 5 | ID: org-43-doc-1-chunk-0 | Relevant: False

Query: q2
Question: What clinical criteria must be evaluated for the requested imaging procedure?
Rank 1 | ID: org-43-doc-1-chunk-8 | Relevant: True
Rank 2 | ID: org-43-doc-1-chunk-7 | Relevant: False
Rank 3 | ID: org-43-doc-1-chunk-9 | Relevant: True
Rank 4 | ID: org-43-doc-1-chunk-3 | Relevant: False
Rank 5 | ID: org-43-doc-1-chunk-6 | Relevant: False

Query: q3
Question: What eligibility and coverage checks are required before authorization?
Rank 1 | ID: org-43-doc-1-chunk-12 | Relevant: True
Rank 2 | ID: org-43-doc-1-chunk-11 | Relevant: True
Rank 3 | ID: org-43-doc-1-chunk-3 | Relevant: False
Rank 4 | ID: org-43-doc-1-chunk-2 | Relevant: False
Rank 5 | ID: org-43-doc-1-chunk-13 | Relevant: False

Query: q4
Question: What information must be requested when a prior authorization submission is incomplete?
Rank 1 | ID: org-43-doc-1-chunk-16 | Relevant: False
Rank 2 | ID: org-43-doc-1-chunk-6 | Relevant: False
Rank 3 | ID: org-43-doc-1-chunk-13 | Relevant: True
Rank 4 | ID: org-43-doc-1-chunk-15 | Relevant: True
Rank 5 | ID: org-43-doc-1-chunk-14 | Relevant: True

Query: q5
Question: When must a case be escalated to a human reviewer?
Rank 1 | ID: org-43-doc-1-chunk-28 | Relevant: True
Rank 2 | ID: org-43-doc-1-chunk-27 | Relevant: True
Rank 3 | ID: org-43-doc-1-chunk-29 | Relevant: False
Rank 4 | ID: org-43-doc-1-chunk-19 | Relevant: False
Rank 5 | ID: org-43-doc-1-chunk-5 | Relevant: False

Query: q6
Question: What evidence citation and audit information must be recorded?
Rank 1 | ID: org-43-doc-1-chunk-24 | Relevant: True
Rank 2 | ID: org-43-doc-1-chunk-23 | Relevant: True
Rank 3 | ID: org-43-doc-1-chunk-25 | Relevant: True
Rank 4 | ID: org-43-doc-1-chunk-16 | Relevant: False
Rank 5 | ID: org-43-doc-1-chunk-36 | Relevant: False
"""
