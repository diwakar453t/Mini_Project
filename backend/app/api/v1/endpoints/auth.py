"""
Authentication endpoints
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_current_user,
    decode_token,
)
from app.models.user import User, UserRole, Profile
from app.core.config import settings

router = APIRouter()


# Pydantic models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str = None
    role: UserRole = UserRole.RENTER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefresh(BaseModel):
    refresh_token: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str
    new_password: str


class PhoneVerification(BaseModel):
    phone: str
    otp: str


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user"""
    
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if user_data.phone and db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create user profile
    profile = Profile(
        user_id=user.id,
        country="India",
        currency="INR",
        timezone="Asia/Kolkata",
        preferred_language="en",
    )
    db.add(profile)
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """User login"""
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Update last login
    user.last_login = str(timedelta(seconds=0))  # Current timestamp
    user.failed_login_attempts = 0
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token"""
    
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user)) -> Any:
    """User logout"""
    # In a production system, you would typically:
    # 1. Blacklist the JWT token
    # 2. Clear session data
    # 3. Log the logout event
    
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Request password reset"""
    
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists for security
        return {"message": "If email exists, password reset instructions have been sent"}
    
    # Generate reset token (valid for 1 hour)
    reset_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(hours=1)
    )
    
    # TODO: Send reset email with token
    # For development, return token directly
    if settings.is_development:
        return {
            "message": "Password reset token generated",
            "reset_token": reset_token  # Remove in production
        }
    
    return {"message": "If email exists, password reset instructions have been sent"}


@router.post("/reset-password")
def reset_password(
    request: ResetPassword,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password with token"""
    
    payload = decode_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.failed_login_attempts = 0
    db.commit()
    
    return {"message": "Password successfully reset"}


@router.post("/verify-phone")
def verify_phone(
    request: PhoneVerification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Verify phone number with OTP"""
    
    # TODO: Implement actual OTP verification
    # For development, accept any 6-digit OTP starting with "123"
    if settings.is_development and request.otp.startswith("123") and len(request.otp) == 6:
        current_user.phone = request.phone
        current_user.phone_verified = True
        db.commit()
        return {"message": "Phone number verified successfully"}
    
    # TODO: Integrate with SMS provider (Twilio) for actual OTP verification
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid OTP"
    )