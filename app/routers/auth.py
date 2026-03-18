"""
Authentication routes for user registration, login, password reset, and email verification
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, logger
from sqlalchemy.orm import Session
from app.database.base import get_db

from app.database.base import get_db
from app.schemas.user import LoginRequest, TokenResponse
from app.services.user import user_service
from app.core.security import create_access_token
from app.core.config import settings

from app.schemas.user import (
    UserCreate, 
    UserLogin, 
    UserResponse, 
    Token, 
    PasswordResetRequest, 
    PasswordReset,
    EmailVerification,
    MessageResponse
)
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    create_password_reset_token,
    verify_token
)
from app.core.config import settings
from app.services.user import user_service
from app.services.email import email_service
from app.dependencies.auth import get_current_active_user, get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    """
    try:
        logger.info(f"Register request received for email={user_data.email}")

        user = await user_service.create_user(db, user_data)

        logger.info(f"User created successfully email={user.email}, id={user.id}")
        return user

    except HTTPException as e:
        logger.warning(f"HTTP error during registration: {e.detail}")
        raise e

    except Exception as e:
        logger.exception(f"Unexpected error during registration for email={user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    # 🔍 Authenticate
    user = user_service.authenticate_user(
        db,
        email=user_credentials.email,
        password=user_credentials.password
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 🔥 CREATE TOKEN (MULTI-TENANT)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        subject=user.email,
        tenant_id=str(user.tenant_id),   # 🔥 CRITICAL
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    email = verify_token(refresh_token, token_type="refresh")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user and validate stored refresh token
    user = user_service.get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    # Ensure the provided refresh token matches the one we have stored
    if not user.refresh_token or user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(subject=user.email)
    # Persist new refresh token
    user_service.set_refresh_token(db, user.email, new_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(verification: EmailVerification, db: Session = Depends(get_db)):
    """
    Verify user email address
    """
    # Verify email verification token
    email = verify_token(verification.token, token_type="email_verification")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Verify user email
    success = user_service.verify_email(db, verification.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )
    
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Resend email verification
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Create new verification token
    from app.core.security import create_email_verification_token
    verification_token = create_email_verification_token(current_user.email)
    
    # Persist the new verification token using the active DB session
    success_set = user_service.set_verification_token(db, current_user.email, verification_token)
    if not success_set:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update verification token"
        )

    # Send verification email
    success = await email_service.send_verification_email(
        to_email=current_user.email,
        username=current_user.username,
        token=verification_token
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return MessageResponse(message="Verification email sent successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request password reset
    """
    # Check if user exists
    user = user_service.get_user_by_email(db, request.email)
    if not user:
        # Return success even if user doesn't exist for security
        return MessageResponse(message="If your email is registered, you will receive a password reset link")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Create password reset token
    reset_token = create_password_reset_token(user.email)
    
    # Save token to database
    user_service.set_password_reset_token(db, user.email, reset_token)
    
    # Send password reset email
    success = await email_service.send_password_reset_email(
        to_email=user.email,
        username=user.username,
        token=reset_token
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )
    
    return MessageResponse(message="Password reset link sent to your email")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Reset password using reset token
    """
    # Verify password reset token
    email = verify_token(reset_data.token, token_type="password_reset")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user by reset token
    user = user_service.get_user_by_reset_token(db, reset_data.token)
    if not user or user.email != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Update password
    success = user_service.update_password(db, user.id, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return MessageResponse(message="Password reset successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Logout user (client should remove tokens)
    """
    # Clear stored refresh token so it can no longer be used
    cleared = user_service.clear_refresh_token(db, current_user.email)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout user"
        )

    return MessageResponse(message="Logged out successfully")


@router.delete("/account", response_model=MessageResponse)
async def delete_account(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Deactivate user account
    """
    success = user_service.deactivate_user(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )
    
    return MessageResponse(message="Account deactivated successfully")
