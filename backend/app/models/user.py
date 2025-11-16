"""
User and Profile models
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

from .base import BaseModel


class UserRole(str, enum.Enum):
    """User roles enumeration"""
    GUEST = "guest"
    RENTER = "renter"  
    HOST = "host"
    ADMIN = "admin"


class KYCStatus(str, enum.Enum):
    """KYC status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class User(BaseModel):
    """User account model"""
    
    __tablename__ = "users"
    
    # Basic Info
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RENTER, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    
    # Security
    email_verified = Column(Boolean, default=False)
    last_login = Column(String(255), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chargers = relationship("Charger", back_populates="host", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="renter", foreign_keys="Booking.renter_id")
    reviews = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    payouts = relationship("Payout", back_populates="host")
    disputes_raised = relationship("Dispute", back_populates="raised_by_user", foreign_keys="Dispute.raised_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"


class Profile(BaseModel):
    """Extended user profile model"""
    
    __tablename__ = "profiles"
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Personal Info
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(String(10), nullable=True)  # YYYY-MM-DD format
    gender = Column(String(20), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    country = Column(String(100), default="India")
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="Asia/Kolkata")
    currency = Column(String(5), default="INR")
    
    # Notifications
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    
    # KYC Documents
    kyc_documents = Column(JSON, nullable=True)  # Store document URLs and metadata
    
    # Host specific fields
    host_rating = Column(String(5), default="0.0")  # Average rating as string
    host_rating_count = Column(Integer, default=0)
    response_time_minutes = Column(Integer, nullable=True)  # Average response time
    
    # Renter specific fields  
    vehicle_details = Column(JSON, nullable=True)  # Vehicle information
    preferred_connectors = Column(JSON, nullable=True)  # List of preferred connector types
    
    # Emergency Contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Social Links
    social_links = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<Profile {self.user_id}>"