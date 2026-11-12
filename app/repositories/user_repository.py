from sqlalchemy.orm import Session
from sqlalchemy import String, select
from app.models.user import User
class UserRepository:
    def __init__(self, db:Session):
        self.db=db

    #==============================================
    # GET BY EMAIL
    #==============================================
    def get_by_email(self,email:str):
        stmt=select(User).where(
            User.email==email
        )
        return self.db.execute(stmt).scalar_one_or_none()
    #==============================================
    # GET BY ID
    #==============================================
    def get_by_id(self,user_id:int):
        stmt=select(User).where(
            User.id==user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
    #==============================================
    # Craete
    #==============================================
    def create(self, user:User):
        self.db.add(user)
        return user

    #==============================================
    # GET USERS OF THE ORGANIZATION
    #==============================================

    def get_by_organization_id(self, organization_id:int):
        stmt=select(User).where(
            User.organization_id==organization_id
        )
        result=self.db.execute(stmt).scalars().all()
        return result
    #==============================================
    # GET USERS BY ID + ORGANIZATION
    #==============================================
    # That's tenant isolation.
    def get_by_id_for_organization(
        self,
        user_id:int,
        organization_id:int
    ):
        stmt=(
            select(User).where(
                User.id==user_id,
                User.organization_id==organization_id
            )
        )

        result=self.db.execute(stmt).scalar_one_or_none()
        return result
