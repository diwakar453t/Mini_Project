# Add new endpoints for availability and pricing

@router.get("/chargers/{charger_id}/availability")
def get_charger_availability(
    charger_id: int,
    date: str,  # Format: YYYY-MM-DD
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get available time slots for a charger on a specific date"""
    
    try:
        # Parse date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Ensure date is not in the past
        if target_date.date() < datetime.utcnow().date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot check availability for past dates"
            )
        
        # Get availability slots
        slots = booking_service.get_availability_slots(
            db=db,
            charger_id=charger_id,
            date=target_date
        )
        
        return {
            "charger_id": charger_id,
            "date": date,
            "slots": slots,
            "total_slots": len(slots),
            "available_slots": len([s for s in slots if s["available"]])
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/estimate-price")
def estimate_booking_price(
    charger_id: int,
    start_time: datetime,
    end_time: datetime,
    vehicle_info: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get price estimate for a booking"""
    
    try:
        pricing_breakdown = booking_service.calculate_pricing(
            db=db,
            charger_id=charger_id,
            start_time=start_time,
            end_time=end_time,
            vehicle_info=vehicle_info
        )
        
        return {
            "charger_id": charger_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "pricing": pricing_breakdown,
            "currency": "INR"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{booking_id}/extend")
def extend_booking(
    booking_id: int,
    extension_data: ExtendBooking,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Extend a booking"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Calculate new end time
    new_end_time = booking.end_time + timedelta(minutes=extension_data.additional_minutes)
    
    try:
        updated_booking = booking_service.extend_booking(
            db=db,
            booking_id=booking_id,
            new_end_time=new_end_time,
            user_id=current_user.id
        )
        
        return updated_booking
        
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