"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users, 
    chargers,
    bookings,
    payments,
    reviews,
    admin,
    websocket,
)

# Conditionally import dummy payments in development
from app.core.config import settings
if settings.USE_DUMMY_PAYMENTS:
    from app.api.v1.endpoints import payments_dummy

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Charger management routes  
api_router.include_router(chargers.router, prefix="/chargers", tags=["Chargers"])

# Booking management routes
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])

# Payment routes
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# Review routes
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

# Admin routes
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# WebSocket routes
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

# Dummy payment routes (development only)
if settings.USE_DUMMY_PAYMENTS:
    api_router.include_router(payments_dummy.router, prefix="/payments", tags=["Dummy Payments"])