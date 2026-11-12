from fastapi import APIRouter ,status,Depends, UploadFile, File
from app.schemas.user import UserResponse ,CreateUserRequest,ChangeRoleRequest
from app.schemas.policy import  PolicyResponse
from app.api.dependencies import get_user_service, require_permission, get_policy_service
from app.services.user_service import UserService
from app.models.user import User
from app.core.permission import Permission
from app.services.policy_service import PolicyService
from app.schemas.policy import PolicyDocumentResponse
from app.schemas.policy import PolicyCreater

router=APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)

# ==========================================================
# CREATE USER
# ==========================================================

@router.post(
    "/create-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    request:CreateUserRequest,
    user_service:UserService=Depends(
        get_user_service
    ),
    current_user:User=Depends(
        require_permission(
            Permission.MANAGE_USERS
        )
)):
    return user_service.create_user(
        request,
        current_user.organization_id
    )

# ==========================================================
# GET USERS OF MY ORGANIZATION
# ==========================================================

@router.get(
    "/users",
    response_model=list[UserResponse]
)
def get_users(
    user_service:UserService=Depends(get_user_service),
    current_user:User=Depends(require_permission(
        Permission.MANAGE_USERS
    ))
):
    return user_service.get_organization_users(current_user.organization_id)

# ==========================================================
# CHANGE USER ROLE
# ==========================================================
@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse
)
def change_user_role(
    user_id:int,
    request:ChangeRoleRequest,
    current_user:User=Depends(
        require_permission(
            Permission.MANAGE_ROLES
        )
    ),
    user_service:UserService=Depends(
        get_user_service
    )

):
    return user_service.change_role(user_id,current_user.organization_id,request)
# ==========================================================
# DEACTIVATE USER
# ==========================================================
@router.patch(
    "/users/{user_id}/deactive",
    response_model=UserResponse
)
def deactive_user(
    user_id:int,
    user_service:UserService=Depends(
        get_user_service
    ),
    current_user:User=Depends(
        require_permission(Permission.MANAGE_USERS)
    )
):
    return user_service.deactivate_user(
        user_id,
        current_user.organization_id

    )
# =====================================
# CREATE POLICY
# =====================================

@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_policy(
    request:PolicyCreater,
    current_user:User=Depends(
        require_permission(
            Permission.MANAGE_POLICIES
        )
    ),
    service:PolicyService=Depends(
        get_policy_service
    )
):
    return service.create_policy(
        name=request.name,
        version=request.version,
        description=request.description,
        organization_id=current_user.organization_id
    )

# =====================================
# UPLOAD POLICY DOCUMENT
# =====================================
@router.post(
    "/policies/{policy_id}/document",
    response_model=PolicyDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_policy_document(
    policy_id:int,
    file:UploadFile=File(...),
    current_user:User=Depends(
        require_permission(
            Permission.MANAGE_POLICIES
        )
    ),
    service: PolicyService = Depends(get_policy_service)
):
    return await service.upload_policy_document(
        policy_id=policy_id,
        file=file,
        organization_id=current_user.organization_id
    )

# =====================================
# GET POLICY DOCUMENTS
# =====================================

@router.get(
    "/policies/{policy_id}/documents",
    response_model=list[PolicyDocumentResponse]
)
def get_policy_documents(
    policy_id:int,
    current_user:User=Depends(
        require_permission(
            Permission.MANAGE_POLICIES
        )
    ),
    service:PolicyService=Depends(
        get_policy_service
    )
):
    return service.get_policy_documents(
        policy_id=policy_id,
        organization_id=current_user.organization_id
    )
