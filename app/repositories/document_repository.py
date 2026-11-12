
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models.document import DocumentPage, Document
from app.models.authorization import Authorization
from app.models.user import User


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    # ===============================================
    # CREATE DOCUMENT
    # ===============================================
    def create(self, document: Document):
        self.db.add(document)
        return document

    # ===============================================
    # CREATE DOCUMENT PAGES
    # ===============================================
    def create_page(self, page: DocumentPage):
        self.db.add(page)
        return page

    # ===============================================
    # GET DOCUMENTS BY AUTHORIZATION
    # ORGANIZATION-SCOPED
    # ===============================================
    def get_by_authorization(
        self,
        authorization_id: int,
        organization_id: int
    ):

        stmt = (
            select(Document)
            .join(
                Authorization,
                Document.authorization_id == Authorization.id
            )
            .join(
                User,
                Authorization.user_id == User.id
            )
            .where(
                Document.authorization_id == authorization_id,
                User.organization_id == organization_id
            )
            .order_by(Document.created_at.desc())
        )

        result = self.db.execute(stmt)

        return result.scalars().all()

    # ===============================================
    # GET PROCESSED DOCUMENTS WITH THEIR PAGES
    # ORGANIZATION-SCOPED
    # ===============================================
    def get_processed_documents_with_pages(
        self,
        authorization_id: int,
        organization_id: int
    ):

        stmt = (
            select(Document)
            .join(
                Authorization,
                Document.authorization_id == Authorization.id
            )
            .join(
                User,
                Authorization.user_id == User.id
            )
            .options(
                selectinload(Document.pages)
            )
            .where(
                Document.authorization_id == authorization_id,
                User.organization_id == organization_id,
                Document.processing_status == "PROCESSED"
            )
            .order_by(Document.created_at.asc())
        )

        result = self.db.execute(stmt)

        return result.scalars().all()
