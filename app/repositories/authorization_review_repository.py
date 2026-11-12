
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.authorization_review import AuthorizationReview


class AuthorizationReviewRepository:

    def __init__(self, db: Session):
        self.db = db

    # ================================================
    # CREATE REVIEW RECORD
    # ================================================
    def create(self, review: AuthorizationReview):

        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)

        return review

    # ================================================
    # GET REVIEWS FOR AN AUTHORIZATION
    # ORGANIZATION-SCOPED
    # ================================================
    def get_by_authorization(
        self,
        authorization_id: int,
        organization_id: int
    ):

        stmt = (
            select(AuthorizationReview)
            .where(
                AuthorizationReview.authorization_id == authorization_id,
                AuthorizationReview.organization_id == organization_id
            )
            .order_by(
                AuthorizationReview.created_at.desc()
            )
        )

        return self.db.execute(stmt).scalars().all()

    # ================================================
    # GET LATEST REVIEW
    # ================================================
    def get_latest_by_authorization(
        self,
        authorization_id: int,
        organization_id: int
    ):

        stmt = (
            select(AuthorizationReview)
            .where(
                AuthorizationReview.authorization_id == authorization_id,
                AuthorizationReview.organization_id == organization_id
            )
            .order_by(
                AuthorizationReview.created_at.desc(),
                AuthorizationReview.id.desc()
            )
            .limit(1)
        )

        return self.db.execute(stmt).scalar_one_or_none()
