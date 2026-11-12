from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.authorization_workflow import AuthorizationWorkflow

class AuthorizationWorkflowRepository:
    def __init__(
            self,
            db:Session
    ):
        self.db=db

    #===============================================
    #Create Workflow
    #===============================================
    def create(self, workflow:AuthorizationWorkflow):
        self.db.add(workflow)
        self.db.flush()
        self.db.refresh(workflow)

        return workflow

    #==================================================
    #Get workflow by authorization and organization
    #===================================================
    def get_by_authorization(
            self,
            authorization_id:int,
            organization_id:int,
    ):
        stmt=(select(AuthorizationWorkflow)
              .where(
                  AuthorizationWorkflow.authorization_id==authorization_id,
                  AuthorizationWorkflow.organization_id==organization_id
              ))

        return self.db.execute(stmt).scalar_one_or_none()

    #=======================================================
    #Get workflow by thread Id
    #=======================================================
    def get_by_thread_id(
        self,
        thread_id: str,
        organization_id: int
    ):
        stmt = (
            select(AuthorizationWorkflow)
            .where(
                AuthorizationWorkflow.thread_id == thread_id,
                AuthorizationWorkflow.organization_id == organization_id
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()

    #==========================================================
    #Get workflow with row lock
    #==========================================================
    def get_by_authorization_for_update(
            self,
            authorization_id:int,
            organization_id:int
    ):
        stmt=(
            select(AuthorizationWorkflow)
            .where(
                AuthorizationWorkflow.authorization_id==authorization_id,
                AuthorizationWorkflow.organization_id==organization_id
            )
            .with_for_update()
        )

        return self.db.execute(stmt).scalar_one_or_none()


    '''
Imagine two reviewers attempt to approve the same authorization simultaneously.

Without a database lock, both requests might retrieve the pending workflow and attempt to resume it.

With PostgreSQL row locking:
- Reviewer A acquires the lock.
- Reviewer B waits.
- Reviewer A processes the decision and commits.
- Reviewer B obtains the lock and must recheck the workflow status.
This is one layer of our duplicate-decision protection. We will also implement status validation and idempotency in the service.
    '''
