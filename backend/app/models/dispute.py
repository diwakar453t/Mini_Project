"""
Dispute resolution models
"""
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, JSON, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class DisputeStatus(str, enum.Enum):
    """Dispute status enumeration"""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    WAITING_RESPONSE = "waiting_response"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class DisputeCategory(str, enum.Enum):
    """Dispute category enumeration"""
    PAYMENT = "payment"
    CHARGER_ISSUE = "charger_issue"
    NO_SHOW = "no_show"
    OVERCHARGE = "overcharge"
    ACCESS_PROBLEM = "access_problem"
    CANCELLATION = "cancellation"
    HOST_BEHAVIOR = "host_behavior"
    TECHNICAL = "technical"
    OTHER = "other"


class DisputePriority(str, enum.Enum):
    """Dispute priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Dispute(BaseModel):
    """Dispute resolution model"""
    
    __tablename__ = "disputes"
    
    # References
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    raised_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin handling dispute
    
    # Dispute Details
    category = Column(Enum(DisputeCategory), nullable=False)
    priority = Column(Enum(DisputePriority), default=DisputePriority.MEDIUM)
    status = Column(Enum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    
    # Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Evidence
    evidence_files = Column(JSON, nullable=True)  # Array of file URLs
    screenshots = Column(JSON, nullable=True)  # Array of screenshot URLs
    
    # Financial Impact
    disputed_amount = Column(Float, nullable=True)
    refund_requested = Column(Float, nullable=True)
    refund_approved = Column(Float, nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolution_action = Column(String(100), nullable=True)  # refund, no_action, compensation
    admin_verdict = Column(Text, nullable=True)
    
    # Timeline
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Communication
    last_response_from = Column(String(20), nullable=True)  # renter, host, admin
    last_response_at = Column(DateTime(timezone=True), nullable=True)
    response_due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Escalation
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(Text, nullable=True)
    
    # Satisfaction
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating for resolution
    satisfaction_feedback = Column(Text, nullable=True)
    
    # Internal Notes
    internal_notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["payment_issue", "first_time_user"]
    
    # Relationships
    booking = relationship("Booking", back_populates="disputes")
    raised_by_user = relationship("User", back_populates="disputes_raised", foreign_keys=[raised_by])
    assigned_admin = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<Dispute {self.id} - {self.category}>"
    
    @property
    def charger(self):
        """Get the charger involved in the dispute"""
        return self.booking.charger if self.booking else None
    
    @property
    def host(self):
        """Get the host involved in the dispute"""
        return self.booking.charger.host if self.booking and self.booking.charger else None
    
    @property
    def renter(self):
        """Get the renter involved in the dispute"""
        return self.booking.renter if self.booking else None