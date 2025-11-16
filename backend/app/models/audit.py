"""
Audit logging model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class AuditLog(BaseModel):
    """Audit log for tracking critical operations"""
    
    __tablename__ = "audit_logs"
    
    # User reference (nullable for system operations)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Operation Details
    action = Column(String(100), nullable=False)  # login, create_booking, payment, etc.
    resource_type = Column(String(50), nullable=False)  # user, booking, charger, payment
    resource_id = Column(String(100), nullable=True)  # ID of affected resource
    
    # Context
    endpoint = Column(String(255), nullable=True)  # API endpoint
    method = Column(String(10), nullable=True)  # HTTP method
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Changes
    old_values = Column(JSON, nullable=True)  # Before state
    new_values = Column(JSON, nullable=True)  # After state
    
    # Status
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Additional Context
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)
    
    # Geolocation
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Risk Assessment
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    flags = Column(JSON, nullable=True)  # Security flags
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"