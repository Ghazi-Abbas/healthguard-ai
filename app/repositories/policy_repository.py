from sqlalchemy.orm import Session ,selectinload
from sqlalchemy import select

from app.models.policy import (
    Policy,
    PolicyDocument,
    PolicyDocumentPage

)
class PolicyRepository:
    def __init__(self, db:Session):
        self.db=db

    #===========================================
    # CREATE THE POLICY
    #===========================================

    def create_policy(
            self,
            policy:Policy
    ):
        self.db.add(policy)
        return policy
    #===========================================
    # GET POLICY BY ID FOR THE ORGANIZATION
    #===========================================

    def get_by_id_for_organization(
            self,
            policy_id:int,
            organization_id:int
    ):
        stmt=(
            select(Policy)
            .where(
                Policy.id==policy_id,
                Policy.organization_id==organization_id
        )

        )

        return(
            self.db
            .execute(stmt)
            .scalar_one_or_none()
        )

    #===========================================
    # CREATE THE DOCUMENTS
    #===========================================
    def create_document(
            self,
            document:PolicyDocument
    ):
        self.db.add(document)

        return document
    #===========================================
    # CREATE THE PAGE
    #===========================================
    def create_page(
            self,
            page:PolicyDocumentPage
    ):
        self.db.add(page)
        return page

    #===========================================
    # GET DOCUMENTS
    #===========================================
    def get_Documents(
            self,
            policy_id:int,
    ):
        stmt=(
            select(PolicyDocument)
            .where(
                PolicyDocument.policy_id
                ==policy_id
            )
            .order_by(
                PolicyDocument.created_at.desc()
            )
        )

        return(
            self.db
            .execute(stmt)
            .scalars()
            .all()
        )

    # ===========================================
    # GET DOCUMENT FOR INGESTION "This return the document with page"
    # ===========================================

    def get_document_for_ingestion(
        self,
        *,
        organization_id:int,
        policy_version_id:int,
        document_id:int,
    )-> PolicyDocument |None:
        stmt=(
            select(PolicyDocument)
            .join(
                Policy,
                PolicyDocument.policy_id==Policy.id
            )
            .where(
                PolicyDocument.id==document_id,
                Policy.id==policy_version_id,
                Policy.organization_id== organization_id
            )
            # how SQLAlchemy should load related data.
            # Think of it like ordering food: select() tells the kitchen what you want,
            # and options() adds instructions about how to prepare your order.
            # selectinload() fetches related records with a separate query and associates them with their parent objects.
            .options(
                # selectinload() is a loading strategy that fetches related collections through a separate
                # SELECT query, helping avoid the N+1 query problem."
                selectinload(PolicyDocument.pages)
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()




    # ===========================================
    # UPDATE DOCUMENT INDEXING STATUS
    # ===========================================

    def update_document_indexing_status(
        self,
        *,
        organization_id: int,
        policy_version_id: int,
        document_id: int,
        indexing_status: str,
    ) -> PolicyDocument | None:

        stmt = (
            select(PolicyDocument)
            .join(
                Policy,
                PolicyDocument.policy_id == Policy.id,
            )
            .where(
                PolicyDocument.id == document_id,
                Policy.id == policy_version_id,
                Policy.organization_id == organization_id,
            )
        )

        document = (
            self.db.execute(stmt)
            .scalar_one_or_none()
        )

        if document is None:
            return None

        document.indexing_status = indexing_status

        self.db.commit()
        self.db.refresh(document)

        return document




    """
SQLAlchemy also issues a separate query, conceptually:
SELECT policy_document_pages.*
FROM policy_document_pages
WHERE policy_document_pages.document_id IN (501);
    """

    """
document.id       # 501
document.filename # "mri_policy.pdf"
document.pages    # [page 1, page 2, ...]"""

    # ===========================================
    # GET ACTIVE POLICY VERSION IDS
    # ===========================================
    def get_active_policy_version_ids(
            self,
            *,
            organization_id:int
    )->list[int]:
        stmt=select(Policy.id).where(
            Policy.organization_id==organization_id,
            Policy.status=="ACTIVE"
        )

        return list(self.db.execute(stmt).scalars().all())

    """
    [101, 102]
    """

    """
    The mental model to remember: the first method finds a particular document to prepare for AI ingestion;
    the second identifies which active policies are eligible when searching policy chunks.
    """
