"""
WebSocket endpoints for real-time communication
"""
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import asyncio
import logging

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.charger import Charger
from app.models.booking import Booking

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[int, WebSocket] = {}
        # Charger subscriptions: charger_id -> list of user_ids
        self.charger_subscriptions: Dict[int, List[int]] = {}
        # Booking subscriptions: booking_id -> list of user_ids  
        self.booking_subscriptions: Dict[int, List[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept connection and store user mapping"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: int):
        """Remove user connection and clean up subscriptions"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Clean up charger subscriptions
        for charger_id, subscribers in self.charger_subscriptions.items():
            if user_id in subscribers:
                subscribers.remove(user_id)
        
        # Clean up booking subscriptions  
        for booking_id, subscribers in self.booking_subscriptions.items():
            if user_id in subscribers:
                subscribers.remove(user_id)
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    def subscribe_to_charger(self, user_id: int, charger_id: int):
        """Subscribe user to charger updates"""
        if charger_id not in self.charger_subscriptions:
            self.charger_subscriptions[charger_id] = []
        
        if user_id not in self.charger_subscriptions[charger_id]:
            self.charger_subscriptions[charger_id].append(user_id)
            logger.info(f"User {user_id} subscribed to charger {charger_id}")
    
    def subscribe_to_booking(self, user_id: int, booking_id: int):
        """Subscribe user to booking updates"""
        if booking_id not in self.booking_subscriptions:
            self.booking_subscriptions[booking_id] = []
        
        if user_id not in self.booking_subscriptions[booking_id]:
            self.booking_subscriptions[booking_id].append(user_id)
            logger.info(f"User {user_id} subscribed to booking {booking_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_charger_subscribers(self, message: dict, charger_id: int):
        """Broadcast message to all users subscribed to a charger"""
        if charger_id in self.charger_subscriptions:
            subscribers = self.charger_subscriptions[charger_id].copy()
            for user_id in subscribers:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_to_booking_subscribers(self, message: dict, booking_id: int):
        """Broadcast message to all users subscribed to a booking"""
        if booking_id in self.booking_subscriptions:
            subscribers = self.booking_subscriptions[booking_id].copy()
            for user_id in subscribers:
                await self.send_personal_message(message, user_id)


# Global connection manager
manager = ConnectionManager()


async def get_current_user_ws(websocket: WebSocket, token: str, db: Session) -> User:
    """Get current user from WebSocket token"""
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        return user
        
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


@router.websocket("/chargers/{charger_id}")
async def charger_websocket(
    websocket: WebSocket,
    charger_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for charger real-time updates"""
    
    # Authenticate user
    current_user = await get_current_user_ws(websocket, token, db)
    if not current_user:
        return
    
    # Verify charger exists
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
    
    # Connect user and subscribe to charger
    await manager.connect(websocket, current_user.id)
    manager.subscribe_to_charger(current_user.id, charger_id)
    
    try:
        # Send initial charger status
        await websocket.send_text(json.dumps({
            "type": "charger_status",
            "charger_id": charger_id,
            "status": charger.current_status.value,
            "is_active": charger.is_active,
            "timestamp": str(db.execute("SELECT NOW()").scalar())
        }))
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": str(db.execute("SELECT NOW()").scalar())
                    }))
                
                elif message.get("type") == "get_telemetry":
                    # Get latest telemetry data
                    latest_telemetry = db.query(charger.telemetry).order_by(
                        charger.telemetry.timestamp.desc()
                    ).first()
                    
                    if latest_telemetry:
                        await websocket.send_text(json.dumps({
                            "type": "telemetry_update",
                            "charger_id": charger_id,
                            "power_output_kw": latest_telemetry.power_output_kw,
                            "voltage_v": latest_telemetry.voltage_v,
                            "current_a": latest_telemetry.current_a,
                            "energy_delivered_kwh": latest_telemetry.energy_delivered_kwh,
                            "session_duration_minutes": latest_telemetry.session_duration_minutes,
                            "timestamp": str(latest_telemetry.timestamp)
                        }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"WebSocket error for user {current_user.id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(current_user.id)


@router.websocket("/bookings/{booking_id}")
async def booking_websocket(
    websocket: WebSocket,
    booking_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for booking real-time updates"""
    
    # Authenticate user
    current_user = await get_current_user_ws(websocket, token, db)
    if not current_user:
        return
    
    # Verify booking exists and user has access
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
    
    # Check access permissions
    has_access = (
        booking.renter_id == current_user.id or
        booking.charger.host_id == current_user.id or
        current_user.role.value == "admin"
    )
    
    if not has_access:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user and subscribe to booking
    await manager.connect(websocket, current_user.id)
    manager.subscribe_to_booking(current_user.id, booking_id)
    
    try:
        # Send initial booking status
        await websocket.send_text(json.dumps({
            "type": "booking_status",
            "booking_id": booking_id,
            "status": booking.status.value,
            "payment_status": booking.payment_status.value,
            "start_time": str(booking.start_time),
            "end_time": str(booking.end_time),
            "timestamp": str(db.execute("SELECT NOW()").scalar())
        }))
        
        # If booking has an active session, send session info
        if booking.session:
            await websocket.send_text(json.dumps({
                "type": "session_update",
                "booking_id": booking_id,
                "session_id": booking.session.session_id,
                "status": booking.session.status.value,
                "energy_delivered_kwh": booking.session.energy_delivered_kwh,
                "actual_duration_minutes": booking.session.actual_duration_minutes,
                "timestamp": str(db.execute("SELECT NOW()").scalar())
            }))
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": str(db.execute("SELECT NOW()").scalar())
                    }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"WebSocket error for user {current_user.id}: {e}")
    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(current_user.id)


# Utility functions for broadcasting updates from other parts of the application

async def broadcast_charger_update(charger_id: int, update_data: dict):
    """Broadcast charger status update to all subscribers"""
    message = {
        "type": "charger_update",
        "charger_id": charger_id,
        **update_data
    }
    await manager.broadcast_to_charger_subscribers(message, charger_id)


async def broadcast_booking_update(booking_id: int, update_data: dict):
    """Broadcast booking status update to all subscribers"""
    message = {
        "type": "booking_update", 
        "booking_id": booking_id,
        **update_data
    }
    await manager.broadcast_to_booking_subscribers(message, booking_id)


async def broadcast_telemetry_update(charger_id: int, telemetry_data: dict):
    """Broadcast telemetry update to charger subscribers"""
    message = {
        "type": "telemetry_update",
        "charger_id": charger_id,
        **telemetry_data
    }
    await manager.broadcast_to_charger_subscribers(message, charger_id)


async def send_notification(user_id: int, notification: dict):
    """Send notification to specific user"""
    message = {
        "type": "notification",
        **notification
    }
    await manager.send_personal_message(message, user_id)