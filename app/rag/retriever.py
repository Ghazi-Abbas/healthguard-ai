from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.rag.vector_store import(
    get_semantic_vector_store,
    get_hybrid_vector_store
)

def get_semantic_retriever(
        *,
        top_k,
        metadata_filter:dict,
)-> BaseRetriever:
    return get_semantic_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={
            "k":top_k,
            "filter":metadata_filter
        }
    )

def get_hybrid_retriever(
        *,
        top_k:int,
        metadata_filter:dict,
)-> BaseRetriever:
    return get_hybrid_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={
            "k":top_k,
            "filter":metadata_filter
        }
    )


# Unlike your vector retrievers, this function does not fetch documents from pgvector.

"""
This creates a BM25 retriever using the supplied documents.

BM25 calculates how useful query terms are for identifying relevant documents.
Its ranking considers factors such as term frequency, how rare a term is across the
corpus, and document length.

CPT and ICD codes.
Policy identifiers.
Medication names.
Exact clinical terminology.
Specific procedure names.
BM25 retriever = Find the supplied documents that best match the important words in the query.
"""
def create_keyword_retriver(
        documents:list[Document],
        *,
        top_k:int,
)->BM25Retriever:
    return BM25Retriever.from_documents(
        documents=documents,
        k=top_k
    )
