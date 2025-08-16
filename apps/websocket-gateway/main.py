"""
Cyber Werewolves WebSocket Gateway Service
Handles real-time WebSocket connections and message broadcasting
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
import redis.asyncio as redis
import nats.aio.client as nc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cyber Werewolves WebSocket Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
redis_client: redis.Redis = None
nats_client: nc.Client = None
active_connections: Dict[str, Set[WebSocket]] = {}
room_connections: Dict[str, Set[str]] = {}

class ConnectionManager:
    """Manages WebSocket connections and rooms"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.room_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all rooms
        for room_id, clients in self.room_connections.items():
            if client_id in clients:
                clients.remove(client_id)
        
        logger.info(f"Client {client_id} disconnected")
    
    async def join_room(self, client_id: str, room_id: str):
        """Add client to a room"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(client_id)
        logger.info(f"Client {client_id} joined room {room_id}")
    
    async def leave_room(self, client_id: str, room_id: str):
        """Remove client from a room"""
        if room_id in self.room_connections:
            if client_id in self.room_connections[room_id]:
                self.room_connections[room_id].remove(client_id)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        logger.info(f"Client {client_id} left room {room_id}")
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude_client: str = None):
        """Broadcast message to all clients in a room"""
        if room_id in self.room_connections:
            for client_id in self.room_connections[room_id]:
                if client_id != exclude_client:
                    await self.send_to_client(client_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for client_id in self.active_connections:
            await self.send_to_client(client_id, message)

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "websocket-gateway"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            
            if msg_type == "join_room":
                room_id = message.get("room_id")
                await manager.join_room(client_id, room_id)
                
            elif msg_type == "leave_room":
                room_id = message.get("room_id")
                await manager.leave_room(client_id, room_id)
                
            elif msg_type == "message":
                room_id = message.get("room_id")
                payload = message.get("payload", {})
                
                # Broadcast to room
                await manager.broadcast_to_room(room_id, {
                    "type": "message",
                    "sender_id": client_id,
                    "payload": payload,
                    "timestamp": message.get("timestamp")
                }, exclude_client=client_id)
                
            elif msg_type == "ping":
                # Send pong response
                await manager.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(client_id)

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True,
            health_check_interval=30
        )
        await redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

async def init_nats():
    """Initialize NATS connection"""
    global nats_client
    try:
        nats_client = nc.Client()
        await nats_client.connect(servers=["nats://nats:4222"])
        
        # Subscribe to game events
        await nats_client.subscribe("game.*", cb=handle_game_event)
        logger.info("Connected to NATS")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {e}")

async def handle_game_event(msg):
    """Handle incoming game events from NATS"""
    try:
        subject = msg.subject
        data = json.loads(msg.data.decode())
        
        # Extract room_id from subject (e.g., "game.room_123")
        parts = subject.split(".")
        if len(parts) >= 2:
            room_id = parts[1]
            
            # Broadcast to all clients in the room
            await manager.broadcast_to_room(room_id, {
                "type": "game_event",
                "event_type": data.get("type"),
                "payload": data.get("payload", {}),
                "timestamp": data.get("timestamp")
            })
            
    except Exception as e:
        logger.error(f"Error handling game event: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting WebSocket Gateway...")
    await init_redis()
    await init_nats()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down WebSocket Gateway...")
    if redis_client:
        await redis_client.close()
    if nats_client:
        await nats_client.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False
    )