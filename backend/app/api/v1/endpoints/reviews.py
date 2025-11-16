"""
Review and rating endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user, is_owner_or_admin
from app.models.review import Review
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole

router = APIRouter()


# Pydantic models
class ReviewCreate(BaseModel):
    rating: int  # 1-5
    title: Optional[str] = None
    comment: Optional[str] = None
    charger_condition_rating: Optional[int] = None
    location_rating: Optional[int] = None
    host_communication_rating: Optional[int] = None
    value_for_money_rating: Optional[int] = None
    charging_speed_rating: Optional[int] = None
    positive_aspects: List[str] = []
    negative_aspects: List[str] = []


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    charger_id: int
    reviewer_id: int
    rating: int
    title: Optional[str]
    comment: Optional[str]
    charger_condition_rating: Optional[int]
    location_rating: Optional[int]
    host_communication_rating: Optional[int]
    value_for_money_rating: Optional[int]
    charging_speed_rating: Optional[int]
    positive_aspects: List[str]
    negative_aspects: List[str]
    host_response: Optional[str]
    host_responded_at: Optional[str]
    is_verified: bool
    is_public: bool
    helpful_count: int
    not_helpful_count: int
    created_at: str
    
    # Reviewer info
    reviewer_name: str
    reviewer_avatar: Optional[str]
    
    class Config:
        from_attributes = True


class HostResponse(BaseModel):
    response: str


class ReviewUpdate(BaseModel):
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_flagged: Optional[bool] = None
    flag_reason: Optional[str] = None


@router.post("/bookings/{booking_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    booking_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a review for a completed booking"""
    
    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify user is the renter
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the renter can review this booking"
        )
    
    # Check if booking is completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings"
        )
    
    # Check if review already exists
    existing_review = db.query(Review).filter(Review.booking_id == booking_id).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking"
        )
    
    # Validate rating
    if not 1 <= review_data.rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Create review
    review = Review(
        booking_id=booking_id,
        charger_id=booking.charger_id,
        reviewer_id=current_user.id,
        rating=review_data.rating,
        title=review_data.title,
        comment=review_data.comment,
        charger_condition_rating=review_data.charger_condition_rating,
        location_rating=review_data.location_rating,
        host_communication_rating=review_data.host_communication_rating,
        value_for_money_rating=review_data.value_for_money_rating,
        charging_speed_rating=review_data.charging_speed_rating,
        positive_aspects=review_data.positive_aspects,
        negative_aspects=review_data.negative_aspects,
        is_verified=True,
        is_public=True,
    )
    
    # Add session context if available
    if booking.session:
        review.charging_duration_hours = booking.session.actual_duration_minutes / 60 if booking.session.actual_duration_minutes else None
        review.energy_charged_kwh = booking.session.energy_delivered_kwh
    
    # Add vehicle type from booking
    if booking.vehicle_info and "type" in booking.vehicle_info:
        review.vehicle_type = booking.vehicle_info["type"]
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Update charger rating (will be handled by database trigger in production)
    # For now, calculate manually
    charger = booking.charger
    all_reviews = db.query(Review).filter(
        Review.charger_id == charger.id,
        Review.is_public == True
    ).all()
    
    if all_reviews:
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        charger.average_rating = round(avg_rating, 1)
        charger.rating_count = len(all_reviews)
        db.commit()
    
    return {
        **review.dict(),
        "reviewer_name": current_user.name,
        "reviewer_avatar": current_user.profile.avatar_url if current_user.profile else None,
        "created_at": str(review.created_at),
    }


@router.get("/chargers/{charger_id}/reviews", response_model=List[ReviewResponse])
def get_charger_reviews(
    charger_id: int,
    skip: int = 0,
    limit: int = 20,
    min_rating: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """Get reviews for a charger"""
    
    query = db.query(Review).filter(
        Review.charger_id == charger_id,
        Review.is_public == True
    )
    
    if min_rating:
        query = query.filter(Review.rating >= min_rating)
    
    query = query.order_by(Review.created_at.desc())
    reviews = query.offset(skip).limit(limit).all()
    
    # Format reviews with reviewer info
    review_responses = []
    for review in reviews:
        reviewer = review.reviewer
        review_responses.append({
            **review.dict(),
            "reviewer_name": reviewer.name,
            "reviewer_avatar": reviewer.profile.avatar_url if reviewer.profile else None,
            "created_at": str(review.created_at),
            "host_responded_at": review.host_responded_at,
        })
    
    return review_responses


@router.post("/{review_id}/response")
def add_host_response(
    review_id: int,
    response_data: HostResponse,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Add host response to a review"""
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user is the host of the charger
    if review.charger.host_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the charger owner can respond to reviews"
        )
    
    # Check if response already exists
    if review.host_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host response already exists"
        )
    
    # Add response
    review.host_response = response_data.response
    review.host_responded_at = str(db.execute("SELECT NOW()").scalar())
    
    db.commit()
    
    return {
        "message": "Host response added successfully",
        "response": review.host_response
    }


@router.post("/{review_id}/helpful")
def mark_review_helpful(
    review_id: int,
    helpful: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Mark review as helpful or not helpful"""
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # TODO: Track user votes to prevent multiple votes
    # For now, just increment counters
    
    if helpful:
        review.helpful_count += 1
    else:
        review.not_helpful_count += 1
    
    db.commit()
    
    return {
        "message": "Vote recorded",
        "helpful_count": review.helpful_count,
        "not_helpful_count": review.not_helpful_count
    }


@router.patch("/{review_id}")
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update review (admin only for moderation)"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Update fields
    for field, value in review_update.dict(exclude_unset=True).items():
        setattr(review, field, value)
    
    # Add moderation info
    if review_update.is_flagged is not None:
        review.moderated_by = current_user.id
        review.moderated_at = str(db.execute("SELECT NOW()").scalar())
    
    db.commit()
    
    return {
        "message": "Review updated successfully",
        "review_id": review.id
    }


@router.get("/user/{user_id}/reviews")
def get_user_reviews(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get reviews written by a user"""
    
    # Only allow access to own reviews or admin
    if not is_owner_or_admin(user_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    reviews = db.query(Review).filter(
        Review.reviewer_id == user_id
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    review_responses = []
    for review in reviews:
        review_responses.append({
            **review.dict(),
            "charger_title": review.charger.title,
            "host_name": review.charger.host.name,
            "created_at": str(review.created_at),
        })
    
    return review_responses