"""WebSocket connection and message management"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional, TYPE_CHECKING
import json
import asyncio
import logging
from datetime import datetime

if TYPE_CHECKING:
    from app.game.game_service import GameService

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Active connections: room_id -> list of websockets
        self.connections: Dict[str, List[WebSocket]] = {}
        # WebSocket to room mapping
        self.websocket_rooms: Dict[WebSocket, str] = {}
        # WebSocket to user mapping
        self.websocket_users: Dict[WebSocket, str] = {}
        # WebSocket to seat mapping
        self.websocket_seats: Dict[WebSocket, int] = {}
        # Game service reference
        self.game_service: Optional["GameService"] = None
        
    async def connect(self, websocket: WebSocket, token: Optional[str], room_id: Optional[str]):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Validate token and get user_id (matches auth router logic)
        user_id: Optional[str] = None
        try:
            if token:
                from jose import jwt
                from app.config import settings
                payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
                user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"Invalid WS token: {e}")

        if room_id:
            if room_id not in self.connections:
                self.connections[room_id] = []
            self.connections[room_id].append(websocket)
            self.websocket_rooms[websocket] = room_id
            
            # If authenticated, try to resolve user's seat in the room
            try:
                if user_id:
                    from app.database import SessionLocal, RoomMember
                    db = SessionLocal()
                    try:
                        member = db.query(RoomMember).filter(
                            RoomMember.room_id == room_id,
                            RoomMember.user_id == user_id,
                            RoomMember.left_at.is_(None)
                        ).first()
                        if member and member.seat:
                            self.websocket_seats[websocket] = member.seat
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Failed to resolve seat for WS: {e}")

        self.websocket_users[websocket] = user_id
        
        logger.info(f"WebSocket connected: user={user_id}, room={room_id}")
        
        # Send connection acknowledgment
        await self.send_personal_message(websocket, {
            "type": "system",
            "payload": {
                "message": "Connected successfully",
                "room_id": room_id
            },
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        room_id = self.websocket_rooms.get(websocket)
        user_id = self.websocket_users.get(websocket)
        
        if room_id and websocket in self.connections.get(room_id, []):
            self.connections[room_id].remove(websocket)
            if not self.connections[room_id]:
                del self.connections[room_id]
                
        self.websocket_rooms.pop(websocket, None)
        self.websocket_users.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected: user={user_id}, room={room_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: dict, 
        exclude: Optional[WebSocket] = None,
        target_seats: Optional[List[int]] = None
    ):
        """Broadcast message to all connections in a room"""
        if room_id not in self.connections:
            return
            
        failed_connections = []
        for connection in list(self.connections[room_id]):
            if connection == exclude:
                continue
            
            # Seat-based filtering
            if target_seats is not None:
                seat = self.websocket_seats.get(connection)
                if seat not in target_seats:
                    continue

            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                failed_connections.append(connection)
        
        # Clean up failed connections
        for connection in failed_connections:
            await self.disconnect(connection)
    
    async def handle_message(self, websocket: WebSocket, message: dict):
        """Process incoming WebSocket message"""
        try:
            message_type = message.get("type")
            # Support both reqId (spec) and req_id (legacy)
            req_id = message.get("reqId") or message.get("req_id")
            payload = message.get("payload", {})
            room_id = self.websocket_rooms.get(websocket)
            user_id = self.websocket_users.get(websocket)
            
            logger.info(f"Received message: type={message_type}, user={user_id}, room={room_id}")
            
            # Send ACK
            if req_id:
                await self.send_personal_message(websocket, {
                    "type": "ack",
                    "reqId": req_id,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                })
            
            # Handle different message types
            if message_type == "speak":
                await self._handle_speak(websocket, room_id, user_id, payload)
            elif message_type == "vote":
                await self._handle_vote(websocket, room_id, user_id, payload)
            elif message_type == "night_action":
                await self._handle_night_action(websocket, room_id, user_id, payload)
            else:
                await self.send_personal_message(websocket, {
                    "type": "error",
                    "reqId": req_id,
                    "payload": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {message_type}"
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000)
                })
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error"
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
    
    async def _handle_speak(self, websocket: WebSocket, room_id: str, user_id: str, payload: dict):
        """Handle speak message"""
        content = payload.get("content", "")
        seat = self.websocket_seats.get(websocket)
        
        if not seat or not self.game_service:
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "INVALID_SESSION",
                    "message": "Invalid session or game not started"
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            return
        
        try:
            # Find game_id for this room
            from app.database import Room, Game
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                room = db.query(Room).filter(Room.id == room_id).first()
                if room:
                    game = db.query(Game).filter(Game.room_id == room_id).order_by(Game.started_at.desc()).first()
                    if game:
                        await self.game_service.submit_speak(game.id, seat, content)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error handling speak: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "SPEAK_FAILED",
                    "message": str(e)
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
    
    async def _handle_vote(self, websocket: WebSocket, room_id: str, user_id: str, payload: dict):
        """Handle vote message"""
        target_seat = payload.get("target_seat")
        seat = self.websocket_seats.get(websocket)
        
        if not seat or not self.game_service:
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "INVALID_SESSION",
                    "message": "Invalid session or game not started"
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            return
        
        try:
            # Find game_id for this room
            from app.database import Room, Game
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                room = db.query(Room).filter(Room.id == room_id).first()
                if room:
                    game = db.query(Game).filter(Game.room_id == room_id).order_by(Game.started_at.desc()).first()
                    if game:
                        await self.game_service.submit_vote(game.id, seat, target_seat)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error handling vote: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "VOTE_FAILED",
                    "message": str(e)
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
    
    async def _handle_night_action(self, websocket: WebSocket, room_id: str, user_id: str, payload: dict):
        """Handle night action message"""
        action = payload.get("action")
        target_seat = payload.get("target_seat")
        seat = self.websocket_seats.get(websocket)
        
        if not seat or not self.game_service:
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "INVALID_SESSION",
                    "message": "Invalid session or game not started"
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            return
        
        try:
            # Find game_id for this room
            from app.database import Room, Game
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                room = db.query(Room).filter(Room.id == room_id).first()
                if room:
                    game = db.query(Game).filter(Game.room_id == room_id).order_by(Game.started_at.desc()).first()
                    if game:
                        await self.game_service.submit_night_action(game.id, seat, action, target_seat)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error handling night action: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "payload": {
                    "code": "NIGHT_ACTION_FAILED",
                    "message": str(e)
                },
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
