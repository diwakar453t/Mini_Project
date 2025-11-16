"""
Payment processing endpoints
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import razorpay
import stripe
import hmac
import hashlib
import json

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.user import User

router = APIRouter()

# Initialize payment clients
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

stripe.api_key = settings.STRIPE_SECRET_KEY


# Pydantic models
class PaymentCreate(BaseModel):
    booking_id: int
    payment_method: str  # razorpay, stripe, upi


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: Optional[str]
    amount: float
    currency: str
    payment_url: Optional[str]
    upi_intent: Optional[str]


class PaymentConfirm(BaseModel):
    payment_id: str
    order_id: str
    signature: str


class RefundRequest(BaseModel):
    booking_id: int
    amount: Optional[float] = None
    reason: str


def generate_upi_deep_link(
    amount: float, 
    booking_code: str, 
    merchant_upi: str = "merchant@paytm"
) -> str:
    """Generate UPI deep link for payment"""
    
    # UPI intent parameters
    pa = merchant_upi  # Merchant UPI ID
    pn = "ChargeMitra"  # Merchant name
    am = str(amount)  # Amount
    cu = "INR"  # Currency
    tn = f"Booking {booking_code}"  # Transaction note
    
    # Google Pay deep link
    gpay_link = f"tez://upi/pay?pa={pa}&pn={pn}&am={am}&cu={cu}&tn={tn}"
    
    # PhonePe deep link
    phonepe_link = f"phonepe://pay?pa={pa}&pn={pn}&am={am}&cu={cu}&tn={tn}"
    
    # Generic UPI link
    upi_link = f"upi://pay?pa={pa}&pn={pn}&am={am}&cu={cu}&tn={tn}"
    
    return {
        "upi": upi_link,
        "gpay": gpay_link,
        "phonepe": phonepe_link
    }


@router.post("/create", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create payment order"""
    
    # Get booking
    booking = db.query(Booking).filter(Booking.id == payment_data.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify user owns this booking
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check payment status
    if booking.payment_status == PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed"
        )
    
    amount_paisa = int(booking.total_amount * 100)  # Convert to paisa
    
    if payment_data.payment_method == "razorpay":
        if not razorpay_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay not configured"
            )
        
        try:
            # Create Razorpay order
            order_data = {
                "amount": amount_paisa,
                "currency": "INR",
                "receipt": f"booking_{booking.id}_{booking.booking_code}",
                "notes": {
                    "booking_id": booking.id,
                    "user_id": current_user.id,
                    "charger_id": booking.charger_id
                }
            }
            
            order = razorpay_client.order.create(order_data)
            
            # Update booking with order ID
            booking.razorpay_order_id = order["id"]
            booking.payment_status = PaymentStatus.PENDING
            db.commit()
            
            return PaymentResponse(
                payment_id="",
                order_id=order["id"],
                amount=booking.total_amount,
                currency="INR",
                payment_url=None,
                upi_intent=None
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Razorpay order: {str(e)}"
            )
    
    elif payment_data.payment_method == "upi":
        # Generate UPI deep links
        upi_links = generate_upi_deep_link(
            booking.total_amount,
            booking.booking_code
        )
        
        return PaymentResponse(
            payment_id="",
            order_id="",
            amount=booking.total_amount,
            currency="INR",
            payment_url=None,
            upi_intent=json.dumps(upi_links)
        )
    
    elif payment_data.payment_method == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe not configured"
            )
        
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_paisa,  # Stripe also uses smallest currency unit
                currency="inr",
                metadata={
                    "booking_id": booking.id,
                    "user_id": current_user.id,
                    "booking_code": booking.booking_code
                }
            )
            
            return PaymentResponse(
                payment_id=intent.id,
                order_id="",
                amount=booking.total_amount,
                currency="INR",
                payment_url=None,
                upi_intent=None
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Stripe payment: {str(e)}"
            )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment method"
        )


@router.post("/confirm")
def confirm_payment(
    payment_data: PaymentConfirm,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Confirm Razorpay payment"""
    
    if not razorpay_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay not configured"
        )
    
    # Find booking by order ID
    booking = db.query(Booking).filter(
        Booking.razorpay_order_id == payment_data.order_id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found for this order"
        )
    
    # Verify user owns this booking
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': payment_data.order_id,
            'razorpay_payment_id': payment_data.payment_id,
            'razorpay_signature': payment_data.signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Payment verified, update booking
        booking.payment_status = PaymentStatus.COMPLETED
        booking.payment_method = "razorpay"
        booking.payment_id = payment_data.payment_id
        booking.razorpay_payment_id = payment_data.payment_id
        booking.paid_amount = booking.total_amount
        
        # Auto-confirm booking if not already confirmed
        if booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
        
        db.commit()
        
        return {
            "message": "Payment confirmed successfully",
            "booking_id": booking.id,
            "status": booking.status.value
        }
        
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)) -> Any:
    """Handle payment webhooks from Razorpay/Stripe"""
    
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    
    if signature:
        # Razorpay webhook
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook secret not configured"
            )
        
        # Verify webhook signature
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        
        try:
            event = json.loads(body)
            
            if event["event"] == "payment.captured":
                payment = event["payload"]["payment"]["entity"]
                order_id = payment["order_id"]
                payment_id = payment["id"]
                amount = payment["amount"] / 100  # Convert from paisa
                
                # Find and update booking
                booking = db.query(Booking).filter(
                    Booking.razorpay_order_id == order_id
                ).first()
                
                if booking:
                    booking.payment_status = PaymentStatus.COMPLETED
                    booking.payment_id = payment_id
                    booking.razorpay_payment_id = payment_id
                    booking.paid_amount = amount
                    
                    if booking.status == BookingStatus.PENDING:
                        booking.status = BookingStatus.CONFIRMED
                    
                    db.commit()
            
            elif event["event"] == "payment.failed":
                payment = event["payload"]["payment"]["entity"]
                order_id = payment["order_id"]
                
                booking = db.query(Booking).filter(
                    Booking.razorpay_order_id == order_id
                ).first()
                
                if booking:
                    booking.payment_status = PaymentStatus.FAILED
                    db.commit()
            
            return {"status": "success"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook processing failed: {str(e)}"
            )
    
    else:
        # Check for Stripe webhook
        stripe_signature = request.headers.get("stripe-signature")
        
        if stripe_signature and settings.STRIPE_WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(
                    body, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
                )
                
                if event["type"] == "payment_intent.succeeded":
                    payment_intent = event["data"]["object"]
                    booking_id = payment_intent["metadata"]["booking_id"]
                    
                    booking = db.query(Booking).filter(Booking.id == booking_id).first()
                    if booking:
                        booking.payment_status = PaymentStatus.COMPLETED
                        booking.payment_id = payment_intent["id"]
                        booking.paid_amount = payment_intent["amount"] / 100
                        
                        if booking.status == BookingStatus.PENDING:
                            booking.status = BookingStatus.CONFIRMED
                        
                        db.commit()
                
                return {"status": "success"}
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stripe webhook error: {str(e)}"
                )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid webhook"
    )


@router.post("/refund")
def create_refund(
    refund_data: RefundRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create refund for a booking"""
    
    booking = db.query(Booking).filter(Booking.id == refund_data.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions (renter, host, or admin)
    if not (
        booking.renter_id == current_user.id or
        booking.charger.host_id == current_user.id or
        current_user.role.value == "admin"
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
    
    refund_amount = refund_data.amount or booking.paid_amount
    refund_amount_paisa = int(refund_amount * 100)
    
    try:
        if booking.payment_method == "razorpay" and booking.razorpay_payment_id:
            if not razorpay_client:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Razorpay not configured"
                )
            
            refund = razorpay_client.payment.refund(
                booking.razorpay_payment_id,
                {
                    "amount": refund_amount_paisa,
                    "notes": {
                        "reason": refund_data.reason,
                        "booking_id": booking.id
                    }
                }
            )
            
            booking.payment_status = PaymentStatus.REFUNDED if refund_amount == booking.paid_amount else PaymentStatus.PARTIAL_REFUND
            booking.refund_amount = refund_amount
            db.commit()
            
            return {
                "message": "Refund processed successfully",
                "refund_id": refund["id"],
                "amount": refund_amount
            }
        
        elif booking.payment_method == "stripe":
            refund = stripe.Refund.create(
                payment_intent=booking.payment_id,
                amount=refund_amount_paisa,
                metadata={
                    "reason": refund_data.reason,
                    "booking_id": booking.id
                }
            )
            
            booking.payment_status = PaymentStatus.REFUNDED if refund_amount == booking.paid_amount else PaymentStatus.PARTIAL_REFUND
            booking.refund_amount = refund_amount
            db.commit()
            
            return {
                "message": "Refund processed successfully",
                "refund_id": refund.id,
                "amount": refund_amount
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund not supported for this payment method"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )