"""
Charger, ChargerPricing, and ChargerTelemetry models
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text, JSON, Float, ARRAY, DateTime
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ConnectorType(str, enum.Enum):
    """Charger connector types"""
    CCS = "ccs"
    CHADEMO = "chademo" 
    NACS = "nacs"
    TYPE2 = "type2"
    TYPE1 = "type1"


class ChargerType(str, enum.Enum):
    """Charger power levels"""
    LEVEL1 = "level1"  # Slow AC charging (3.7kW)
    LEVEL2 = "level2"  # Fast AC charging (7kW-22kW)
    DC_FAST = "dc_fast"  # DC Fast charging (50kW+)


class ChargerStatus(str, enum.Enum):
    """Charger operational status"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    FAULT = "fault"


class PricingType(str, enum.Enum):
    """Pricing models"""
    PER_HOUR = "per_hour"
    PER_KWH = "per_kwh"
    FLAT_RATE = "flat_rate"


class Charger(BaseModel):
    """Charger listing model"""
    
    __tablename__ = "chargers"
    
    # Owner
    host_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Location
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Charger Specifications
    connector_type = Column(Enum(ConnectorType), nullable=False)
    charger_type = Column(Enum(ChargerType), nullable=False)
    max_power_kw = Column(Float, nullable=False)
    voltage = Column(Integer, nullable=True)
    current_rating = Column(Integer, nullable=True)
    
    # Images and Media
    images = Column(ARRAY(String), nullable=True)  # Array of image URLs
    cover_image = Column(String(500), nullable=True)  # Main display image
    
    # Amenities and Features
    amenities = Column(JSON, nullable=True)  # {"wifi": true, "parking": true, "restroom": false}
    features = Column(JSON, nullable=True)   # {"cable_provided": true, "weatherproof": true}
    
    # Availability 
    availability_schedule = Column(JSON, nullable=True)  # Weekly schedule
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    auto_accept_bookings = Column(Boolean, default=False)
    
    # Operational Status
    current_status = Column(Enum(ChargerStatus), default=ChargerStatus.AVAILABLE)
    last_maintenance = Column(DateTime, nullable=True)
    
    # Access Instructions
    access_instructions = Column(Text, nullable=True)
    access_code = Column(String(50), nullable=True)
    host_contact_required = Column(Boolean, default=False)
    
    # Statistics
    total_bookings = Column(Integer, default=0)
    total_energy_delivered = Column(Float, default=0.0)  # kWh
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Relationships
    host = relationship("User", back_populates="chargers")
    pricing = relationship("ChargerPricing", back_populates="charger", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="charger", cascade="all, delete-orphan")
    telemetry = relationship("ChargerTelemetry", back_populates="charger", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="charger")
    
    def __repr__(self):
        return f"<Charger {self.title}>"


class ChargerPricing(BaseModel):
    """Charger pricing configuration"""
    
    __tablename__ = "charger_pricing"
    
    # Foreign Key
    charger_id = Column(Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False)
    
    # Pricing Model
    pricing_type = Column(Enum(PricingType), nullable=False)
    price_value = Column(Float, nullable=False)  # Price in INR
    currency = Column(String(5), default="INR")
    
    # Session Constraints
    min_session_minutes = Column(Integer, default=30)
    max_session_minutes = Column(Integer, default=480)  # 8 hours
    
    # Time-based Pricing
    peak_hours_start = Column(String(5), nullable=True)  # "09:00"
    peak_hours_end = Column(String(5), nullable=True)    # "18:00"
    peak_price_multiplier = Column(Float, default=1.0)
    
    # Weekend Pricing
    weekend_price_multiplier = Column(Float, default=1.0)
    
    # Cancellation Policy
    cancellation_policy = Column(JSON, nullable=True)
    
    # Booking Constraints
    advance_booking_hours = Column(Integer, default=168)  # 1 week
    same_day_booking = Column(Boolean, default=True)
    
    # Additional Fees
    booking_fee = Column(Float, default=0.0)
    overstay_fee_per_hour = Column(Float, default=50.0)
    late_cancellation_fee = Column(Float, default=100.0)
    
    # Relationships
    charger = relationship("Charger", back_populates="pricing")
    
    def __repr__(self):
        return f"<ChargerPricing {self.charger_id} - {self.pricing_type}>"


class ChargerTelemetry(BaseModel):
    """Real-time charger telemetry data"""
    
    __tablename__ = "charger_telemetry"
    
    # Foreign Key
    charger_id = Column(Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False)
    
    # Telemetry Data
    timestamp = Column(DateTime, nullable=False)
    status = Column(Enum(ChargerStatus), nullable=False)
    power_output_kw = Column(Float, default=0.0)
    voltage_v = Column(Float, nullable=True)
    current_a = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    
    # Session Data (if charging)
    session_id = Column(String(100), nullable=True)  # Current charging session
    energy_delivered_kwh = Column(Float, default=0.0)
    session_duration_minutes = Column(Integer, default=0)
    
    # Error Information
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Network Status
    connectivity_status = Column(String(20), default="online")  # online, offline, poor
    signal_strength = Column(Integer, nullable=True)  # 0-100
    
    # Additional Metadata
    firmware_version = Column(String(50), nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Relationships
    charger = relationship("Charger", back_populates="telemetry")
    
    def __repr__(self):
        return f"<ChargerTelemetry {self.charger_id} - {self.status}>"