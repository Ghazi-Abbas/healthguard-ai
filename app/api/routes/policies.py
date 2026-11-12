from fastapi import APIRouter, Depends , status ,HTTPException
from app.api.dependencies import get_current_user ,get_policy_repository
from app.core.permission import Permission
from app.schemas.rag import(PolicyEvidence, PolicySearchRequest,PolicySearchResponse, )
from app.api.dependencies import require_permission ,get_policy_serch_service , get_policy_ingestion_service
from app.services.policy_search_service import PolicySearchService
from app.models.user import User
from app.services.policy_ingestion_service import PolicyIngestionService
from app.schemas.policy_rag import PolicyRAGResponse ,PolicyRAGRequest
from app.repositories.policy_repository import PolicyRepository
from app.api.dependencies import (
    require_permission,
    get_policy_repository,
    get_policy_ingestion_service,
    get_policy_retrieval_service,
)

from app.services.policy_retrieval_service import PolicyREtrievalService

router=APIRouter(prefix="/policies", tags=["Policies"])


@router.post(
      "/{policy_id}/documnet/{document_id}/ingest",
      status_code=status.HTTP_200_OK
)
def ingest_policy_document(
    policy_id:int,
    document_id:int,
    current_user:User=Depends(
        require_permission(Permission.INGEST_POLICY)
    ),
    service:PolicyIngestionService=Depends(
        get_policy_ingestion_service
    )
):
    try:
        chunk_count=service.index_policy_documents(
        organization_id=current_user.organization_id,
        policy_version_id=policy_id,
        document_id=document_id

    )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return{
        "message":"Policy document indexed successfully",
        "policy_id":policy_id,
        "document_id":document_id,
        "chunks_indexed":chunk_count

    }

@router.post(
    "/search",
    response_model=PolicySearchResponse,
)
def search_policies(
    request: PolicySearchRequest,
    current_user: User = Depends(
        require_permission(Permission.SEARCH_POLICY)
    ),
    service: PolicyREtrievalService = Depends(
        get_policy_retrieval_service
    ),
) -> PolicySearchResponse:

    documents = service.search(
        query=request.query,
        method=request.method,
        organization_id=current_user.organization_id,
        policy_version_id=request.policy_version_id,
        top_k=request.top_k,
    )

    results = [
        PolicyEvidence(
            text=document.page_content,
            policy_version_id=document.metadata["policy_version_id"],
            document_id=document.metadata["document_id"],
            page_number=document.metadata["page_number"],
            section=document.metadata.get("section"),
            source=document.metadata.get("source"),
        )
        for document in documents
    ]

    return PolicySearchResponse(
        query=request.query,
        method=request.method,
        results=results,
    )

@router.post(
    "/ask",
    response_model=PolicyRAGResponse
)

def ask_policy_question(
    request:PolicyRAGRequest,
    current_user:User=Depends(
        require_permission(Permission.SEARCH_POLICY)
    ),
    repository:PolicyRepository=Depends(get_policy_repository)
) -> PolicyRAGResponse:

    organization_id=current_user.organization_id

    active_version_ids=repository.get_active_policy_version_ids(
        organization_id=organization_id
    )

    # An explicitly requested version must be in the user's scope.

    if request.policy_version_id is not None:
        if request.policy_version_id not in active_version_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy version not found"

            )

        active_version_ids=[request.policy_version_id]
