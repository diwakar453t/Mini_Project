"""
Charger management endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel
from sqlalchemy import func as geo_func

from app.core.database import get_db
from app.core.security import get_current_active_user, get_current_host_or_admin, is_owner_or_admin
from app.models.charger import Charger, ChargerPricing, ConnectorType, ChargerType, ChargerStatus, PricingType
from app.models.user import User, UserRole

router = APIRouter()


# Pydantic models
class ChargerCreate(BaseModel):
    title: str
    description: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    connector_type: ConnectorType
    charger_type: ChargerType
    max_power_kw: float
    voltage: Optional[int] = None
    current_rating: Optional[int] = None
    amenities: Optional[dict] = {}
    features: Optional[dict] = {}
    availability_schedule: Optional[dict] = {}
    access_instructions: Optional[str] = None
    access_code: Optional[str] = None
    host_contact_required: bool = False
    auto_accept_bookings: bool = False


class ChargerPricingCreate(BaseModel):
    pricing_type: PricingType
    price_value: float
    min_session_minutes: int = 30
    max_session_minutes: int = 480
    peak_hours_start: Optional[str] = None
    peak_hours_end: Optional[str] = None
    peak_price_multiplier: float = 1.0
    weekend_price_multiplier: float = 1.0
    booking_fee: float = 0.0
    overstay_fee_per_hour: float = 50.0
    late_cancellation_fee: float = 100.0
    advance_booking_hours: int = 168
    same_day_booking: bool = True


class ChargerResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    connector_type: ConnectorType
    charger_type: ChargerType
    max_power_kw: float
    amenities: dict
    features: dict
    current_status: ChargerStatus
    is_active: bool
    is_verified: bool
    auto_accept_bookings: bool
    average_rating: float
    rating_count: int
    total_bookings: int
    host_id: int
    cover_image: Optional[str]
    images: List[str]
    
    class Config:
        from_attributes = True


class ChargerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[dict] = None
    features: Optional[dict] = None
    availability_schedule: Optional[dict] = None
    access_instructions: Optional[str] = None
    access_code: Optional[str] = None
    host_contact_required: Optional[bool] = None
    auto_accept_bookings: Optional[bool] = None
    is_active: Optional[bool] = None


@router.post("/", response_model=ChargerResponse, status_code=status.HTTP_201_CREATED)
def create_charger(
    charger_data: ChargerCreate,
    current_user: User = Depends(get_current_host_or_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new charger (host only)"""
    
    # Validate coordinates
    if not (-90 <= charger_data.latitude <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid latitude"
        )
    if not (-180 <= charger_data.longitude <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid longitude"
        )
    
    # Create charger
    charger = Charger(
        host_id=current_user.id,
        title=charger_data.title,
        description=charger_data.description,
        address=charger_data.address,
        city=charger_data.city,
        state=charger_data.state,
        pincode=charger_data.pincode,
        latitude=charger_data.latitude,
        longitude=charger_data.longitude,
        connector_type=charger_data.connector_type,
        charger_type=charger_data.charger_type,
        max_power_kw=charger_data.max_power_kw,
        voltage=charger_data.voltage,
        current_rating=charger_data.current_rating,
        amenities=charger_data.amenities,
        features=charger_data.features,
        availability_schedule=charger_data.availability_schedule,
        access_instructions=charger_data.access_instructions,
        access_code=charger_data.access_code,
        host_contact_required=charger_data.host_contact_required,
        auto_accept_bookings=charger_data.auto_accept_bookings,
        is_active=True,
        current_status=ChargerStatus.AVAILABLE,
    )
    
    db.add(charger)
    db.commit()
    db.refresh(charger)
    
    return {
        **charger.dict(),
        "latitude": charger_data.latitude,
        "longitude": charger_data.longitude,
        "images": charger.images or [],
    }


@router.get("/", response_model=List[ChargerResponse])
def search_chargers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = Query(None, ge=0.1, le=100),
    connector_type: Optional[ConnectorType] = None,
    charger_type: Optional[ChargerType] = None,
    min_power_kw: Optional[float] = None,
    max_price: Optional[float] = None,
    available_now: Optional[bool] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    amenities: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """Search chargers with filters"""
    
    query = db.query(Charger).filter(Charger.is_active == True)
    
    # City/State filters
    if city:
        query = query.filter(Charger.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Charger.state.ilike(f"%{state}%"))
    
    # Geo radius search via Haversine (no PostGIS)
    if latitude is not None and longitude is not None and radius_km is not None:
        lat1 = func.radians(latitude)
        lon1 = func.radians(longitude)
        lat2 = func.radians(Charger.latitude)
        lon2 = func.radians(Charger.longitude)
        dlon = lon2 - lon1
        d = 6371 * func.acos(
            func.cos(lat1) * func.cos(lat2) * func.cos(dlon) + func.sin(lat1) * func.sin(lat2)
        )
        query = query.filter(d <= radius_km).order_by(d)
    else:
        # Default ordering
        query = query.order_by(Charger.average_rating.desc(), Charger.created_at.desc())
    
    # Charger specification filters
    if connector_type:
        query = query.filter(Charger.connector_type == connector_type)
    if charger_type:
        query = query.filter(Charger.charger_type == charger_type)
    if min_power_kw:
        query = query.filter(Charger.max_power_kw >= min_power_kw)
    
    # Rating filter
    if min_rating:
        query = query.filter(Charger.average_rating >= min_rating)
    
    # Status filters
    if available_now:
        query = query.filter(Charger.current_status == ChargerStatus.AVAILABLE)
    
    # Amenities filter
    if amenities:
        for amenity in amenities:
            query = query.filter(
                func.jsonb_extract_path_text(Charger.amenities, amenity) == 'true'
            )
    
    # TODO: Price filter (requires joining with pricing table)
    
    total = query.count()
    chargers = query.offset(skip).limit(limit).all()
    
    # Convert chargers to response format
    charger_responses = []
    for charger in chargers:
        latitude_val = charger.latitude or 0.0
        longitude_val = charger.longitude or 0.0
        
        charger_responses.append({
            **charger.dict(),
            "latitude": latitude_val,
            "longitude": longitude_val,
            "images": charger.images or [],
        })
    
    return charger_responses


@router.get("/{charger_id}", response_model=ChargerResponse)
def get_charger(
    charger_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get charger details by ID"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    latitude_val = charger.latitude or 0.0
    longitude_val = charger.longitude or 0.0
    
    return {
        **charger.dict(),
        "latitude": latitude_val,
        "longitude": longitude_val,
        "images": charger.images or [],
    }


@router.patch("/{charger_id}", response_model=ChargerResponse)
def update_charger(
    charger_id: int,
    charger_update: ChargerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update charger (owner or admin only)"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    # Check ownership
    if not is_owner_or_admin(charger.host_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this charger"
        )
    
    # Update fields
    for field, value in charger_update.dict(exclude_unset=True).items():
        setattr(charger, field, value)
    
    db.commit()
    db.refresh(charger)
    
    latitude_val = charger.latitude or 0.0
    longitude_val = charger.longitude or 0.0
    
    return {
        **charger.dict(),
        "latitude": latitude_val,
        "longitude": longitude_val,
        "images": charger.images or [],
    }


@router.delete("/{charger_id}")
def delete_charger(
    charger_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete charger (owner or admin only)"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    # Check ownership
    if not is_owner_or_admin(charger.host_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this charger"
        )
    
    # Check for active bookings
    active_bookings = db.query(func.count()).filter(
        and_(
            Charger.id == charger_id,
            # TODO: Check for active bookings
        )
    ).scalar()
    
    if active_bookings > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete charger with active bookings"
        )
    
    db.delete(charger)
    db.commit()
    
    return {"message": "Charger deleted successfully"}


@router.post("/{charger_id}/pricing", status_code=status.HTTP_201_CREATED)
def create_charger_pricing(
    charger_id: int,
    pricing_data: ChargerPricingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Set pricing for charger (owner only)"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    # Check ownership
    if not is_owner_or_admin(charger.host_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to set pricing for this charger"
        )
    
    # Remove existing pricing
    db.query(ChargerPricing).filter(ChargerPricing.charger_id == charger_id).delete()
    
    # Create new pricing
    pricing = ChargerPricing(
        charger_id=charger_id,
        **pricing_data.dict()
    )
    
    db.add(pricing)
    db.commit()
    db.refresh(pricing)
    
    return pricing


@router.get("/{charger_id}/pricing")
def get_charger_pricing(
    charger_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get charger pricing"""
    
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found"
        )
    
    pricing = db.query(ChargerPricing).filter(ChargerPricing.charger_id == charger_id).first()
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing not configured for this charger"
        )
    
    return pricing