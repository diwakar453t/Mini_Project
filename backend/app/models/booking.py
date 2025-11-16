"""
Booking and Session models
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text, JSON, Float, DateTime, func
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class BookingStatus(str, enum.Enum):
    """Booking status enumeration"""
    PENDING = "pending"        # Waiting for host approval
    CONFIRMED = "confirmed"    # Approved and payment successful
    ACTIVE = "active"         # Currently in progress
    COMPLETED = "completed"   # Successfully completed
    CANCELLED = "cancelled"   # Cancelled by user/host
    FAILED = "failed"         # Payment or technical failure
    NO_SHOW = "no_show"       # User didn't show up
    EXPIRED = "expired"       # Booking time passed


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"


class SessionStatus(str, enum.Enum):
    """Charging session status"""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ERROR = "error"


class Booking(BaseModel):
    """Booking/reservation model"""
    
    __tablename__ = "bookings"
    
    # References
    charger_id = Column(Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False)
    renter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Booking Details
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    
    # Status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Pricing & Payment
    pricing_type = Column(String(20), nullable=False)  # per_hour, per_kwh, flat_rate
    unit_price = Column(Float, nullable=False)  # Price per unit
    estimated_cost = Column(Float, nullable=False)  # Initial estimate
    final_cost = Column(Float, nullable=True)  # Actual cost after completion
    
    # Payment breakdown
    subtotal = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    taxes = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    
    # Payment Details
    currency = Column(String(5), default="INR")
    payment_method = Column(String(50), nullable=True)  # razorpay, stripe, upi
    payment_id = Column(String(255), nullable=True)  # External payment ID
    razorpay_order_id = Column(String(255), nullable=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    
    # Booking Metadata
    booking_code = Column(String(20), unique=True, nullable=False)  # 6-8 character code
    qr_code_url = Column(String(500), nullable=True)
    
    # Vehicle Information
    vehicle_info = Column(JSON, nullable=True)  # Vehicle details for this booking
    
    # Access & Instructions
    access_code = Column(String(50), nullable=True)  # Charger access code
    special_instructions = Column(Text, nullable=True)
    
    # Timing & Status Updates
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    started_charging_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Cancellation
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(String(20), nullable=True)  # renter, host, system, admin
    refund_amount = Column(Float, nullable=True)
    
    # Extension & Overstay
    extended_times = Column(Integer, default=0)
    overstay_minutes = Column(Integer, default=0)
    overstay_fee = Column(Float, default=0.0)
    
    # Communication
    host_notified = Column(Boolean, default=False)
    renter_notified = Column(Boolean, default=False)
    
    # Notes & History
    host_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    status_history = Column(JSON, nullable=True)  # Track all status changes
    
    # Relationships
    charger = relationship("Charger", back_populates="bookings")
    renter = relationship("User", back_populates="bookings", foreign_keys=[renter_id])
    session = relationship("Session", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    review = relationship("Review", back_populates="booking", uselist=False)
    disputes = relationship("Dispute", back_populates="booking")
    
    def __repr__(self):
        return f"<Booking {self.booking_code}>"
    
    @property
    def host(self):
        """Get the host (charger owner) for this booking"""
        return self.charger.host if self.charger else None
    
    @property
    def duration_hours(self):
        """Calculate booking duration in hours"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0


class Session(BaseModel):
    """Actual charging session model"""
    
    __tablename__ = "sessions"
    
    # Reference
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Session Details
    session_id = Column(String(100), unique=True, nullable=False)  # External session ID
    status = Column(Enum(SessionStatus), default=SessionStatus.NOT_STARTED, nullable=False)
    
    # Timing
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)
    actual_duration_minutes = Column(Integer, default=0)
    
    # Energy & Power
    energy_delivered_kwh = Column(Float, default=0.0)
    peak_power_kw = Column(Float, default=0.0)
    average_power_kw = Column(Float, default=0.0)
    
    # Charging Progress
    initial_battery_percent = Column(Integer, nullable=True)
    final_battery_percent = Column(Integer, nullable=True)
    target_battery_percent = Column(Integer, nullable=True)
    
    # Financial
    energy_cost = Column(Float, default=0.0)
    time_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    host_payout = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    
    # Session Events
    pause_count = Column(Integer, default=0)
    total_pause_minutes = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Termination
    termination_reason = Column(String(100), nullable=True)  # user_stopped, target_reached, timeout, error
    terminated_by = Column(String(20), nullable=True)  # user, host, system, automatic
    
    # Telemetry Summary
    min_voltage = Column(Float, nullable=True)
    max_voltage = Column(Float, nullable=True)
    min_current = Column(Float, nullable=True)
    max_current = Column(Float, nullable=True)
    max_temperature = Column(Float, nullable=True)
    
    # Quality Metrics
    efficiency_percent = Column(Float, nullable=True)  # Energy transfer efficiency
    uptime_percent = Column(Float, nullable=True)  # Session uptime
    
    # Session Events Log
    events_log = Column(JSON, nullable=True)  # Detailed event timeline
    
    # Relationships
    booking = relationship("Booking", back_populates="session")
    
    def __repr__(self):
        return f"<Session {self.session_id}>"
    
    @property
    def charger(self):
        """Get the charger for this session"""
        return self.booking.charger if self.booking else None
    
    @property
    def renter(self):
        """Get the renter for this session"""  
        return self.booking.renter if self.booking else None