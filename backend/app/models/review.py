"""
Review and Rating models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, Float, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class Review(BaseModel):
    """Review and rating model"""
    
    __tablename__ = "reviews"
    
    # References
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True)
    charger_id = Column(Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Renter
    
    # Overall Rating
    rating = Column(Integer, nullable=False)  # 1-5 stars
    
    # Detailed Ratings
    charger_condition_rating = Column(Integer, nullable=True)  # 1-5
    location_rating = Column(Integer, nullable=True)  # 1-5  
    host_communication_rating = Column(Integer, nullable=True)  # 1-5
    value_for_money_rating = Column(Integer, nullable=True)  # 1-5
    charging_speed_rating = Column(Integer, nullable=True)  # 1-5
    
    # Review Content
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    
    # Review Categories/Tags
    positive_aspects = Column(JSON, nullable=True)  # ["clean", "fast_charging", "helpful_host"]
    negative_aspects = Column(JSON, nullable=True)  # ["hard_to_find", "slow_charging"]
    
    # Photos
    review_images = Column(JSON, nullable=True)  # Array of image URLs
    
    # Host Response
    host_response = Column(Text, nullable=True)
    host_responded_at = Column(String, nullable=True)  # DateTime as string
    
    # Review Status
    is_verified = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Moderation
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(100), nullable=True)
    moderated_at = Column(String, nullable=True)  # DateTime as string
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Helpfulness
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Additional Context
    charging_duration_hours = Column(Float, nullable=True)
    energy_charged_kwh = Column(Float, nullable=True)
    vehicle_type = Column(String(100), nullable=True)
    
    # Relationships
    booking = relationship("Booking", back_populates="review")
    charger = relationship("Charger", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews", foreign_keys=[reviewer_id])
    moderator = relationship("User", foreign_keys=[moderated_by])
    
    def __repr__(self):
        return f"<Review {self.id} - {self.rating} stars>"
    
    @property
    def host(self):
        """Get the host (charger owner) for this review"""
        return self.charger.host if self.charger else None
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = [
            self.charger_condition_rating,
            self.location_rating,
            self.host_communication_rating,
            self.value_for_money_rating,
            self.charging_speed_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return round(sum(valid_ratings) / len(valid_ratings), 1) if valid_ratings else None