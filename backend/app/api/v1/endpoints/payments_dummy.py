"""
Dummy payment endpoints for development and testing
These endpoints simulate payment flows without real payment processing
"""
from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import uuid
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user, get_current_admin
from app.core.config import settings
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.user import User, UserRole

router = APIRouter()

# Only enable dummy payments in development
def check_dummy_payments_enabled():
    if not getattr(settings, 'USE_DUMMY_PAYMENTS', False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dummy payment endpoints are disabled"
        )


# Pydantic models for dummy payments
class DummyPaymentCreate(BaseModel):
    booking_id: int
    payment_method: str  # "upi", "card", "wallet"
    simulate_delay: Optional[int] = 3  # Seconds
    simulate_network_latency: Optional[int] = 0  # Additional latency


class DummyPaymentComplete(BaseModel):
    booking_id: int
    status: str  # "SUCCESS", "FAILED"
    transaction_id: str
    failure_reason: Optional[str] = None


class DummyWebhookPayload(BaseModel):
    event_type: str  # "payment.success", "payment.failed", "payment.refund"
    booking_id: int
    transaction_id: str
    amount: float
    metadata: Optional[dict] = None


@router.post("/dummy/create")
def create_dummy_payment(
    payment_data: DummyPaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a dummy payment object for testing"""
    
    check_dummy_payments_enabled()
    
    # Get booking
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id,
        Booking.renter_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or access denied"
        )
    
    if booking.payment_status == PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed"
        )
    
    # Generate dummy payment ID
    payment_id = f"dummy_pay_{uuid.uuid4().hex[:12]}"
    
    # Store payment metadata for tracking
    payment_metadata = {
        "payment_id": payment_id,
        "booking_id": booking.id,
        "amount": booking.total_amount,
        "currency": "INR",
        "payment_method": payment_data.payment_method,
        "simulate_delay": payment_data.simulate_delay,
        "simulate_network_latency": payment_data.simulate_network_latency,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": current_user.id
    }
    
    # Update booking with payment tracking
    booking.payment_id = payment_id
    booking.payment_method = f"dummy_{payment_data.payment_method}"
    booking.payment_status = PaymentStatus.PROCESSING
    db.commit()
    
    # Generate appropriate redirect URL based on payment method
    redirect_url = f"/payments/dummy?booking_id={booking.id}&payment_id={payment_id}&amount={booking.total_amount}&method={payment_data.payment_method}"
    
    # Log the dummy transaction
    print(f"[DUMMY PAYMENT] Created payment {payment_id} for booking {booking.id}")
    
    return {
        "payment_id": payment_id,
        "redirect_url": redirect_url,
        "amount": booking.total_amount,
        "currency": "INR",
        "payment_method": payment_data.payment_method,
        "booking_id": booking.id,
        "metadata": payment_metadata
    }


@router.post("/dummy/complete")
def complete_dummy_payment(
    completion_data: DummyPaymentComplete,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Complete a dummy payment (success or failure)"""
    
    check_dummy_payments_enabled()
    
    # Get booking
    booking = db.query(Booking).filter(
        Booking.id == completion_data.booking_id,
        Booking.renter_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or access denied"
        )
    
    # Process payment completion
    if completion_data.status == "SUCCESS":
        booking.payment_status = PaymentStatus.COMPLETED
        booking.paid_amount = booking.total_amount
        
        # Auto-confirm booking if not already confirmed
        if booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_at = datetime.utcnow()
        
        # Create charging session if auto-accept
        if booking.charger.auto_accept_bookings:
            from app.models.booking import Session as ChargingSession, SessionStatus
            
            session = ChargingSession(
                booking_id=booking.id,
                session_id=f"dummy_session_{completion_data.transaction_id}",
                status=SessionStatus.NOT_STARTED
            )
            db.add(session)
        
        db.commit()
        
        # Log successful payment
        print(f"[DUMMY PAYMENT] SUCCESS: {completion_data.transaction_id} for booking {booking.id}")
        
        return {
            "message": "Payment completed successfully",
            "booking_id": booking.id,
            "booking_status": booking.status.value,
            "payment_status": booking.payment_status.value,
            "transaction_id": completion_data.transaction_id,
            "amount_paid": booking.paid_amount
        }
    
    else:  # FAILED
        booking.payment_status = PaymentStatus.FAILED
        db.commit()
        
        # Log failed payment
        print(f"[DUMMY PAYMENT] FAILED: {completion_data.transaction_id} for booking {booking.id} - {completion_data.failure_reason}")
        
        return {
            "message": "Payment failed",
            "booking_id": booking.id,
            "payment_status": booking.payment_status.value,
            "transaction_id": completion_data.transaction_id,
            "failure_reason": completion_data.failure_reason or "Payment processing failed"
        }


@router.post("/dummy/refund")
def create_dummy_refund(
    booking_id: int,
    amount: Optional[float] = None,
    reason: str = "Customer request",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a dummy refund"""
    
    check_dummy_payments_enabled()
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions (renter, host, or admin)
    if not (
        booking.renter_id == current_user.id or
        booking.charger.host_id == current_user.id or
        current_user.role == UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if booking.payment_status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot refund unpaid booking"
        )
    
    refund_amount = amount or booking.paid_amount
    refund_id = f"dummy_refund_{uuid.uuid4().hex[:12]}"
    
    # Update booking
    if refund_amount >= booking.paid_amount:
        booking.payment_status = PaymentStatus.REFUNDED
    else:
        booking.payment_status = PaymentStatus.PARTIAL_REFUND
    
    booking.refund_amount = refund_amount
    db.commit()
    
    # Log refund
    print(f"[DUMMY REFUND] {refund_id}: ₹{refund_amount} for booking {booking.id} - {reason}")
    
    return {
        "message": "Refund processed successfully",
        "refund_id": refund_id,
        "booking_id": booking.id,
        "amount": refund_amount,
        "reason": reason,
        "payment_status": booking.payment_status.value
    }


@router.post("/webhook/simulate")
def simulate_webhook(
    webhook_data: DummyWebhookPayload,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Simulate webhook payloads for testing (admin only)"""
    
    check_dummy_payments_enabled()
    
    booking = db.query(Booking).filter(Booking.id == webhook_data.booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Simulate webhook processing
    webhook_response = {
        "event_id": f"dummy_event_{uuid.uuid4().hex[:12]}",
        "event_type": webhook_data.event_type,
        "booking_id": webhook_data.booking_id,
        "transaction_id": webhook_data.transaction_id,
        "amount": webhook_data.amount,
        "processed_at": datetime.utcnow().isoformat(),
        "metadata": webhook_data.metadata
    }
    
    # Process different webhook types
    if webhook_data.event_type == "payment.success":
        booking.payment_status = PaymentStatus.COMPLETED
        booking.paid_amount = webhook_data.amount
        
        if booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_at = datetime.utcnow()
    
    elif webhook_data.event_type == "payment.failed":
        booking.payment_status = PaymentStatus.FAILED
    
    elif webhook_data.event_type == "payment.refund":
        booking.payment_status = PaymentStatus.REFUNDED
        booking.refund_amount = webhook_data.amount
        
        # Cancel booking if full refund
        if webhook_data.amount >= booking.total_amount:
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.utcnow()
            booking.cancellation_reason = "Payment refunded"
    
    elif webhook_data.event_type == "payment.chargeback":
        booking.payment_status = PaymentStatus.FAILED
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = "Payment disputed"
    
    db.commit()
    
    # Log webhook simulation
    print(f"[DUMMY WEBHOOK] {webhook_data.event_type}: {webhook_data.transaction_id} for booking {booking.id}")
    
    return webhook_response


@router.get("/dummy/status/{booking_id}")
def get_dummy_payment_status(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get payment status for a booking"""
    
    check_dummy_payments_enabled()
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.renter_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or access denied"
        )
    
    return {
        "booking_id": booking.id,
        "payment_status": booking.payment_status.value,
        "payment_method": booking.payment_method,
        "payment_id": booking.payment_id,
        "total_amount": booking.total_amount,
        "paid_amount": booking.paid_amount,
        "refund_amount": booking.refund_amount,
        "currency": booking.currency
    }


@router.get("/dummy/test-accounts")
def get_test_accounts(
    current_user: User = Depends(get_current_admin)
) -> Any:
    """Get test account information for dummy payments"""
    
    check_dummy_payments_enabled()
    
    return {
        "test_cards": {
            "success": {
                "number": "4111 1111 1111 1111",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test Success"
            },
            "failure": {
                "number": "4000 0000 0000 0002",
                "expiry": "12/25", 
                "cvv": "456",
                "name": "Test Failure"
            }
        },
        "test_upis": {
            "success": "success@paytm",
            "failure": "failure@paytm"
        },
        "test_wallets": {
            "success": "wallet_success_123",
            "failure": "wallet_failure_456"
        },
        "simulation_options": {
            "delays": [1, 3, 5, 10],
            "network_latency": [0, 500, 1000, 2000],
            "failure_rates": [0, 10, 25, 50]
        }
    }