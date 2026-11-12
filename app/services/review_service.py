
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from langgraph.types import Command

from app.repositories.autharization_repository import AuthorizationRepository
from app.repositories.authorization_review_repository import AuthorizationReviewRepository
from app.repositories.authorization_workflow_repository import AuthorizationWorkflowRepository

from app.models.authorization import Authorization
from app.models.authorization_review import AuthorizationReview


class ReviewService:

    def __init__(
        self,
        auth_repo: AuthorizationRepository,
        review_repo: AuthorizationReviewRepository,
        workflow_repo: AuthorizationWorkflowRepository,
        graph,
        db: Session
    ):
        self.repository = auth_repo
        self.review_repository = review_repo
        self.workflow_repository = workflow_repo
        self.graph = graph
        self.db = db

    # ============================================================
    # VALIDATE AUTHORIZATION
    # ============================================================

    def _validate_authorization(
        self,
        authorization: Authorization | None
    ):

        if authorization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization not found"
            )

        if authorization.status not in ("SUBMITTED", "IN_REVIEW"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization is not available for review"
            )

    # ============================================================
    # VALIDATE WORKFLOW
    # ============================================================

    def _validate_workflow(self, workflow):

        if workflow is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization workflow not found"
            )

        if workflow.workflow_status != "WAITING_FOR_REVIEW":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workflow is not waiting for human review"
            )

    # ============================================================
    # SAVE REVIEW RECORD
    # ============================================================

    def _save_review(
        self,
        authorization_id: int,
        reviewer_id: int,
        organization_id: int,
        decision: str,
        comments: str | None = None
    ):

        review = AuthorizationReview(
            authorization_id=authorization_id,
            reviewer_id=reviewer_id,
            organization_id=organization_id,
            decision=decision,
            comments=comments
        )

        return self.review_repository.create(review)

    # ============================================================
    # VIEW REVIEW QUEUE
    # ============================================================

    def get_review_queue(
        self,
        organization_id: int
    ):

        return self.repository.get_review_queue(organization_id)

    # ============================================================
    # OPEN REVIEW CASE
    # ============================================================

    def get_case(
    self,
    organization_id: int,
    authorization_id: int
     ):
     # 1. Retrieve authorization.
     authorization = self.repository.get_by_id_for_organization(
          authorization_id,
          organization_id
     )

     if authorization is None:
          raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail="Authorization not found"
          )

     # 2. Retrieve workflow.
     workflow = self.workflow_repository.get_by_authorization(
          authorization_id,
          organization_id
     )

     self._validate_workflow(workflow)

     # 3. Retrieve saved LangGraph state.
     config = {
          "configurable": {
               "thread_id": workflow.thread_id
          }
     }

     try:
          snapshot = self.graph.get_state(config)
     except Exception as exc:
          raise HTTPException(
               status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
               detail="Unable to retrieve authorization assessment"
          ) from exc

     if not snapshot or not snapshot.values:
          raise HTTPException(
               status_code=status.HTTP_409_CONFLICT,
               detail="Authorization assessment is not available"
          )

     state = snapshot.values

     # 4. Return document metadata only.
     documents = []

     for document in authorization.documents:
          documents.append({
               "id": document.id,
               "filename": document.filename,
               "content_type": document.content_type,
               "processing_status": document.processing_status,
               "page_count": document.page_count
          })

     # 5. Build a limited authorization response.
     authorization_data = {
          "id": authorization.id,
          "member_id": authorization.member_id,
          "procedure_code": authorization.procedure_code,
          "diagnosis_code": authorization.diagnosis_code,
          "service_date": authorization.service_date,
          "status": authorization.status,
          "created_at": authorization.created_at,
          "updated_at": authorization.updated_at,
          "documents": documents
     }

     # 6. Build workflow response.
     workflow_data = {
          "id": workflow.id,
          "thread_id": workflow.thread_id,
          "workflow_status": workflow.workflow_status,
          "created_at": workflow.created_at,
          "updated_at": workflow.updated_at
     }

     # 7. Build AI assessment.
     ai_assessment = {
          "recommendation": state.get("recommendation"),
          "risk": state.get("risk"),
          "criteria_result": state.get("criteria_result", {}),
          "eligibility_result": state.get("eligibility_result", {}),
          "clinical_evidence": state.get("clinical_evidence", []),
          "missing_information": state.get("missing_information", []),
          "uncertainty": state.get("uncertainty", []),
          "guardrail_errors": state.get("guardrail_errors", [])
     }

     return {
          "authorization": authorization_data,
          "workflow": workflow_data,
          "ai_assessment": ai_assessment
     }

    # ============================================================
    # PROCESS HUMAN REVIEW DECISION
    # ============================================================

    def _process_decision(
        self,
        authorization_id: int,
        organization_id: int,
        reviewer_id: int,
        decision: str,
        comments: str | None = None
    ):

        try:

            # ----------------------------------------------------
            # 1. Lock authorization row
            # ----------------------------------------------------

            authorization = (
                self.repository.get_by_id_for_organization_for_update(
                    authorization_id,
                    organization_id
                )
            )

            self._validate_authorization(authorization)

            # ----------------------------------------------------
            # 2. Lock workflow row
            # ----------------------------------------------------

            workflow = (
                self.workflow_repository.get_by_authorization_for_update(
                    authorization_id,
                    organization_id
                )
            )

            self._validate_workflow(workflow)

            # ----------------------------------------------------
            # 3. Save reviewer decision
            # ----------------------------------------------------

            self._save_review(
                authorization_id=authorization_id,
                reviewer_id=reviewer_id,
                organization_id=organization_id,
                decision=decision,
                comments=comments
            )

            # ----------------------------------------------------
            # 4. Mark workflow as processing the decision
            # ----------------------------------------------------

            workflow.workflow_status = "REVIEW_RESUMING"

            # Save the review decision before graph execution.
            self.db.commit()

        except HTTPException:

            self.db.rollback()
            raise

        except Exception:

            self.db.rollback()
            raise

        # --------------------------------------------------------
        # 5. Resume the original LangGraph workflow
        # --------------------------------------------------------

        try:

            result = self.graph.invoke(
                Command(
                    resume={
                        "decision": decision,
                        "notes": comments or ""
                    }
                ),
                config={
                    "configurable": {
                        "thread_id": workflow.thread_id
                    }
                }
            )

            # ----------------------------------------------------
            # 6. Handle REQUEST_INFORMATION
            # ----------------------------------------------------

            if decision == "REQUEST_INFORMATION":

                # The graph should pause again at provider_information.
                if not result.get("__interrupt__"):
                    raise RuntimeError(
                        "Graph did not pause for provider information."
                    )

                authorization.status = "REQUEST_INFORMATION"

                workflow.workflow_status = (
                    "AWAITING_PROVIDER_INFORMATION"
                )

            # ----------------------------------------------------
            # 7. Handle final decisions
            # ----------------------------------------------------

            else:

                # APPROVE and REJECT should finish the graph.
                if result.get("__interrupt__"):
                    raise RuntimeError(
                        "Graph unexpectedly paused after a final decision."
                    )

                if decision == "APPROVE":

                    authorization.status = "APPROVED"

                elif decision == "REJECT":

                    authorization.status = "REJECTED"

                else:

                    raise ValueError(
                        f"Unsupported review decision: {decision}"
                    )

                workflow.workflow_status = "REVIEW_COMPLETED"

            # ----------------------------------------------------
            # 8. Save final database status
            # ----------------------------------------------------

            self.db.commit()

            self.db.refresh(authorization)

            return authorization

        except Exception as error:

            # ----------------------------------------------------
            # 9. Handle graph execution failure
            # ----------------------------------------------------

            self.db.rollback()

            workflow = (
                self.workflow_repository.get_by_authorization(
                    authorization_id,
                    organization_id
                )
            )

            if workflow is not None:

                workflow.workflow_status = "RESUME_FAILED"

                self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The review decision was saved, but the workflow "
                    "could not be resumed. Administrative recovery is required."
                )
            ) from error

    # ============================================================
    # APPROVE
    # ============================================================

    def approve(
        self,
        authorization_id: int,
        organization_id: int,
        reviewer_id: int,
        comments: str | None = None
    ):

        return self._process_decision(
            authorization_id=authorization_id,
            organization_id=organization_id,
            reviewer_id=reviewer_id,
            decision="APPROVE",
            comments=comments
        )

    # ============================================================
    # REJECT
    # ============================================================

    def reject(
        self,
        authorization_id: int,
        organization_id: int,
        reviewer_id: int,
        comments: str | None = None
    ):

        return self._process_decision(
            authorization_id=authorization_id,
            organization_id=organization_id,
            reviewer_id=reviewer_id,
            decision="REJECT",
            comments=comments
        )

    # ============================================================
    # REQUEST ADDITIONAL INFORMATION
    # ============================================================

    def request_information(
        self,
        authorization_id: int,
        organization_id: int,
        reviewer_id: int,
        message: str
    ):

        return self._process_decision(
            authorization_id=authorization_id,
            organization_id=organization_id,
            reviewer_id=reviewer_id,
            decision="REQUEST_INFORMATION",
            comments=message
        )
