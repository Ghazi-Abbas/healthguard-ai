from fastapi import (APIRouter,
                     status,
                     HTTPException,
                    Response,
                    UploadFile,
                    File,
                    Depends)
from app.schemas.authorization import (AuthorizationCreate,
                                        AuthorizationResponse,
                                        AuthorizationUpdate,
                                        AuthorisationPatch)
from app.services.document_service import DocumentService
from app.schemas.authorization_workflow import AuthorizationWorkflowResponse
from app.schemas.document import DocumentResponse
# from uuid import uuid4
from app.services.authorization_service import AuthorizationService
from app.api.dependencies import get_authorization_service, require_permission,get_document_service
from app.models.user import User
from app.core.permission import Permission


router=APIRouter(
    prefix="/api/v1/authorizations",
    tags=["Authorizations"]
)


#=====================================================
#CREATE AUTHERIZATION
#=====================================================

@router.post("/",
            status_code=status.HTTP_201_CREATED,
            response_model=AuthorizationResponse)
def create_authorization(request:AuthorizationCreate,
                         service:AuthorizationService=Depends(get_authorization_service),
                         current_user:User=Depends(require_permission(Permission.CREATE_AUTHORIZATION))
                        ):

    return service.create(
         request,
         current_user.id,
         current_user.organization_id
         )

#=====================================================
#GET MY AUTHORIZATIONS
#=====================================================
@router.get("/my",
            status_code=status.HTTP_200_OK,
            response_model=list[AuthorizationResponse],
            )
def get_my_authorizations(
     current_user:User=Depends(require_permission(Permission.VIEW_OWN_AUTHORIZATION)),
     service:AuthorizationService=Depends(get_authorization_service)
):
     return service.get_my_authorizations(
          current_user.id,
          current_user.organization_id
     )
#=====================================================
#GET ONE AUTHORIZATION
#=====================================================
@router.get(
          "/{authorization_id}",
          status_code=status.HTTP_200_OK,
          response_model=AuthorizationResponse
)
def get_my_authorization(
     authorization_id:int,
     current_user:User=Depends(
          require_permission(Permission.VIEW_OWN_AUTHORIZATION)),
          service:AuthorizationService=Depends(get_authorization_service)
):
     return service.get_my_authorization(
          authorization_id,
          current_user.id,
          current_user.organization_id
     )
#=====================================================
#PATCH OWN AUTHORIZATION
#=====================================================
@router.patch(
          "/{authorization_id}",
          status_code=status.HTTP_200_OK,
          response_model=AuthorizationResponse
)
def update_authorization(
     authorization_id:int,
     request:AuthorisationPatch,
     service:AuthorizationService=Depends(get_authorization_service),
     current_user:User=Depends(require_permission(Permission.CREATE_AUTHORIZATION))
):
     return service.update_authorization(
          authorization_id,
          request,
          current_user.id,
          current_user.organization_id
     )

#=====================================================
#SUBMIT AUTHORIZATION AND START WORKFLOW
#=====================================================

@router.post(
          "/{authorization_id}/submit",
          status_code=status.HTTP_200_OK,
          response_model=AuthorizationWorkflowResponse
)
def submit_authorization(
     authorization_id:int,
     current_user:User=Depends(require_permission(Permission.CREATE_AUTHORIZATION)),
     service:AuthorizationService=Depends(get_authorization_service)
):
     return service.start_authorization_workflow(
            authorization_id,
            current_user.id,
            current_user.organization_id
     )

#
#=====================================================
#UPLOAD DOCUMENTS
#=====================================================
@router.post(
     "/{authorization_id}/documents",
     response_model=DocumentResponse,
     status_code=status.HTTP_201_CREATED,
)
async def upload_document(
     authorization_id:int,
     file:UploadFile=File(...),
     current_user:User=Depends(
          require_permission(
               Permission.UPLOAD_DOCUMENT
          )
     ),

     service:DocumentService=Depends(get_document_service)

):
     return await service.upload_document(
          authorization_id=authorization_id,
          file=file,
          user_id=current_user.id,
          organization_id=current_user.organization_id,

     )

#=====================================================
#VIEW OWN AUTHORIZATION
#=====================================================
@router.get("/{authorization_id}/documents",
            response_model=list[DocumentResponse],
            status_code=status.HTTP_200_OK)
def get_documents(
     authorization_id:int,
     current_user:User=Depends(
          require_permission(
               Permission.VIEW_OWN_AUTHORIZATION
          )
     ),
     service:DocumentService=Depends(get_document_service)
):
     return service.get_document(
          authorization_id=authorization_id,
          user_id=current_user.id,
          organization_id=current_user.organization_id

     )




# #=====================================================
# #Get all Autherization
# #=====================================================

# @router.get("/",
#             status_code=status.HTTP_200_OK,
#             )
# def get_autharization(
#     service:AuthorizationService=Depends(
#         get_authorization_service
#     )
# ):
#     return service.get_all()
#=====================================================
#Get Autherization BY ID
#=====================================================

# @router.get("/{authorization_id}",
#             status_code=status.HTTP_200_OK)
# def get_by_id(authorization_id:str,
#     service:AuthorizationService=Depends(get_authorization_service)):

#     return service.get_by_id(authorization_id)


#=====================================================
#GET ORGANIZATION AUTHERIZATION
#=====================================================

# @router.get("/organizations/{organization_id}/authorizations")
# def get_organisation_authorization(
#     organization_id: int,
#     page: int = 1,
#     page_size: int = 20,
#     status: str | None = None,
#     sort: str = "created_at",
#     order: str = "desc",
#     service: AuthorizationService = Depends(
#         get_authorization_service
#     )

# ):
#         return service.get_organization_authorizations(
#         organization_id=organization_id,
#         page=page,
#         page_size=page_size,
#         status=status,
#         sort=sort,
#         order=order
#     )
# #=====================================================
# # PARTIALY_UPDATE AUTHERIZATION
# #=====================================================
# @router.patch("/{authorization_id}",
#             status_code=status.HTTP_200_OK,
#             response_model=AuthorizationResponse)
# def patch_authorization(authorization_id:str,request:AuthorisationPatch,service:AuthorizationService=Depends(
#     get_authorization_service
# )):

#     return service.patch(
#         authorization_id
#         ,request)

#=====================================================
# #UPDATE AUTHERIZATION
# #=====================================================

# @router.put("/{authorization_id)}",
#             status_code=status.HTTP_200_OK,
#             response_model=AuthorizationResponse)
# def update_authorization(authorization_id:str,request:AuthorizationUpdate,service:AuthorizationService=Depends(
#     get_authorization_service
# )):

#     return service.update(
#         authorization_id
#         ,request)
