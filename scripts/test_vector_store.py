import asyncio
import sys

# Windows compatibility for Psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from langchain_core.documents import Document
from app.rag.vector_store import get_semantic_vector_store

store = get_semantic_vector_store()

test_document = Document(
    page_content=(
        "Prior authorization requires supporting clinical evidence."
    ),
    metadata={
        "organization_id": 999,
        "policy_version_id": 999,
        "document_id": 999,
        "page_number": 1,
        "chunk_index": 0,
        "source": "day13-test",
    },
)

store.add_documents(
    documents=[test_document],
    ids=["day13-test-document-999"],
)

results = store.similarity_search(
    "What evidence is required for prior authorization?",
    k=3,
    filter={
        "organization_id": 999,
        "policy_version_id": 999,
    },
)

for result in results:
    print(result.page_content)
    print(result.metadata)
