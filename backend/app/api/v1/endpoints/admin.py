"""
Admin management endpoints
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User, UserRole, KYCStatus
from app.models.charger import Charger
from app.models.booking import Booking, BookingStatus
from app.models.dispute import Dispute, DisputeStatus
from app.models.review import Review

router = APIRouter()


# Pydantic models
class AdminMetrics(BaseModel):
    total_users: int
    total_hosts: int
    total_chargers: int
    active_chargers: int
    total_bookings: int
    active_bookings: int
    total_revenue: float
    pending_disputes: int
    pending_kyc: int


class UserManagement(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    kyc_status: KYCStatus
    created_at: str
    last_login: Optional[str]


class DisputeResolution(BaseModel):
    resolution_notes: str
    resolution_action: str  # refund, no_action, compensation
    refund_amount: Optional[float] = None


class KYCApproval(BaseModel):
    approved: bool
    notes: Optional[str] = None


@router.get("/metrics", response_model=AdminMetrics)
def get_platform_metrics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get platform metrics and KPIs"""
    
    # User metrics
    total_users = db.query(func.count(User.id)).scalar()
    total_hosts = db.query(func.count(User.id)).filter(User.role == UserRole.HOST).scalar()
    
    # Charger metrics
    total_chargers = db.query(func.count(Charger.id)).scalar()
    active_chargers = db.query(func.count(Charger.id)).filter(Charger.is_active == True).scalar()
    
    # Booking metrics
    total_bookings = db.query(func.count(Booking.id)).scalar()
    active_bookings = db.query(func.count(Booking.id)).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE])
    ).scalar()
    
    # Revenue metrics
    total_revenue = db.query(func.sum(Booking.platform_fee)).filter(
        Booking.payment_status == "completed"
    ).scalar() or 0.0
    
    # Pending items
    pending_disputes = db.query(func.count(Dispute.id)).filter(
        Dispute.status == DisputeStatus.OPEN
    ).scalar()
    
    pending_kyc = db.query(func.count(User.id)).filter(
        User.kyc_status == KYCStatus.SUBMITTED
    ).scalar()
    
    return AdminMetrics(
        total_users=total_users,
        total_hosts=total_hosts,
        total_chargers=total_chargers,
        active_chargers=active_chargers,
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        total_revenue=total_revenue,
        pending_disputes=pending_disputes,
        pending_kyc=pending_kyc
    )


@router.get("/users", response_model=List[UserManagement])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    kyc_status: Optional[KYCStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get all users with filtering"""
    
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if kyc_status:
        query = query.filter(User.kyc_status == kyc_status)
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    query = query.order_by(User.created_at.desc())
    users = query.offset(skip).limit(limit).all()
    
    return [
        UserManagement(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            kyc_status=user.kyc_status,
            created_at=str(user.created_at),
            last_login=user.last_login
        )
        for user in users
    ]


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Update user status (activate/deactivate, change role)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id and is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Update fields
    if is_active is not None:
        user.is_active = is_active
    if role is not None:
        user.role = role
    
    db.commit()
    
    return {
        "message": "User updated successfully",
        "user_id": user.id,
        "is_active": user.is_active,
        "role": user.role.value
    }


@router.post("/users/{user_id}/kyc/approve")
def approve_kyc(
    user_id: int,
    approval_data: KYCApproval,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Approve or reject KYC verification"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.kyc_status != KYCStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC not in submitted status"
        )
    
    # Update KYC status
    if approval_data.approved:
        user.kyc_status = KYCStatus.VERIFIED
        user.is_verified = True
        message = "KYC approved successfully"
    else:
        user.kyc_status = KYCStatus.REJECTED
        message = "KYC rejected"
    
    # Add admin notes to profile
    if user.profile and approval_data.notes:
        kyc_docs = user.profile.kyc_documents or {}
        kyc_docs["admin_notes"] = approval_data.notes
        kyc_docs["reviewed_by"] = current_user.id
        kyc_docs["reviewed_at"] = str(datetime.utcnow())
        user.profile.kyc_documents = kyc_docs
    
    db.commit()
    
    return {
        "message": message,
        "user_id": user.id,
        "kyc_status": user.kyc_status.value
    }


@router.get("/chargers")
def get_all_chargers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    city: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get all chargers with admin details"""
    
    query = db.query(Charger)
    
    if is_active is not None:
        query = query.filter(Charger.is_active == is_active)
    if is_verified is not None:
        query = query.filter(Charger.is_verified == is_verified)
    if city:
        query = query.filter(Charger.city.ilike(f"%{city}%"))
    
    query = query.order_by(Charger.created_at.desc())
    chargers = query.offset(skip).limit(limit).all()
    
    return [
        {
            **charger.dict(),
            "host_name": charger.host.name,
            "host_email": charger.host.email,
            "host_kyc_status": charger.host.kyc_status.value,
        }
        for charger in chargers
    ]


@router.patch("/chargers/{charger_id}")
def update_charger_status(
    charger_id: int,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Update charger status (verify/suspend)"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    if is_active is not None:
        charger.is_active = is_active
    if is_verified is not None:
        charger.is_verified = is_verified
    
    db.commit()
    
    return {
        "message": "Charger status updated",
        "charger_id": charger.id,
        "is_active": charger.is_active,
        "is_verified": charger.is_verified
    }


@router.get("/disputes")
def get_all_disputes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[DisputeStatus] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get all disputes"""
    
    query = db.query(Dispute)
    
    if status_filter:
        query = query.filter(Dispute.status == status_filter)
    
    query = query.order_by(Dispute.created_at.desc())
    disputes = query.offset(skip).limit(limit).all()
    
    return [
        {
            **dispute.dict(),
            "booking_code": dispute.booking.booking_code,
            "charger_title": dispute.booking.charger.title,
            "renter_name": dispute.booking.renter.name,
            "host_name": dispute.booking.charger.host.name,
            "raised_by_name": dispute.raised_by_user.name,
        }
        for dispute in disputes
    ]


@router.post("/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    resolution_data: DisputeResolution,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Resolve a dispute"""
    
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    if dispute.status == DisputeStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispute already resolved"
        )
    
    # Update dispute
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution_notes = resolution_data.resolution_notes
    dispute.resolution_action = resolution_data.resolution_action
    dispute.assigned_to = current_user.id
    dispute.resolved_at = datetime.utcnow()
    
    # Handle refund if requested
    if resolution_data.refund_amount and resolution_data.refund_amount > 0:
        dispute.refund_approved = resolution_data.refund_amount
        # TODO: Process actual refund through payment gateway
    
    db.commit()
    
    return {
        "message": "Dispute resolved successfully",
        "dispute_id": dispute.id,
        "resolution_action": resolution_data.resolution_action,
        "refund_amount": resolution_data.refund_amount
    }


@router.get("/analytics")
def get_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get platform analytics"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily booking counts
    daily_bookings = db.query(
        func.date(Booking.created_at).label('date'),
        func.count(Booking.id).label('count')
    ).filter(
        Booking.created_at >= start_date
    ).group_by(
        func.date(Booking.created_at)
    ).all()
    
    # Revenue by day
    daily_revenue = db.query(
        func.date(Booking.created_at).label('date'),
        func.sum(Booking.platform_fee).label('revenue')
    ).filter(
        and_(
            Booking.created_at >= start_date,
            Booking.payment_status == "completed"
        )
    ).group_by(
        func.date(Booking.created_at)
    ).all()
    
    # Top cities by bookings
    top_cities = db.query(
        Charger.city,
        func.count(Booking.id).label('booking_count')
    ).join(
        Booking, Charger.id == Booking.charger_id
    ).filter(
        Booking.created_at >= start_date
    ).group_by(
        Charger.city
    ).order_by(
        func.count(Booking.id).desc()
    ).limit(10).all()
    
    # Host performance
    top_hosts = db.query(
        User.name,
        func.count(Booking.id).label('booking_count'),
        func.avg(Review.rating).label('avg_rating')
    ).join(
        Charger, User.id == Charger.host_id
    ).join(
        Booking, Charger.id == Booking.charger_id
    ).outerjoin(
        Review, Booking.id == Review.booking_id
    ).filter(
        Booking.created_at >= start_date
    ).group_by(
        User.id, User.name
    ).order_by(
        func.count(Booking.id).desc()
    ).limit(10).all()
    
    return {
        "period": f"{days} days",
        "daily_bookings": [
            {"date": str(item.date), "count": item.count}
            for item in daily_bookings
        ],
        "daily_revenue": [
            {"date": str(item.date), "revenue": float(item.revenue or 0)}
            for item in daily_revenue
        ],
        "top_cities": [
            {"city": item.city, "booking_count": item.booking_count}
            for item in top_cities
        ],
        "top_hosts": [
            {
                "name": item.name,
                "booking_count": item.booking_count,
                "avg_rating": float(item.avg_rating or 0)
            }
            for item in top_hosts
        ]
    }


@router.get("/reviews/flagged")
def get_flagged_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Get flagged reviews for moderation"""
    
    reviews = db.query(Review).filter(
        Review.is_flagged == True
    ).order_by(
        Review.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        {
            **review.dict(),
            "charger_title": review.charger.title,
            "reviewer_name": review.reviewer.name,
            "host_name": review.charger.host.name,
        }
        for review in reviews
    ]