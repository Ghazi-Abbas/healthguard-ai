from fastapi import Request
from app.repositories.autharization_repository import(
    AuthorizationRepository
)
from app.repositories.authorization_review_repository import AuthorizationReviewRepository
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import S3StorageService
from app.cache.cache_service import CacheService
from app.cache.redis_client import get_redis_client
from redis import Redis
from app.repositories.policy_repository import PolicyRepository
from app.services.policy_service import PolicyService
from app.services.policy_ingestion_service import PolicyIngestionService
from app.services.policy_retrieval_service import PolicyREtrievalService
from app.services.authorization_service import(
    AuthorizationService
)
from app.repositories.authorization_workflow_repository import (
    AuthorizationWorkflowRepository
)
from app.repositories.document_repository import DocumentRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.review_service import ReviewService
from app.services.document_service import DocumentService
from app.services.policy_search_service import PolicySearchService
from app.services.policy_ingestion_service import PolicyIngestionService
from app.repositories.member_coverage_repository import MemberCoverageRepository
from app.services.member_coverage_service import MemberCoverageService
from app.repositories.member_repository import MemberRepository
from app.services.member_service import MemberService
from sqlalchemy.orm import Session
from app.db.session import sessionlocal
from fastapi import Depends


#============================================================
# DATABASE DEPENDENCY
#============================================================
def get_db():
    db=sessionlocal()

    try:
        yield db
    finally:
        db.close()

#============================================================
# AUTH SERVICE DEPENDENCY
#============================================================



"""
get_db()
   ↓
create db
   ↓
yield db
   ↓
PAUSE ⏸️
   ↓
FastAPI gives db to route
   ↓
route uses db
   ↓
route finishes
   ↓
get_db() RESUMES ▶️
   ↓
finally
   ↓
db.close()


🧠 Best mental model

Think of yield here as:

"Give this object to FastAPI for now, pause me, and come back to me when the request is finished."

So yes, your idea that return would end the function before cleanup can happen is correct.

Just don't think of yield as being used because of an iterator. yield creates a generator, but FastAPI is using the generator's pause/resume behavior for dependency cleanup.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User

from app.db.session import sessionlocal

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)

def get_user_repository(
        db:Session=Depends(get_db)
):
    return UserRepository(db)

def get_organization_repository(
        db:Session=Depends(get_db)
):
    return OrganizationRepository(db)

def get_auth_service(
        db:Session=Depends(get_db),
        user_reposetory:UserRepository=Depends(
            get_user_repository
        ),
        organ_reposetory:OrganizationRepository=Depends(
            get_organization_repository
        )
):
    return AuthService(
        db, user_reposetory,organ_reposetory
    )


def get_authorization_service(
    request: Request,
    db: Session = Depends(get_db),
    user_repository = Depends(get_user_repository)
):
    coverage_repository = MemberCoverageRepository(db)
    repository = AuthorizationRepository(db)
    workflow_repository = AuthorizationWorkflowRepository(db)
    policy_repository = PolicyRepository(db)
    document_repository = DocumentRepository(db)

    graph = request.app.state.authorization_graph


    return AuthorizationService(
        repository=repository,
        db=db,
        coverage_repository=coverage_repository,
        workflow_repository=workflow_repository,
        policy_repository=policy_repository,
        document_repository=document_repository,
        graph=graph,
        user_repository=user_repository,
    )
#===============================================
# GET CURRENT USER
#===============================================
def get_current_user(
        token:str =Depends(
            oauth2_scheme
        ),
        service:AuthService=Depends(
            get_auth_service
        )
):
    return service.get_current_user(token)



#============================================================
# Required the role for the Authorization
#============================================================
def require_role(require_role:str):
    def role_checker(
            current_user:User=Depends(get_current_user)
            ):
        if current_user.role!=require_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission"
            )
        return current_user
    return role_checker

def get_user_service(
        user_repository=Depends(get_user_repository),
        db=Depends(get_db)
):
    return UserService(user_repository,db)

#============================================================
# Required Permission
#============================================================
from app.core.permission import ( Permission, Role , ROLE_PERMISSIONS)

def require_permission(required_permission:Permission):
    def permission_checker(
            current_user:User=Depends(get_current_user)
    ):
        try:
            # Role("PROVIDER") find role  Role.PROVIDER
            role=Role(current_user.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        permission=ROLE_PERMISSIONS.get(
            role,
            set()
        )
        if required_permission not in permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return permission_checker

#============================================================
# GET AUTH REPOSETORY
#============================================================
def get_authorization_reposetory(
        db:Session=Depends(get_db)
):
    return AuthorizationRepository(db)

#============================================================
# GET REVIEW SERVICE
#============================================================



def get_review_service(
    request: Request,
    db: Session = Depends(get_db),
    authorization_repo: AuthorizationRepository = Depends(
        get_authorization_reposetory
    )
):
    review_repo = AuthorizationReviewRepository(db)

    workflow_repo = AuthorizationWorkflowRepository(db)

    graph = request.app.state.authorization_graph

    return ReviewService(
        auth_repo=authorization_repo,
        review_repo=review_repo,
        workflow_repo=workflow_repo,
        graph=graph,
        db=db
    )


#============================================================
#============================================================
# ADDING THE PROVIDER DEPENDENCY
#============================================================
#============================================================

def get_document_repository(
        db:Session=Depends(get_db)
):
    return DocumentRepository(db)

def get_storage_service():
    return S3StorageService()


def get_document_service(
    request: Request,
    authorization_repository: AuthorizationRepository = Depends(
        get_authorization_reposetory
    ),
    document_reposetory: DocumentRepository = Depends(
        get_document_repository
    ),
    storage_service: S3StorageService = Depends(
        get_storage_service
    ),
    db: Session = Depends(get_db)
):
    workflow_repository = AuthorizationWorkflowRepository(db)

    graph = request.app.state.authorization_graph

    return DocumentService(
        authorization_repository=authorization_repository,
        document_reposetory=document_reposetory,
        storage_service=storage_service,
        workflow_repository=workflow_repository,
        graph=graph,
        db=db
    )


#============================================================
#============================================================
# ADDING THE POLICY DEPENDENCY
#============================================================
#============================================================
def get_redis_service(client:Redis=Depends(get_redis_client)):
    return CacheService(
            client=client
    )

def get_policy_repository(
        db:Session=Depends(get_db)
):
    return PolicyRepository(db=db)

def get_policy_ingestion_service(
        repository:PolicyRepository=Depends(get_policy_repository)
)->PolicyIngestionService:
    return PolicyIngestionService(
        repository
    )

def get_policy_service(
        policy_repository:PolicyRepository=Depends(get_policy_repository),
        storage_service:S3StorageService=Depends(get_storage_service),
        db:Session=Depends(get_db),
        cache=Depends(get_redis_service),
        ingestion_service:PolicyIngestionService=Depends(
            get_policy_ingestion_service
        )

):
    return PolicyService(
        policy_repository=policy_repository,
        storage_service=storage_service,
        db=db,
        cache=cache,
        policy_ingestion_service=ingestion_service
    )

def get_policy_serch_service(
     policy_repository:PolicyRepository=Depends(get_policy_repository),
):
   return PolicySearchService(
        policy_repository=policy_repository
    )

def get_policy_retrieval_service(
        db:Session= Depends(get_db),
        policy_repository:PolicyRepository=Depends(get_policy_repository)

)->PolicyREtrievalService:
    return PolicyREtrievalService(
        policy_repository=policy_repository
    )

def get_member_coverage_repository(
        db:Session=Depends(get_db)
)-> MemberCoverageRepository:
    return MemberCoverageRepository(db)

def get_member_coverage_service(
        db:Session = Depends(get_db),
        repository:MemberCoverageRepository=Depends(get_member_coverage_repository)
)->MemberCoverageService:
    return MemberCoverageService(db=db,
                                 repository=repository)

def get_member_repository(
        db:Session=Depends(get_db))->MemberRepository:
    return MemberRepository(db)

def get_member_service(
        db:Session=Depends(get_db),
        repository:MemberRepository=Depends(get_member_repository)

)->MemberService:
    return MemberService(db=db,
                         repository=repository)
