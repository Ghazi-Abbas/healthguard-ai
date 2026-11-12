
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.authorization_workflow import AuthorizationWorkflow

from app.models.authorization import Authorization
from app.models.user import User
from app.models.document import Document


class AuthorizationRepository:

    def __init__(self, db: Session):
        self.db = db

    # ================================================
    # CREATE AUTHORIZATION
    # ================================================
    def create(self, authorization: Authorization):
        self.db.add(authorization)
        self.db.flush()
        self.db.refresh(authorization)
        return authorization

    # ================================================
    # GET ALL AUTHORIZATIONS CREATED BY USER
    # SAME USER + SAME ORGANIZATION
    # ================================================
    def get_by_user(
        self,
        user_id: int,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(
                Authorization.user_id == user_id,
                User.organization_id == organization_id
            )
            .order_by(Authorization.created_at.desc())
        )

        return self.db.execute(stmt).scalars().all()

    # ================================================
    # GET ONE AUTHORIZATION CREATED BY USER
    # ================================================
    def get_by_id_for_user(
        self,
        authorization_id: int,
        user_id: int,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(
                Authorization.id == authorization_id,
                Authorization.user_id == user_id,
                User.organization_id == organization_id
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()



    # ================================================
    # GET REVIEW QUEUE
    # ONLY WORKFLOWS WAITING FOR HUMAN REVIEW
    # ORGANIZATION-SCOPED
    # ================================================
    def get_review_queue(
        self,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(
                User,
                Authorization.user_id == User.id
            )
            .join(
                AuthorizationWorkflow,
                AuthorizationWorkflow.authorization_id == Authorization.id
            )
            .where(
                User.organization_id == organization_id,
                AuthorizationWorkflow.organization_id == organization_id,
                AuthorizationWorkflow.workflow_status == "WAITING_FOR_REVIEW",
                Authorization.status.in_(["SUBMITTED", "IN_REVIEW"])
            )
            .order_by(
                Authorization.created_at.asc()
            )
        )

        return self.db.execute(stmt).scalars().all()

    # ================================================
    # GET ONE AUTHORIZATION FOR ORGANIZATION
    # WITH RELATED WORKFLOW DATA
    # ================================================
    def get_by_id_for_organization(
        self,
        authorization_id: int,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(
                Authorization.id == authorization_id,
                User.organization_id == organization_id
            )
            .options(
                selectinload(Authorization.member),
                selectinload(Authorization.member_coverage),
                selectinload(
                    Authorization.documents
                ).selectinload(Document.pages)
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ================================================
    # GET ONE AUTHORIZATION FOR UPDATE
    # TENANT-SCOPED ROW LOCK
    # ================================================
    def get_by_id_for_organization_for_update(
        self,
        authorization_id: int,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(
                Authorization.id == authorization_id,
                User.organization_id == organization_id
            )
            .with_for_update(of=Authorization)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ================================================
    # UPDATE AUTHORIZATION STATUS
    # ================================================
    def update_status(
        self,
        authorization: Authorization,
        status: str
    ):
        authorization.status = status
        return authorization










    # ================================================
    # GET AUTHORIZATIONS WITH FILTERS AND PAGINATION
    # ORGANIZATION-SCOPED
    # ================================================
    def get_authorizations(
        self,
        organization_id: int,
        page: int,
        page_size: int,
        status=None,
        created_from=None,
        created_to=None,
        procedure_code=None
    ):

        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(User.organization_id == organization_id)
        )

        if status:
            stmt = stmt.where(
                Authorization.status == status
            )

        if procedure_code:
            stmt = stmt.where(
                Authorization.procedure_code == procedure_code
            )

        if created_from:
            stmt = stmt.where(
                Authorization.created_at >= created_from
            )

        if created_to:
            stmt = stmt.where(
                Authorization.created_at <= created_to
            )

        stmt = stmt.order_by(
            Authorization.created_at.desc(),
            Authorization.id.desc()
        )

        offset = (page - 1) * page_size

        stmt = (
            stmt
            .offset(offset)
            .limit(page_size)
        )

        result = self.db.execute(stmt)

        return result.scalars().all()


    def get_by_id_for_user_for_update(
        self,
        authorization_id: int,
        user_id: int,
        organization_id: int
    ):
        stmt = (
            select(Authorization)
            .join(User, Authorization.user_id == User.id)
            .where(
                Authorization.id == authorization_id,
                Authorization.user_id == user_id,
                User.organization_id == organization_id
            )
            .with_for_update(of=Authorization)
        )

        return self.db.execute(stmt).scalar_one_or_none()
