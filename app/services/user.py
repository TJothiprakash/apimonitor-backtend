"""
User service layer for business logic
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password, create_email_verification_token
from app.services.email import email_service
from app.models.tenant import Tenant

from app.core.security import verify_password




class UserService:

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """
        TEMP: Find user by email (single tenant assumption for now)
        Later: add tenant selection
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    from app.models.tenant import Tenant
    from app.core.security import get_password_hash, create_email_verification_token

    @staticmethod
    async def create_user(db: Session, user_data: UserCreate) -> User:
        """Create new user (MULTI-TENANT SAFE)"""

        # 🔍 Check existing user
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # 🔥 STEP 1: CREATE TENANT
        tenant = Tenant(name=f"{user_data.username}-tenant")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # 🔥 STEP 2: CREATE USER WITH tenant_id
        verification_token = create_email_verification_token(user_data.email)

        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            verification_token=verification_token,
            tenant_id=tenant.id  # ✅ THIS FIXES YOUR ERROR
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # 🔥 STEP 3: SEND EMAIL
        await email_service.send_verification_email(
            to_email=user_data.email,
            username=user_data.username,
            token=verification_token
        )

        return db_user


    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)
        
        # Check if email is being updated and if it's already taken
        if "email" in update_data:
            existing_user = UserService.get_user_by_email(db, update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """Verify user email with token"""
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            return False

        user.is_verified = True
        user.verification_token = None
        db.commit()
        return True

    @staticmethod
    def update_last_login(db: Session, user_id: int):
        """Update user's last login timestamp"""
        user = UserService.get_user_by_id(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """Deactivate user account"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        db.commit()
        return True

    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
        """Activate user account"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = True
        db.commit()
        return True

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> bool:
        """Update user password"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None  # Clear any existing reset token
        db.commit()
        return True

    @staticmethod
    def set_password_reset_token(db: Session, email: str, token: str) -> bool:
        """Set password reset token for user"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False

        user.password_reset_token = token
        db.commit()
        return True

    @staticmethod
    def set_verification_token(db: Session, email: str, token: str) -> bool:
        """Set email verification token for user"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False

        user.verification_token = token
        db.commit()
        return True

    @staticmethod
    def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
        """Get user by password reset token"""
        return db.query(User).filter(User.password_reset_token == token).first()

    @staticmethod
    def set_refresh_token(db: Session, email: str, token: str) -> bool:
        """Set refresh token for user"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False

        user.refresh_token = token
        db.commit()
        return True

    @staticmethod
    def get_user_by_refresh_token(db: Session, token: str) -> Optional[User]:
        """Get user by refresh token"""
        return db.query(User).filter(User.refresh_token == token).first()

    @staticmethod
    def clear_refresh_token(db: Session, email: str) -> bool:
        """Clear stored refresh token for a user (logout)"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False

        user.refresh_token = None
        db.commit()
        return True


# Create user service instance
user_service = UserService()
