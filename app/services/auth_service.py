from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import(
    hash_password,
    verify_password,
    create_access_token,
    validate_token
)

from app.models.organization import Organization
from app.models.user import User

from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository


class AuthService:

    def __init__(
            self, db:Session,
            user_reposetory:UserRepository,
            organ_reposetory:OrganizationRepository
    ):
        self.db=db
        self.user_reposetory=user_reposetory
        self.organ_reposetory=organ_reposetory

    def register(
            self,
            organization_name:str,
            user_name:str,
            email:str,
            password:str
    ):
        existing_user=(
            self.user_reposetory.get_by_email(email)
        )

        if existing_user:
            raise ValueError("User with this email already exists")
        # 1. Create organization
        organization=Organization(
            name=organization_name
        )

        self.organ_reposetory.create(organization)

        # Make SQLAlchemy generate organization.id
        self.db.flush()

        # 2. Create first user

        user=User(
            email=email,
            password_hash=hash_password(password),
            username=user_name,
            role="ADMIN",
            organization_id=organization.id
        )

        self.user_reposetory.create(user)

        # 3. Commit everything together

        self.db.commit()

        self.db.refresh(user)

        return user
    #================================================
    #LOGIN
    #================================================
    def login(
        self,
        email:str,
        password:str
    ):
        user=(
            self.user_reposetory.get_by_email(email)
        )

        if not user:
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is in active")

        if not verify_password(
            password,
            user.password_hash
        ):
            raise ValueError(
                "Invalid email or password"
            )

        token=create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            role=user.role
        )

        return token


    #===============================================
    # GET CURRENT USER
    #===============================================

    def get_current_user(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

        # Step 1: Validate JWT signature and expiration
        payload = validate_token(token)

        if payload is None:
            raise credentials_exception

        # Step 2: Extract user ID
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        # Step 3: Validate user ID format
        try:
            user_id = int(user_id)

            if user_id <= 0:
                raise ValueError("Invalid user ID")

        except (ValueError, TypeError):
            raise credentials_exception

        # Step 4: Fetch user from database
        user = self.user_reposetory.get_by_id(user_id)

        if user is None:
            raise credentials_exception

        # Step 5: Reject inactive users
        if not user.is_active:
            raise credentials_exception

        return user
