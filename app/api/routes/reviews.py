
from fastapi import APIRouter, Depends, status

from app.models.user import User
from app.api.dependencies import (
    require_permission,
    get_review_service
)
from app.core.permission import Permission
from app.services.review_service import ReviewService
from app.schemas.review import RequestINformationRequest


router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["Reviews"]
)


# ==========================================================
# VIEW REVIEW QUEUE
# ==========================================================
@router.get(
    "/",
    status_code=status.HTTP_200_OK
)
def get_review_queue(
    current_user: User = Depends(
        require_permission(Permission.VIEW_QUEUE)
    ),
    service: ReviewService = Depends(get_review_service)
):
    return service.get_review_queue(
        current_user.organization_id
    )


# ==========================================================
# OPEN / REVIEW CASE
# ==========================================================
@router.get(
    "/{authorization_id}",
    status_code=status.HTTP_200_OK
)
def review_case(
    authorization_id: int,
    current_user: User = Depends(
        require_permission(Permission.REVIEW_CASE)
    ),
    service: ReviewService = Depends(get_review_service)
):
    return service.get_case(
        current_user.organization_id,
        authorization_id
    )


# ==========================================================
# APPROVE
# ==========================================================
@router.post(
    "/{authorization_id}/approve",
    status_code=status.HTTP_200_OK
)
def approved_authorization(
    authorization_id: int,
    current_user: User = Depends(
        require_permission(Permission.APPROVE)
    ),
    service: ReviewService = Depends(get_review_service)
):
    return service.approve(
        authorization_id=authorization_id,
        organization_id=current_user.organization_id,
        reviewer_id=current_user.id
    )


# ==========================================================
# REJECT
# ==========================================================
@router.post(
    "/{authorization_id}/reject",
    status_code=status.HTTP_200_OK
)
def reject_authorization(
    authorization_id: int,
    current_user: User = Depends(
        require_permission(Permission.REJECT)
    ),
    service: ReviewService = Depends(get_review_service)
):
    return service.reject(
        authorization_id=authorization_id,
        organization_id=current_user.organization_id,
        reviewer_id=current_user.id
    )


# ==========================================================
# REQUEST ADDITIONAL INFORMATION
# ==========================================================
@router.post(
    "/{authorization_id}/request-information",
    status_code=status.HTTP_200_OK
)
def request_information(
    authorization_id: int,
    request: RequestINformationRequest,
    current_user: User = Depends(
        require_permission(Permission.REQUEST_INFORMATION)
    ),
    service: ReviewService = Depends(get_review_service)
):
    return service.request_information(
        authorization_id=authorization_id,
        organization_id=current_user.organization_id,
        reviewer_id=current_user.id,
        message=request.message
    )
