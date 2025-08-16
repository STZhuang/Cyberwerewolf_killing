"""Room management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import random
import string
import logging

from app.database import get_db, Room, RoomMember, User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class RoomConfig(BaseModel):
    max_players: int = 9
    roles: List[str] = [
        "Villager", "Villager", "Werewolf", "Werewolf", 
        "Seer", "Witch", "Guard", "Hunter", "Idiot"
    ]
    phase_durations: dict = {
        "Night": 25,
        "DayTalk": 120,
        "Vote": 30,
        "Trial": 20
    }

class CreateRoomRequest(BaseModel):
    max_players: Optional[int] = 9
    config: Optional[RoomConfig] = None

class RoomResponse(BaseModel):
    id: str
    code: str
    status: str
    max_players: int
    config: dict
    host: dict
    members: List[dict] = []

def generate_room_code() -> str:
    """Generate a unique room code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

@router.post("/", response_model=RoomResponse)
async def create_room(
    request: CreateRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new room"""
    
    # Generate unique room code
    while True:
        code = generate_room_code()
        existing = db.query(Room).filter(Room.code == code).first()
        if not existing:
            break
    
    # Create room config
    config = request.config.dict() if request.config else RoomConfig().dict()
    
    # Create room
    room = Room(
        id=str(uuid.uuid4()),
        code=code,
        host_id=current_user.id,
        max_players=request.max_players or 9,
        config=config,
        status="open"
    )
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    # Add host as first member
    member = RoomMember(
        room_id=room.id,
        user_id=current_user.id,
        seat=1,
        is_bot=False
    )
    db.add(member)
    db.commit()
    
    return RoomResponse(
        id=room.id,
        code=room.code,
        status=room.status,
        max_players=room.max_players,
        config=room.config,
        host={
            "id": current_user.id,
            "username": current_user.username
        },
        members=[{
            "user_id": current_user.id,
            "username": current_user.username,
            "seat": 1,
            "is_bot": False
        }]
    )

@router.get("/", response_model=List[RoomResponse])
async def list_rooms(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List available rooms"""
    
    query = db.query(Room)
    if status:
        query = query.filter(Room.status == status)
    
    rooms = query.all()
    
    room_list = []
    for room in rooms:
        # Get host info
        host = db.query(User).filter(User.id == room.host_id).first()
        
        # Get members
        members = db.query(RoomMember, User).join(User).filter(
            RoomMember.room_id == room.id,
            RoomMember.left_at.is_(None)
        ).all()
        
        room_list.append(RoomResponse(
            id=room.id,
            code=room.code,
            status=room.status,
            max_players=room.max_players,
            config=room.config,
            host={
                "id": host.id,
                "username": host.username
            },
            members=[{
                "user_id": member.User.id,
                "username": member.User.username,
                "seat": member.RoomMember.seat,
                "is_bot": member.RoomMember.is_bot
            } for member in members]
        ))
    
    return room_list

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    db: Session = Depends(get_db)
):
    """Get room details"""
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Get host info
    host = db.query(User).filter(User.id == room.host_id).first()
    
    # Get members
    members = db.query(RoomMember, User).join(User).filter(
        RoomMember.room_id == room.id,
        RoomMember.left_at.is_(None)
    ).all()
    
    return RoomResponse(
        id=room.id,
        code=room.code,
        status=room.status,
        max_players=room.max_players,
        config=room.config,
        host={
            "id": host.id,
            "username": host.username
        },
        members=[{
            "user_id": member.User.id,
            "username": member.User.username,
            "seat": member.RoomMember.seat,
            "is_bot": member.RoomMember.is_bot
        } for member in members]
    )

@router.post("/{room_id}/join")
async def join_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a room"""
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if room.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is not available for joining"
        )
    
    # Check if user is already in room
    existing_member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
        RoomMember.left_at.is_(None)
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already in room"
        )
    
    # Check room capacity
    current_members = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.left_at.is_(None)
    ).count()
    
    if current_members >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is full"
        )
    
    # Find available seat
    occupied_seats = db.query(RoomMember.seat).filter(
        RoomMember.room_id == room_id,
        RoomMember.left_at.is_(None)
    ).all()
    occupied_seats = [seat[0] for seat in occupied_seats]
    
    available_seat = None
    for seat in range(1, room.max_players + 1):
        if seat not in occupied_seats:
            available_seat = seat
            break
    
    if not available_seat:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No available seats"
        )
    
    # Add member
    member = RoomMember(
        room_id=room_id,
        user_id=current_user.id,
        seat=available_seat,
        is_bot=False
    )
    db.add(member)
    db.commit()
    
    return {"message": "Successfully joined room", "seat": available_seat}

@router.post("/{room_id}/leave")
async def leave_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a room"""
    
    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
        RoomMember.left_at.is_(None)
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not in room"
        )
    
    # Mark as left
    from datetime import datetime
    member.left_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Successfully left room"}

@router.post("/{room_id}/start")
async def start_game(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a game in the room"""
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if room.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only host can start the game"
        )
    
    if room.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game already started or room closed"
        )
    
    # Check minimum players
    member_count = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.left_at.is_(None)
    ).count()
    
    if member_count < 6:  # Minimum for werewolf game
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Need at least 6 players to start"
        )
    
    # Create and start game using game service
    from app.game.game_service import GameService
    from app.websocket_manager import manager  # Get the WebSocket manager instance
    
    game_service = GameService(db, manager)
    manager.game_service = game_service  # Set reference
    
    try:
        # Create game
        game_id = await game_service.create_game(room_id, room.config)
        
        # Start game (assign roles and begin first phase)
        result = await game_service.start_game(game_id)
        
        # Update room status
        room.status = "playing"
        db.commit()
        
        return {
            "message": "Game started successfully",
            "game_id": game_id,
            "assignments": result.get("assignments", [])
        }
        
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start game: {str(e)}"
        )