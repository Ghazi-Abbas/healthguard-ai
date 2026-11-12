
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import (
    get_member_coverage_service,
    require_permission,
)

from app.core.permission import Permission
from app.models.user import User

from app.schemas.member_coverage import (
    MemberCoverageCreate,
    MemberCoverageResponse,
)

from app.services.member_coverage_service import MemberCoverageService


router = APIRouter(
    prefix="/member-coverage",
    tags=["Member Coverage"],
)


# =========================================================
# CREATE MEMBER COVERAGE
# =========================================================

@router.post(
    "",
    response_model=MemberCoverageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member_coverage(
    payload: MemberCoverageCreate,
    current_user: User = Depends(
        require_permission(Permission.CREATE_MEMBER_COVERAGE)
    ),
    service: MemberCoverageService = Depends(
        get_member_coverage_service
    ),
):

    try:
        return service.create_coverage(
            payload=payload,
            organization_id=current_user.organization_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create member coverage.",
        ) from exc


# =========================================================
# GET MEMBER COVERAGES BY MEMBER ID
# Uses internal member ID
# =========================================================

@router.get(
    "/by-member/{member_id}",
    response_model=list[MemberCoverageResponse],
    status_code=status.HTTP_200_OK,
)
def get_member_coverages(
    member_id: int,
    current_user: User = Depends(
        require_permission(Permission.VIEW_MEMBERS_COVERAGE)
    ),
    service: MemberCoverageService = Depends(
        get_member_coverage_service
    ),
):

    try:
        return service.get_member_coverages(
            member_id=member_id,
            organization_id=current_user.organization_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# =========================================================
# GET MEMBER COVERAGE BY COVERAGE ID
# =========================================================

@router.get(
    "/{coverage_id}",
    response_model=MemberCoverageResponse,
    status_code=status.HTTP_200_OK,
)
def get_member_coverage(
    coverage_id: int,
    current_user: User = Depends(
        require_permission(Permission.VIEW_MEMBERS_COVERAGE)
    ),
    service: MemberCoverageService = Depends(
        get_member_coverage_service
    ),
):

    coverage = service.get_coverage(
        coverage_id=coverage_id,
        organization_id=current_user.organization_id,
    )

    if coverage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member coverage not found.",
        )

    return coverage
