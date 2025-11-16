"""
User management endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import get_current_active_user, is_owner_or_admin
from app.models.user import User, Profile, UserRole, KYCStatus

router = APIRouter()


# Pydantic models
class UserProfile(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    is_verified: bool
    kyc_status: KYCStatus
    avatar_url: Optional[str]
    bio: Optional[str]
    city: Optional[str]
    state: Optional[str]
    host_rating: Optional[str]
    host_rating_count: Optional[int]
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    preferred_language: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None


class HostApplication(BaseModel):
    business_name: Optional[str] = None
    business_type: str
    pan_number: str
    aadhar_number: str
    business_address: str
    documents: List[str] = []  # URLs of uploaded documents


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user profile"""
    
    # Ensure profile exists
    if not current_user.profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(current_user)
    
    return {
        **current_user.dict(),
        **current_user.profile.dict(),
    }


@router.put("/me", response_model=UserProfile)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile"""
    
    # Update user fields
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.phone is not None:
        # Check if phone is already used
        existing_user = db.query(User).filter(
            User.phone == user_update.phone,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        current_user.phone = user_update.phone
        current_user.phone_verified = False  # Need to re-verify
    
    # Update or create profile
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    # Update profile fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if hasattr(profile, field) and value is not None:
            setattr(profile, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        **current_user.dict(),
        **profile.dict(),
    }


@router.get("/{user_id}", response_model=UserProfile)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get public user profile by ID"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return public profile only
    return {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "is_verified": user.is_verified,
        "avatar_url": user.profile.avatar_url if user.profile else None,
        "bio": user.profile.bio if user.profile else None,
        "city": user.profile.city if user.profile else None,
        "state": user.profile.state if user.profile else None,
        "host_rating": user.profile.host_rating if user.profile else "0.0",
        "host_rating_count": user.profile.host_rating_count if user.profile else 0,
        # Hide sensitive information
        "email": None,
        "phone": None,
        "kyc_status": None,
    }


@router.post("/hosts/apply")
def apply_for_host_role(
    application: HostApplication,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Apply to become a host"""
    
    if current_user.role == UserRole.HOST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a host"
        )
    
    # Update user role to HOST
    current_user.role = UserRole.HOST
    current_user.kyc_status = KYCStatus.SUBMITTED
    
    # Update profile with KYC documents
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    # Store KYC documents and business information
    profile.kyc_documents = {
        "business_name": application.business_name,
        "business_type": application.business_type,
        "pan_number": application.pan_number,
        "aadhar_number": application.aadhar_number,
        "business_address": application.business_address,
        "documents": application.documents,
        "submitted_at": str(db.query(func.now()).scalar()),
    }
    
    db.commit()
    
    return {
        "message": "Host application submitted successfully",
        "status": "pending_verification",
        "kyc_status": current_user.kyc_status,
    }


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Upload user avatar"""
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large (max 5MB)"
        )
    
    # TODO: Implement actual file upload to storage
    # For development, return a placeholder URL
    avatar_url = f"/uploads/avatars/{current_user.id}_{file.filename}"
    
    # Update user profile
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    profile.avatar_url = avatar_url
    db.commit()
    
    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url,
    }


@router.get("/{user_id}/chargers")
def get_user_chargers(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get chargers owned by a user"""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only show public chargers unless it's the owner or admin
    if is_owner_or_admin(user_id, current_user):
        chargers = user.chargers[skip:skip + limit]
    else:
        chargers = [c for c in user.chargers if c.is_active][skip:skip + limit]
    
    return {
        "chargers": chargers,
        "total": len(user.chargers),
        "skip": skip,
        "limit": limit,
    }


@router.get("/{user_id}/bookings")
def get_user_bookings(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get bookings made by a user"""
    
    # Only allow access to own bookings or admin
    if not is_owner_or_admin(user_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    bookings = user.bookings[skip:skip + limit]
    
    return {
        "bookings": bookings,
        "total": len(user.bookings),
        "skip": skip,
        "limit": limit,
    }