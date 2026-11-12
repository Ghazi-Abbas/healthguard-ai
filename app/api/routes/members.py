from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.core.permission import Permission
from app.api.dependencies import require_permission ,get_member_service
from app.models.user import User
from app.schemas.member import MemberCreate, MemberResponse
from app.services.member_service import MemberService


router = APIRouter(
    prefix="/members",
    tags=["Members"],
)


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    payload: MemberCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_MEMBER)),
    service: MemberService = Depends(get_member_service),
):
    try:
        return service.create_member(
            payload=payload,
            organization_id=current_user.organization_id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create member.",
        ) from exc

#=========================================================
# GET THE LIST OF TEH MEMBERS BY ORGANIZATION_ID
#=========================================================
@router.get(
    "",
    response_model=list[MemberResponse],
)
def list_members(
    current_user: User = Depends(require_permission(Permission.VIEW_MEMBERS)
    ),
    service: MemberService = Depends(get_member_service),
):
    return service.list_members(
        organization_id=current_user.organization_id,
    )

#=========================================================
# GET THE LIST OF TEH MEMBER BY MEMBER ID
#=========================================================
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
)
def get_member(
    member_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_MEMBERS)
    ),
    service: MemberService = Depends(get_member_service),
):
    member = service.get_member(
        member_id=member_id,
        organization_id=current_user.organization_id,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )

    return member
