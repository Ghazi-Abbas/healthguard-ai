from pwdlib import PasswordHash
from datetime import datetime , timedelta, timezone
from jose import jwt ,JWTError
from app.core.config import settings
Password_hash=PasswordHash.recommended()


def hash_password(password:str)->str:
    return Password_hash.hash(password)

def verify_password(
        plain_password:str,
        hashed_password:str
)->bool:
    return Password_hash.verify(
        plain_password,
        hashed_password
    )

def create_access_token(
        user_id:int,
        organization_id:int,
        role:str
)->str:
    expire=datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload={
        "sub":str(user_id),
        "organization_id":organization_id,
        "role":role,
        "exp":expire
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM

    )

def validate_token(token:str):
    try:
        payload=jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        return payload
    except JWTError:
        return None
