from app.rag.embeddings import get_embidding_service
from app.rag.constants import EMBIDDING_DIMENSION

embeddings = get_embidding_service()

document_vectors = embeddings.embed_documents(
    ["A policy requires clinical documentation for authorization."]
)

query_vector = embeddings.embed_query(
    "What clinical documents are required?"
)

print("Document vector dimensions:", len(document_vectors[0]))
print("Query vector dimensions:", len(query_vector))

assert len(document_vectors[0]) == EMBIDDING_DIMENSION
assert len(query_vector) == EMBIDDING_DIMENSION
