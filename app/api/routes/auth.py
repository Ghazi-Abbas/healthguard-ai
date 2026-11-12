from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import (
   RegisterRequest,
   UserResponse,
   TokenResponse,
   LoginRequest


)

from app.services.auth_service import AuthService

from app.api.dependencies import (
    get_auth_service,
    get_current_user
)

from app.models.user import User

router=APIRouter(
    prefix="/api/v1/auth",
    tags=["Authenticaion"]
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    request:RegisterRequest,
    service:AuthService=Depends(
        get_auth_service
    )
):
    try:
        user=service.register(
            organization_name=request.organization_name,
            email=request.email,
            password=request.password,
            user_name=request.username

        )

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/login",
    response_model=TokenResponse,

)
def login(
    request:LoginRequest,
    service:AuthService=Depends(
        get_auth_service
    )
):

    try:
        token=service.login(
            email=request.email,
            password=request.password
        )

        return {"access_token":token,
                "token_type":"bearer"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={
                "WWW-Authenticate": "Bearer"
            }

        )

@router.get("/me",
            response_model=UserResponse)
def get_me(
    current_user:User =Depends(
        get_current_user
    )
):
    return current_user


@router.post("/token", response_model=TokenResponse)
def login_for_swagger(
    request: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    try:
        token = service.login(
            email=request.username,
            password=request.password
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
