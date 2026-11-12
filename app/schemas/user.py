from enum import Enum
from pydantic import BaseModel, Field , EmailStr

class UserRole(str,Enum):
    ADMIN="ADMIN"
    PROVIDER="PROVIDER"
    REVIEWER="REVIEWER"

class CreateUserRequest(BaseModel):
    username:str= Field(
            min_length=3,
            max_length=128
        )
    email:EmailStr
    password:str=Field(min_length=8)
    role:UserRole

class ChangeRoleRequest(BaseModel):
    role:UserRole

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    username:str
    role:UserRole
    organization_id:int
    is_active:bool

    # Allows Pydantic to read values from ORM/SQLAlchemy objects
    # from_attributes=True allows Pydantic to read attributes from
    # a SQLAlchemy ORM object and use them to build the Pydantic response model.
    model_config={
        "from_attributes":True
    }
