from app.rag.keyword_retriever import get_keyword_retriever


documents = get_keyword_retriever(
    search_query="medical necessity clinical documentation",
    organization_id=43,
    active_policy_version_ids=[1],  # Replace with an ID from Step 1
    top_k=6,
)

print(f"Retrieved documents: {len(documents)}")

for document in documents:
    print("\n-------------------------")
    print("Content:", document.page_content[:300])
    print("Metadata:", document.metadata)
