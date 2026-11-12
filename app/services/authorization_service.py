from app.repositories.autharization_repository import AuthorizationRepository
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.models.authorization import Authorization
from app.schemas.authorization import AuthorisationPatch, AuthorizationCreate
from app.schemas.review import RequestINformationRequest
from app.repositories.member_coverage_repository import MemberCoverageRepository
from app.repositories.authorization_workflow_repository import (
    AuthorizationWorkflowRepository
)
from sqlalchemy.exc import IntegrityError
from app.repositories.policy_repository import PolicyRepository
from uuid import uuid4
from app.models.authorization_workflow import AuthorizationWorkflow
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository

import logging

logger = logging.getLogger(__name__)


class AuthorizationService:

    def __init__(
          self,
          repository: AuthorizationRepository,
          db: Session,
          coverage_repository: MemberCoverageRepository,
          workflow_repository: AuthorizationWorkflowRepository,
          policy_repository: PolicyRepository,
          document_repository: DocumentRepository,
          graph,
          user_repository: UserRepository = None,

          ):
          self.repository = repository
          self.db = db
          self.coverage_repository = coverage_repository
          self.workflow_repository = workflow_repository
          self.policy_repository = policy_repository
          self.document_repository = document_repository
          self.graph = graph
          self.user_repository = user_repository



#============================================================
# CREATE THE USER
#============================================================
    def create(
    self,
    request: AuthorizationCreate,
    user_id: int,
    organization_id: int
) -> Authorization:

     try:
          # 1. Verify that the requesting user belongs to this organization.
          user = self.user_repository.get_by_id_for_organization(
               user_id=user_id,
               organization_id=organization_id
          )

          if user is None:
               raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
               )

          # 2. Verify that the member has active coverage in this organization.
          coverage = (
               self.coverage_repository.get_active_coverage_for_service_date(
                    member_id=request.member_id,
                    plan_id=request.plan_id,
                    service_date=request.service_date,
                    organization_id=organization_id
               )
          )

          if coverage is None:
               raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                         "No active coverage was found for this member, "
                         "plan, and service date. Verify eligibility "
                         "before creating the authorization."
                    )
               )

          # 3. Create authorization only after both checks pass.
          authorization = Authorization(
               member_id=request.member_id,
               member_record_id=coverage.member_id,
               member_coverage_id=coverage.id,
               service_date=request.service_date,
               procedure_code=request.procedure_code,
               diagnosis_code=request.diagnosis_code,
               clinical_summary=request.clinical_summary,
               user_id=user_id,
               status="DRAFT",
          )

          self.repository.create(authorization)
          self.db.commit()
          self.db.refresh(authorization)

          return authorization

     except HTTPException:
          self.db.rollback()
          raise

     except SQLAlchemyError:
          self.db.rollback()

          logger.exception(
               "Database error while creating authorization"
          )

          raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail="Failed to create authorization"
          ) from None
    # =====================================
    # GET ALL OWN SAME ORG + SAME USER
    # =====================================
    def get_my_authorizations(
              self,
              user_id:int,
              organization_id:int
    ):
         return(
              self.repository.get_by_user(
                   user_id,
                   organization_id
              )
         )
    # =====================================
    # GET ONE OWN AUTHORIZATION
    # =====================================
    def get_my_authorization(
              self,
              authorization_id:int,
              user_id:int,
              organization_id:int
    ):
         authorization:Authorization=self.repository.get_by_id_for_user(
              authorization_id,
              user_id,
              organization_id
         )
         if authorization is None:
            raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="Authorization not found"
            )
         return authorization

    # =====================================
    # UPDATE
    # =====================================

    def update_authorization(
          self,
          authorization_id: int,
          request: AuthorisationPatch,
          user_id: int,
          organization_id: int
          ):
          authorization = self.repository.get_by_id_for_user(
               authorization_id,
               user_id,
               organization_id
          )

          if authorization is None:
               raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorization not found"
               )

          if authorization.status != "DRAFT":
               raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only Draft authorizations can be modified"
               )

          update_data = request.validate_patch_data()

          for field, value in update_data.items():
               setattr(authorization, field, value)

          self.db.commit()
          self.db.refresh(authorization)

          return authorization

    # =====================================
    # SUBMIT
    # =====================================
    def submit_authorization(
              self,
              authorization_id:int,
              user_id:int,
              organization_id:int
    ):
         authorization=(
         self.repository.get_by_id_for_user(
              authorization_id,
              user_id,
              organization_id
         ))

         if authorization is None:
              raise HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail="Authorization not found"
              )
         if authorization.status !="DRAFT":
              raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail=(
                        "Only Draft authorization"
                        "can be submitted"
                   )
              )
         authorization.status="SUBMITTED"

         self.db.commit()
         self.db.refresh(authorization)
         return authorization




    def get_organization_authorization(
            self,
            organization_id: int,
            page: int = 1,
            page_size: int = 20,
            status=None,
            created_from=None,
            created_to=None,
            procedure_code=None
    ):
         return self.repository.get_authorizations(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            status=status,
            created_from=created_from,
            created_to=created_to,
            procedure_code=procedure_code
         )

    # =====================================
    # Build the initial
    # =====================================


    def build_initial_state(
     self,
     authorization,
     organization_id: int,
     thread_id: str
     ) -> dict:

     # 1. Prepare authorization facts
     authorization_data = {
          "member_id": authorization.member_id,
          "procedure_code": authorization.procedure_code,
          "diagnosis_code": authorization.diagnosis_code,
          "clinical_summary": authorization.clinical_summary,
          "service_date": authorization.service_date.isoformat()
     }

     # 2. Retrieve coverage using the internal member ID
     coverage_records = (
          self.coverage_repository.get_coverage_for_eligibility(
               organization_id=organization_id,
               member_id=authorization.member_record_id
          )
     )

     # 3. Retrieve active policy versions for this organization
     active_policy_version_ids = (
          self.policy_repository.get_active_policy_version_ids(
               organization_id=organization_id
          )
     )

     documents = (
          self.document_repository.get_processed_documents_with_pages(
          authorization_id=authorization.id,
         organization_id=organization_id
          )
     )

     # 4. Prepare clinical document pages
     clinical_pages = []

     for document in documents:
          for page in document.pages:

               clinical_pages.append({
                    "evidence_id": (
                         f"DOC-{document.id}-PAGE-{page.page_number}"
                    ),
                    "document_id": document.id,
                    "filename": document.filename,
                    "page_number": page.page_number,
                    "text": page.text
               })

     # 5. Prepare policy question
     policy_question = (
          f"Determine the applicable policy criteria for "
          f"procedure {authorization.procedure_code} "
          f"and diagnosis {authorization.diagnosis_code}."
     )

     # 6. Build initial LangGraph state
     return {
          "authorization_id": authorization.id,
          "thread_id": thread_id,
          "organization_id": organization_id,

          "authorization": authorization_data,

          "service_date": authorization.service_date.isoformat(),

          "policy_question": policy_question,

          "case_context": authorization.clinical_summary,

          "active_policy_version_ids": active_policy_version_ids,

          "clinical_pages": clinical_pages,

          "coverage_records": coverage_records,

          "workflow_status": "RUNNING",

          "needs_human_review": False
     }

    # =====================================
    # Start authorization workflow
    # =====================================
    def start_authorization_workflow(
          self,
          authorization_id: int,
          user_id: int,
          organization_id: int
          ):
          # 1. Retrieve authorization belonging to this user and organization
          authorization = self.repository.get_by_id_for_user(
               authorization_id=authorization_id,
               user_id=user_id,
               organization_id=organization_id
          )

          if authorization is None:
               raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorization not found"
               )

          # 2. Check whether a workflow already exists
          existing_workflow = (
               self.workflow_repository.get_by_authorization(
                    authorization_id=authorization_id,
                    organization_id=organization_id
               )
          )

          if existing_workflow:
               return existing_workflow

          # 3. Only DRAFT authorizations can start a new workflow
          if authorization.status != "DRAFT":
               raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only DRAFT authorizations can be submitted"
               )

          # 4. Generate a unique LangGraph thread ID
          thread_id = str(uuid4())

          # 5. Create workflow record
          workflow = AuthorizationWorkflow(
               authorization_id=authorization.id,
               organization_id=organization_id,
               thread_id=thread_id,
               workflow_status="RUNNING"
          )

          try:
               # Mark authorization as submitted
               authorization.status = "SUBMITTED"

               # Add workflow to database
               self.workflow_repository.create(workflow)

               # Commit both changes before invoking the graph
               self.db.commit()

          except IntegrityError:
               self.db.rollback()

               # Another request may have created the workflow
               existing_workflow = (
                    self.workflow_repository.get_by_authorization(
                         authorization_id=authorization_id,
                         organization_id=organization_id
                    )
               )

               if existing_workflow:
                    return existing_workflow

               raise

          try:
               # 6. Build initial LangGraph state
               initial_state = self.build_initial_state(
                    authorization=authorization,
                    organization_id=organization_id,
                    thread_id=thread_id
               )

               # 7. Configure PostgreSQL checkpoint thread
               config = {
                    "configurable": {
                         "thread_id": thread_id
                    }
               }

               # 8. Execute the authorization graph
               result = self.graph.invoke(
                    initial_state,
                    config=config
               )

               # 9. Check whether the graph paused for human review
               if result.get("__interrupt__"):

                    authorization.status = "IN_REVIEW"

                    workflow.workflow_status = "WAITING_FOR_REVIEW"

                    self.db.commit()

                    self.db.refresh(authorization)
                    self.db.refresh(workflow)

                    return workflow

          except Exception as exc:

               logger.error(
                    "Authorization workflow failed | "
                    "authorization_id=%s | organization_id=%s | "
                    "thread_id=%s | error_type=%s",
                    authorization_id,
                    organization_id,
                    thread_id,
                    type(exc).__name__,
                    exc_info=True,
               )

               self.db.rollback()

               failed_workflow = (
                    self.workflow_repository.get_by_authorization(
                         authorization_id=authorization_id,
                         organization_id=organization_id
                    )
               )

               if failed_workflow:
                    failed_workflow.workflow_status = "FAILED"
                    self.db.commit()

               raise
