"""Main FastAPI application"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import json
from typing import Dict, Set

from app.config import settings
from app.database import get_db, Base, engine
from app.routers import auth, rooms, admin, llm_config
from app.routers import game_actions, agent_tools, llm_admin
from app.websocket_manager import manager

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="Cyber Werewolves API",
    description="人机混战狼人杀平台",
    version="0.1.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager is imported from websocket_manager module

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(llm_config.router, prefix="/api", tags=["llm-config"])
app.include_router(game_actions.router, tags=["game-actions"])
app.include_router(agent_tools.router, tags=["agent-tools"])
app.include_router(llm_admin.router, tags=["llm-admin"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Cyber Werewolves API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = None,
    room_id: str | None = Query(default=None, alias="room_id"),
    roomId: str | None = Query(default=None, alias="roomId"),
):
    """WebSocket endpoint for real-time game communication"""
    try:
        used_room_id = roomId or room_id
        await manager.connect(websocket, token, used_room_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message based on type
            await manager.handle_message(websocket, message)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
