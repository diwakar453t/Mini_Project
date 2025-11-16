"""
Booking management endpoints
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
import uuid
import qrcode
import io
import base64

from app.core.database import get_db
from app.core.security import get_current_active_user, is_owner_or_admin
from app.core.config import settings
from app.models.booking import Booking, Session as ChargingSession, BookingStatus, PaymentStatus, SessionStatus
from app.models.charger import Charger, ChargerPricing
from app.models.user import User, UserRole
from app.services.booking_service import booking_service, BookingConflictError

router = APIRouter()


# Pydantic models
class BookingCreate(BaseModel):
    charger_id: int
    start_time: datetime
    end_time: datetime
    vehicle_info: Optional[dict] = {}
    special_instructions: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    charger_id: int
    renter_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    payment_status: PaymentStatus
    booking_code: str
    total_amount: float
    paid_amount: float
    currency: str
    qr_code_url: Optional[str]
    access_code: Optional[str]
    
    class Config:
        from_attributes = True


class BookingUpdate(BaseModel):
    end_time: Optional[datetime] = None
    special_instructions: Optional[str] = None
    status: Optional[BookingStatus] = None


class ExtendBooking(BaseModel):
    additional_minutes: int


class CancelBooking(BaseModel):
    reason: str


def generate_booking_code() -> str:
    """Generate unique booking code"""
    return str(uuid.uuid4()).replace('-', '').upper()[:8]


def calculate_booking_cost(
    charger: Charger,
    start_time: datetime,
    end_time: datetime,
    db: Session
) -> dict:
    """Calculate booking cost based on pricing model"""
    
    pricing = db.query(ChargerPricing).filter(
        ChargerPricing.charger_id == charger.id
    ).first()
    
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pricing not configured for this charger"
        )
    
    duration_hours = (end_time - start_time).total_seconds() / 3600
    duration_minutes = duration_hours * 60
    
    # Validate session constraints
    if duration_minutes < pricing.min_session_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum session duration is {pricing.min_session_minutes} minutes"
        )
    
    if duration_minutes > pricing.max_session_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum session duration is {pricing.max_session_minutes} minutes"
        )
    
    # Calculate base cost
    if pricing.pricing_type.value == "per_hour":
        subtotal = duration_hours * pricing.price_value
    elif pricing.pricing_type.value == "per_kwh":
        # For per_kwh pricing, estimate based on charger power
        estimated_kwh = duration_hours * charger.max_power_kw * 0.8  # 80% efficiency
        subtotal = estimated_kwh * pricing.price_value
    else:  # flat_rate
        subtotal = pricing.price_value
    
    # Apply time-based multipliers
    # TODO: Implement peak hours and weekend pricing
    
    # Add booking fee
    booking_fee = pricing.booking_fee
    platform_fee = subtotal * (settings.PLATFORM_COMMISSION_RATE / 100)
    
    total_amount = subtotal + booking_fee + platform_fee
    
    return {
        "subtotal": round(subtotal, 2),
        "booking_fee": round(booking_fee, 2),
        "platform_fee": round(platform_fee, 2),
        "total_amount": round(total_amount, 2),
        "estimated_duration_minutes": int(duration_minutes),
        "pricing_type": pricing.pricing_type.value,
        "unit_price": pricing.price_value,
    }


def check_availability(
    charger_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
    db: Session = None
) -> bool:
    """Check if charger is available for the given time slot"""
    
    # Check for overlapping bookings
    query = db.query(Booking).filter(
        Booking.charger_id == charger_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
        or_(
            and_(Booking.start_time <= start_time, Booking.end_time > start_time),
            and_(Booking.start_time < end_time, Booking.end_time >= end_time),
            and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
        )
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    
    conflicting_bookings = query.count()
    return conflicting_bookings == 0


def generate_qr_code(booking_code: str) -> str:
    """Generate QR code for booking"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{settings.FRONTEND_URL}/booking/{booking_code}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{qr_code_data}"


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new booking with atomic availability check"""
    
    try:
        # Use the booking service for atomic creation
        booking = booking_service.create_booking_atomic(
            db=db,
            charger_id=booking_data.charger_id,
            renter_id=current_user.id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            vehicle_info=booking_data.vehicle_info,
            special_instructions=booking_data.special_instructions
        )
        
        # Generate QR code
        booking.qr_code_url = generate_qr_code(booking.booking_code)
        db.commit()
        
        return booking
        
    except BookingConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[BookingResponse])
def get_user_bookings(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[BookingStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user's bookings"""
    
    query = db.query(Booking).filter(Booking.renter_id == current_user.id)
    
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    
    query = query.order_by(Booking.created_at.desc())
    total = query.count()
    bookings = query.offset(skip).limit(limit).all()
    
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get booking details"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check access permissions (renter, host, or admin)
    if not (
        booking.renter_id == current_user.id or
        booking.charger.host_id == current_user.id or
        current_user.role == UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return booking


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update booking (extend time, etc.)"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    is_renter = booking.renter_id == current_user.id
    is_host = booking.charger.host_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not (is_renter or is_host or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Handle different update types
    if booking_update.end_time and booking_update.end_time != booking.end_time:
        if not is_renter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only renter can extend booking"
            )
        
        # Check if extension is possible
        if not check_availability(
            booking.charger_id,
            booking.end_time,
            booking_update.end_time,
            exclude_booking_id=booking.id,
            db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Charger is not available for extended time"
            )
        
        # Recalculate cost
        cost_breakdown = calculate_booking_cost(
            booking.charger,
            booking.start_time,
            booking_update.end_time,
            db
        )
        
        booking.end_time = booking_update.end_time
        booking.extended_times += 1
        for key, value in cost_breakdown.items():
            setattr(booking, key, value)
    
    # Status updates (host or admin only)
    if booking_update.status and booking_update.status != booking.status:
        if not (is_host or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only host or admin can update booking status"
            )
        
        booking.status = booking_update.status
        if booking_update.status == BookingStatus.CONFIRMED:
            booking.confirmed_at = datetime.utcnow()
    
    # Other updates
    if booking_update.special_instructions is not None:
        if not is_renter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only renter can update instructions"
            )
        booking.special_instructions = booking_update.special_instructions
    
    db.commit()
    db.refresh(booking)
    
    return booking


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    cancel_data: CancelBooking,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Cancel a booking"""
    
    try:
        # Determine who is cancelling
        cancelled_by = "renter"
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if booking and booking.charger.host_id == current_user.id:
            cancelled_by = "host"
        elif current_user.role == UserRole.ADMIN:
            cancelled_by = "admin"
        
        # Use booking service for cancellation
        refund_calculation = booking_service.cancel_booking(
            db=db,
            booking_id=booking_id,
            user_id=current_user.id,
            reason=cancel_data.reason,
            cancelled_by=cancelled_by
        )
        
        return {
            "message": "Booking cancelled successfully",
            **refund_calculation
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{booking_id}/checkin")
def checkin_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Check in to a booking (start session)"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Only renter can check in
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the renter can check in"
        )
    
    # Validate booking status and timing
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must be confirmed to check in"
        )
    
    now = datetime.utcnow()
    if now < booking.start_time - timedelta(minutes=15):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-in not allowed more than 15 minutes before start time"
        )
    
    if now > booking.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has expired"
        )
    
    # Update booking status
    booking.status = BookingStatus.ACTIVE
    booking.checked_in_at = now
    booking.started_charging_at = now
    
    # Create charging session
    session = ChargingSession(
        booking_id=booking.id,
        session_id=f"session_{booking.id}_{int(now.timestamp())}",
        status=SessionStatus.ACTIVE,
        actual_start_time=now,
    )
    
    db.add(session)
    db.commit()
    
    return {
        "message": "Successfully checked in",
        "session_id": session.session_id,
        "access_code": booking.access_code,
    }