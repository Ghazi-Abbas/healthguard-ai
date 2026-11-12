from app.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.schemas.user import CreateUserRequest, ChangeRoleRequest
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import hash_password

class UserService:

#============================================================
# Creating the constructor
#============================================================
    def __init__(
            self,
            user_repository:UserRepository,
            db:Session
    ):
        self.user_repository=user_repository
        self.db=db
#============================================================
# Craete the user
#============================================================
    def create_user(
            self,
            request:CreateUserRequest,
            organization_id:int
    ):
        existing_users=(
            self.user_repository.get_by_email(
                request.email
            )
        )

        if existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        user=User(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
            role=request.role.value,
            organization_id=organization_id,
            is_active=True
        )
        self.user_repository.create(user)
        self.db.commit()
        self.db.refresh(user)

        return user


#============================================================
# get Organization Users
#============================================================
    def get_organization_users(
            self,
            organization_id:int
    ):
        return self.user_repository.get_by_organization_id(
            organization_id
        )
#============================================================
# CHANGE USER ROLE
#============================================================
    def change_role(
            self,
            user_id:int,
            organization_id:int,
            request:ChangeRoleRequest
    ):
        user:User=(
            self.user_repository.get_by_id_for_organization(
                user_id,
                organization_id
            )
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        # Don't allow changing yourself
        # in this simple implementation.
        #
        # More advanced rules can be added later.
        user.role=request.role.value
        self.db.commit()
        self.db.refresh(user)
        return user

    # =======================================
    # DEACTIVATE USER
    # =======================================
    def deactivate_user(
            self,
            user_id:int,
            organization_id:int
    ):
        user:User=self.user_repository.get_by_id_for_organization(
            user_id,
            organization_id
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user is not found"
            )

        user.is_active=False

        self.db.commit()
        self.db.refresh(user)
        return user
