from langchain_core.documents import Document
from ranx import Qrels, Run, evaluate

from app.evaluation.datasets import EVALUATION_DATASET

from app.evaluation.retrieval_metrics import (
    MATRICS,
    TARGETS,
    TOP_K
)


from app.rag.retriever import(
    create_keyword_retriver,
    get_hybrid_retriever,
    get_semantic_retriever
)

from app.rag.vector_store import get_semantic_vector_store

MAX_KEYWORD_DOCUMENTS=5_000

# ranx expects:
# query_id -> chunk_id -> relevance grade

qrels=Qrels(
    {
        sample["query_id"]:sample["relevant_chunks"]
        for sample in EVALUATION_DATASET
    }
)

for method in ("semantic", "keyword", "hybrid"):
    run_data={}

    for sample in EVALUATION_DATASET:

        metadata_filter = {
            "$and": [
                {
                    "organization_id":
                        sample["organization_id"]
                },
                {
                    "policy_version_id": {
                        "$in": sample["policy_version_ids"]
                    }
                },
            ]
        }

        if method== "semantic":
            retrive=get_semantic_retriever(
                top_k=TOP_K,
                metadata_filter=metadata_filter
            )

            retrive_document=retrive.invoke(
                sample["query"]
            )

        elif method == "hybrid":
            retriever = get_hybrid_retriever(
                top_k=TOP_K,
                metadata_filter=metadata_filter,
            )

            retrieved_documents = retriever.invoke(
                sample["query"]
            )
        else:
            # Load stored chunks for the same tenant and
            # policy versions through the LangChain vector-store API.
            stored = get_semantic_vector_store().get(
                where=metadata_filter,
                limit=MAX_KEYWORD_DOCUMENTS,
                include=["documents", "metadatas"],
            )

            if len(stored["ids"]) >= MAX_KEYWORD_DOCUMENTS:
                raise RuntimeError(
                    "The keyword evaluation corpus reached its "
                    "limit. Use a smaller evaluation corpus or "
                    "a properly managed lexical-search backend."
                )

            # Re-create LangChain Documents, preserving their IDs
            # so the answer key can be matched to retrieved results.
            keyword_documents = [
                Document(
                    id=chunk_id,
                    page_content=text,
                    metadata=metadata or {},
                )
                for chunk_id, text, metadata in zip(
                    stored["ids"],
                    stored["documents"],
                    stored["metadatas"],
                )
                if text and text.strip()
            ]

            if not keyword_documents:
                retrieved_documents = []
            else:
                retriever = create_keyword_retriver(
                    keyword_documents,
                    top_k=TOP_K,
                )

                retrieved_documents = retriever.invoke(
                    sample["query"]
                )

        # Convert the ordered LangChain results to ranx's Run format.
        # These scores only preserve the retriever's result order.
        ranked_chunks = {}

        for rank, document in enumerate(
            retrieved_documents,
            start=1,
        ):
            if not document.id:
                raise ValueError(
                    "A retrieved Document has no ID. Ensure that "
                    "Day 13 preserves each vector-store chunk ID "
                    "as Document.id."
                )

            ranked_chunks[document.id] = float(
                TOP_K - rank + 1
            )

        run_data[sample["query_id"]] = ranked_chunks

    # ranx performs the actual metric calculations.
    scores = evaluate(
        qrels,
        Run(run_data),
        MATRICS
    )

    print(f"\n{'=' * 12} {method.upper()} {'=' * 12}")

    for metric, score in scores.items():
        target = TARGETS.get(metric)

        if target is None:
            print(f"{metric}: {score:.3f}")
        else:
            status = "PASS" if score >= target else "BELOW TARGET"

            print(
                f"{metric}: {score:.3f} "
                f"(target: {target:.2f}) — {status}"
            )
"""
Recall@5 measures how many of the known relevant chunks were retrieved in the top five results.
Precision@5 measures the proportion of retrieved chunks that were relevant. MRR@5 measures how early the
first relevant chunk appeared, while NDCG@5 evaluates the overall ranking quality.
"""
