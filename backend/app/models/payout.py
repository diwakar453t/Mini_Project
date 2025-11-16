"""
Payout and financial models
"""
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, JSON, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class PayoutStatus(str, enum.Enum):
    """Payout status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class PayoutMethod(str, enum.Enum):
    """Payout method enumeration"""
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    DIGITAL_WALLET = "digital_wallet"
    RAZORPAY_PAYOUT = "razorpay_payout"


class Payout(BaseModel):
    """Host payout model"""
    
    __tablename__ = "payouts"
    
    # Reference
    host_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Payout Details
    amount = Column(Float, nullable=False)
    currency = Column(String(5), default="INR")
    payout_status = Column(Enum(PayoutStatus), default=PayoutStatus.PENDING, nullable=False)
    payout_method = Column(Enum(PayoutMethod), nullable=False)
    
    # Payment Details
    bank_account_details = Column(JSON, nullable=True)  # Encrypted bank details
    upi_id = Column(String(255), nullable=True)
    digital_wallet_details = Column(JSON, nullable=True)
    
    # External References
    razorpay_payout_id = Column(String(255), nullable=True)
    bank_reference_number = Column(String(255), nullable=True)
    
    # Timing
    initiated_at = Column(DateTime(timezone=True), nullable=True)
    processing_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Period Covered
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Earnings Breakdown
    gross_earnings = Column(Float, nullable=False)
    platform_commission = Column(Float, nullable=False)
    tax_deducted = Column(Float, default=0.0)
    adjustments = Column(Float, default=0.0)  # Refunds, chargebacks, etc.
    net_amount = Column(Float, nullable=False)
    
    # Session Summary
    total_sessions = Column(Integer, nullable=False)
    total_energy_kwh = Column(Float, nullable=False)
    total_session_hours = Column(Float, nullable=False)
    
    # Status Details
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Notes & Communication
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Tax Information
    tax_year = Column(Integer, nullable=True)
    tax_quarter = Column(Integer, nullable=True)
    tds_amount = Column(Float, default=0.0)  # Tax Deducted at Source
    
    # Relationships
    host = relationship("User", back_populates="payouts")
    
    def __repr__(self):
        return f"<Payout {self.id} - ₹{self.amount}>"
    
    @property
    def commission_rate(self):
        """Calculate commission rate percentage"""
        if self.gross_earnings > 0:
            return round((self.platform_commission / self.gross_earnings) * 100, 2)
        return 0