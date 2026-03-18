"""
Authentication dependencies for FastAPI (MULTI-TENANT SAFE)
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.user import User
from app.core.security import verify_access_token, verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )

    try:
        payload = verify_access_token(credentials.credentials)

        if payload is None:
            raise credentials_exception

        email = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not email or not tenant_id:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = db.query(User).filter(
        User.email == email,
        User.tenant_id == tenant_id
    ).first()

    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:

    if not credentials:
        return None

    try:
        payload = verify_access_token(credentials.credentials)

        if payload is None:
            return None

        email = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        user = db.query(User).filter(
            User.email == email,
            User.tenant_id == tenant_id
        ).first()

        return user if user and user.is_active else None

    except Exception:
        return None