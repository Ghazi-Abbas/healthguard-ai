from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.constants import CHUNK_OVERLAP, CHUNK_SIZE

def get_policy_text_splitter()->RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,

    )

def split_policy_pages(
        pages:list[dict],
        # The * makes all parameters after it keyword-only. That means you must pass their names explicitly.
        # eg organization_id=10,like this
        *,
        organization_id:int,
        policy_version_id:int,
        document_id:int,
)->list[Document] :
    """
    Convert extracted PDF pages into langchain Documents.
    Expected pafe format:
    {
    "page_number:1,
    "text": "policy text"
    }
    """
    splitter=get_policy_text_splitter()

    chunks:list[Document]=[]

    for page in pages:
        page_number=page["page_number"]
        page_text=page["text"].strip()

        if not page_text:
            continue

        page_document=Document(
            page_content=page_text,
            metadata={
                "organization_id":organization_id,
                "policy_version_id":policy_version_id,
                "document_id":document_id,
                "page_number":page_number
            }
        )

        page_chunks=splitter.split_documents([page_document])

        for chunk_index, chunk in enumerate(page_chunks):
            chunk.metadata["chunk_index"]=chunk_index
            chunk.metadata["source"]=(
                f"policy_document:{document_id}:page:{page_number}"
            )
            chunks.append(chunk)

    return chunks


"""
Remember the three nested levels:
1. The outer loop processes each PDF page.
2. The inner loop processes each chunk within that page.
3. chunks.append(chunk) collects every chunk into one final list.
"""
