"""
Booking service with atomic availability checks and transaction handling
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
import logging

from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.charger import Charger, ChargerPricing
from app.models.user import User
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class BookingConflictError(Exception):
    """Raised when booking conflicts with existing reservations"""
    pass


class BookingService:
    """Service for handling booking operations with atomic transactions"""
    
    def __init__(self):
        pass
    
    def check_availability(
        self,
        db: Session,
        charger_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """
        Check if charger is available for the given time slot
        Uses atomic database queries to prevent race conditions
        """
        
        # Buffer time to prevent back-to-back bookings
        buffer_minutes = 15
        buffer_start = start_time - timedelta(minutes=buffer_minutes)
        buffer_end = end_time + timedelta(minutes=buffer_minutes)
        
        query = db.query(Booking).filter(
            Booking.charger_id == charger_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED,
                BookingStatus.ACTIVE,
                BookingStatus.PENDING
            ]),
            # Check for any overlap with buffer
            or_(
                # New booking starts during existing booking (with buffer)
                and_(
                    Booking.start_time <= buffer_start,
                    Booking.end_time > buffer_start
                ),
                # New booking ends during existing booking (with buffer)
                and_(
                    Booking.start_time < buffer_end,
                    Booking.end_time >= buffer_end
                ),
                # New booking completely contains existing booking
                and_(
                    Booking.start_time >= buffer_start,
                    Booking.end_time <= buffer_end
                ),
                # Existing booking completely contains new booking
                and_(
                    Booking.start_time <= buffer_start,
                    Booking.end_time >= buffer_end
                )
            )
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        
        conflicting_bookings = query.count()
        return conflicting_bookings == 0
    
    def calculate_pricing(
        self,
        db: Session,
        charger_id: int,
        start_time: datetime,
        end_time: datetime,
        vehicle_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate pricing for a booking with detailed breakdown"""
        
        charger = db.query(Charger).filter(Charger.id == charger_id).first()
        if not charger:
            raise ValueError("Charger not found")
        
        pricing = db.query(ChargerPricing).filter(
            ChargerPricing.charger_id == charger_id
        ).first()
        
        if not pricing:
            raise ValueError("Pricing not configured for this charger")
        
        duration_hours = (end_time - start_time).total_seconds() / 3600
        duration_minutes = duration_hours * 60
        
        # Validate session constraints
        if duration_minutes < pricing.min_session_minutes:
            raise ValueError(
                f"Minimum session duration is {pricing.min_session_minutes} minutes"
            )
        
        if duration_minutes > pricing.max_session_minutes:
            raise ValueError(
                f"Maximum session duration is {pricing.max_session_minutes} minutes"
            )
        
        # Calculate base cost
        if pricing.pricing_type.value == "per_hour":
            subtotal = duration_hours * pricing.price_value
            estimated_kwh = duration_hours * charger.max_power_kw * 0.8  # 80% efficiency
        elif pricing.pricing_type.value == "per_kwh":
            estimated_kwh = duration_hours * charger.max_power_kw * 0.8
            subtotal = estimated_kwh * pricing.price_value
        else:  # flat_rate
            subtotal = pricing.price_value
            estimated_kwh = duration_hours * charger.max_power_kw * 0.8
        
        # Apply time-based multipliers
        price_multiplier = 1.0
        
        # Peak hours multiplier
        if pricing.peak_hours_start and pricing.peak_hours_end:
            peak_start_hour = int(pricing.peak_hours_start.split(':')[0])
            peak_end_hour = int(pricing.peak_hours_end.split(':')[0])
            booking_start_hour = start_time.hour
            
            if peak_start_hour <= booking_start_hour <= peak_end_hour:
                price_multiplier *= pricing.peak_price_multiplier
        
        # Weekend multiplier
        if start_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            price_multiplier *= pricing.weekend_price_multiplier
        
        subtotal *= price_multiplier
        
        # Add fees
        booking_fee = pricing.booking_fee
        platform_commission_rate = 0.15  # 15% platform commission
        platform_fee = subtotal * platform_commission_rate
        
        # GST calculation (18% on platform fee in India)
        gst_rate = 0.18
        gst_amount = platform_fee * gst_rate
        
        total_amount = subtotal + booking_fee + platform_fee + gst_amount
        
        return {
            "duration_hours": round(duration_hours, 2),
            "duration_minutes": int(duration_minutes),
            "estimated_kwh": round(estimated_kwh, 2),
            "pricing_type": pricing.pricing_type.value,
            "unit_price": pricing.price_value,
            "price_multiplier": price_multiplier,
            "subtotal": round(subtotal, 2),
            "booking_fee": round(booking_fee, 2),
            "platform_fee": round(platform_fee, 2),
            "gst_amount": round(gst_amount, 2),
            "total_amount": round(total_amount, 2),
            "host_payout": round(subtotal, 2),  # Host gets subtotal minus commission
            "commission_amount": round(platform_fee, 2)
        }
    
    def create_booking_atomic(
        self,
        db: Session,
        charger_id: int,
        renter_id: int,
        start_time: datetime,
        end_time: datetime,
        vehicle_info: Optional[Dict[str, Any]] = None,
        special_instructions: Optional[str] = None
    ) -> Booking:
        """
        Create a booking with atomic availability check and database constraint enforcement
        Uses SELECT FOR UPDATE to prevent race conditions
        """
        
        # Start transaction with row-level locking
        try:
            # Lock the charger row to prevent concurrent bookings
            charger = db.query(Charger).filter(
                Charger.id == charger_id,
                Charger.is_active == True
            ).with_for_update().first()
            
            if not charger:
                raise ValueError("Charger not found or inactive")
            
            # Double-check availability within the transaction
            if not self.check_availability(db, charger_id, start_time, end_time):
                raise BookingConflictError(
                    "Charger is not available for the selected time slot"
                )
            
            # Calculate pricing
            pricing_breakdown = self.calculate_pricing(
                db, charger_id, start_time, end_time, vehicle_info
            )
            
            # Generate unique booking code
            booking_code = self._generate_booking_code(db)
            
            # Create booking
            booking = Booking(
                charger_id=charger_id,
                renter_id=renter_id,
                start_time=start_time,
                end_time=end_time,
                estimated_duration_minutes=pricing_breakdown["duration_minutes"],
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                booking_code=booking_code,
                pricing_type=pricing_breakdown["pricing_type"],
                unit_price=pricing_breakdown["unit_price"],
                estimated_cost=pricing_breakdown["subtotal"],
                subtotal=pricing_breakdown["subtotal"],
                platform_fee=pricing_breakdown["platform_fee"],
                taxes=pricing_breakdown["gst_amount"],
                total_amount=pricing_breakdown["total_amount"],
                currency="INR",
                vehicle_info=vehicle_info,
                special_instructions=special_instructions
            )
            
            # Auto-confirm if host allows
            if charger.auto_accept_bookings:
                booking.status = BookingStatus.CONFIRMED
                booking.confirmed_at = datetime.utcnow()
            
            db.add(booking)
            
            # This will raise IntegrityError if there's a constraint violation
            db.commit()
            db.refresh(booking)
            
            logger.info(f"Booking {booking.booking_code} created successfully")
            
            return booking
            
        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Booking conflict detected: {e}")
            raise BookingConflictError(
                "This time slot is no longer available. Please select a different time."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create booking: {e}")
            raise
    
    def extend_booking(
        self,
        db: Session,
        booking_id: int,
        new_end_time: datetime,
        user_id: int
    ) -> Booking:
        """
        Extend an existing booking with availability check
        """
        
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.renter_id == user_id
        ).first()
        
        if not booking:
            raise ValueError("Booking not found or access denied")
        
        if booking.status not in [BookingStatus.CONFIRMED, BookingStatus.ACTIVE]:
            raise ValueError("Cannot extend booking in current status")
        
        if new_end_time <= booking.end_time:
            raise ValueError("New end time must be after current end time")
        
        # Check availability for extension period
        if not self.check_availability(
            db, 
            booking.charger_id, 
            booking.end_time, 
            new_end_time,
            exclude_booking_id=booking.id
        ):
            raise BookingConflictError(
                "Cannot extend booking - time slot not available"
            )
        
        # Calculate additional cost
        additional_pricing = self.calculate_pricing(
            db,
            booking.charger_id,
            booking.end_time,
            new_end_time,
            booking.vehicle_info
        )
        
        # Update booking
        booking.end_time = new_end_time
        booking.extended_times += 1
        booking.estimated_duration_minutes = int(
            (new_end_time - booking.start_time).total_seconds() / 60
        )
        booking.total_amount += additional_pricing["total_amount"]
        
        db.commit()
        db.refresh(booking)
        
        logger.info(f"Booking {booking.booking_code} extended to {new_end_time}")
        
        return booking
    
    def cancel_booking(
        self,
        db: Session,
        booking_id: int,
        user_id: int,
        reason: str,
        cancelled_by: str = "renter"
    ) -> Dict[str, Any]:
        """
        Cancel a booking and calculate refund amount
        """
        
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            raise ValueError("Booking not found")
        
        # Check permissions
        if cancelled_by == "renter" and booking.renter_id != user_id:
            raise ValueError("Access denied")
        elif cancelled_by == "host" and booking.charger.host_id != user_id:
            raise ValueError("Access denied")
        
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValueError("Cannot cancel booking in current status")
        
        # Calculate refund
        refund_calculation = self._calculate_refund(booking)
        
        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.cancelled_by = cancelled_by
        booking.refund_amount = refund_calculation["refund_amount"]
        
        db.commit()
        
        logger.info(f"Booking {booking.booking_code} cancelled by {cancelled_by}")
        
        return refund_calculation
    
    def _generate_booking_code(self, db: Session) -> str:
        """Generate unique booking code"""
        import random
        import string
        
        while True:
            code = 'BK' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            existing = db.query(Booking).filter(Booking.booking_code == code).first()
            if not existing:
                return code
    
    def _calculate_refund(self, booking: Booking) -> Dict[str, Any]:
        """Calculate refund amount based on cancellation policy"""
        
        now = datetime.utcnow()
        time_to_start = (booking.start_time - now).total_seconds() / 3600  # hours
        
        cancellation_fee = 0.0
        refund_percentage = 100.0
        
        # Get cancellation policy from pricing
        if booking.charger and booking.charger.pricing:
            pricing = booking.charger.pricing[0]  # Assuming one pricing per charger
            
            # Apply late cancellation fee if within cancellation window
            cancellation_window_hours = 2  # Default 2 hours
            if time_to_start < cancellation_window_hours:
                cancellation_fee = pricing.late_cancellation_fee
                refund_percentage = 50.0  # 50% refund for late cancellation
        
        # Calculate refund
        if booking.paid_amount > 0:
            refund_before_fee = (booking.paid_amount * refund_percentage) / 100
            refund_amount = max(0, refund_before_fee - cancellation_fee)
        else:
            refund_amount = 0.0
        
        return {
            "refund_amount": round(refund_amount, 2),
            "cancellation_fee": round(cancellation_fee, 2),
            "refund_percentage": refund_percentage,
            "time_to_start_hours": round(time_to_start, 2)
        }
    
    def get_availability_slots(
        self,
        db: Session,
        charger_id: int,
        date: datetime,
        slot_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a specific date"""
        
        charger = db.query(Charger).filter(Charger.id == charger_id).first()
        if not charger:
            raise ValueError("Charger not found")
        
        # Generate time slots for the day (6 AM to 10 PM)
        slots = []
        start_of_day = date.replace(hour=6, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=22, minute=0, second=0, microsecond=0)
        
        current_time = start_of_day
        while current_time < end_of_day:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)
            
            # Check if slot is available
            available = self.check_availability(
                db, charger_id, current_time, slot_end
            )
            
            slots.append({
                "start_time": current_time.isoformat(),
                "end_time": slot_end.isoformat(),
                "available": available
            })
            
            current_time = slot_end
        
        return slots


# Create singleton instance
booking_service = BookingService()