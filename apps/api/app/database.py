"""Database configuration and models"""

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Generator
import uuid
from datetime import datetime

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    banned = Column(Boolean, default=False)
    
    # Relationships
    rooms = relationship("Room", back_populates="host")
    room_memberships = relationship("RoomMember", back_populates="user")


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    host_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="open")  # open/playing/closed
    max_players = Column(Integer, default=9)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    host = relationship("User", back_populates="rooms")
    members = relationship("RoomMember", back_populates="room")
    games = relationship("Game", back_populates="room")


class RoomMember(Base):
    __tablename__ = "room_members"
    
    room_id = Column(String, ForeignKey("rooms.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    seat = Column(Integer)
    is_bot = Column(Boolean, default=False)
    agent_id = Column(String)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)
    
    # Relationships
    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="room_memberships")


class Game(Base):
    __tablename__ = "games"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    seed = Column(String, nullable=False)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    config = Column(JSON)
    version = Column(Integer, default=1)
    current_phase = Column(String, default="Lobby")
    current_round = Column(Integer, default=0)
    
    # Relationships
    room = relationship("Room", back_populates="games")
    players = relationship("GamePlayer", back_populates="game")
    events = relationship("Event", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"
    
    game_id = Column(String, ForeignKey("games.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    seat = Column(Integer, nullable=False)
    role = Column(String)
    alive = Column(Boolean, default=True)
    alignment = Column(String)
    is_bot = Column(Boolean, default=False)
    agent_id = Column(String)
    
    # Relationships
    game = relationship("Game", back_populates="players")
    user = relationship("User")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    idx = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String, nullable=False)
    actor = Column(String)  # seat number or "system"
    payload = Column(JSON)
    hash = Column(String, nullable=False)
    prev_hash = Column(String)
    
    # Relationships
    game = relationship("Game", back_populates="events")


class ActionRecord(Base):
    __tablename__ = "actions"
    
    idempotency_key = Column(String, primary_key=True)
    request = Column(JSON)
    status = Column(String)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


# LLM Configuration Models
class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)  # encrypted
    default_model = Column(String, nullable=False)
    headers = Column(JSON)
    timeout_s = Column(Integer, default=60)
    rate_limit_tpm = Column(Integer)
    rate_limit_rpm = Column(Integer)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Preset(Base):
    __tablename__ = "presets"
    
    id = Column(String, primary_key=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    model_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    temperature = Column(Integer, default=70)  # stored as int * 100
    top_p = Column(Integer, default=100)
    max_tokens = Column(Integer, default=2048)
    seed = Column(Integer)
    stop = Column(JSON)
    modalities = Column(JSON)
    tools_allowed = Column(Boolean, default=True)
    vision_max_pixels = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    provider = relationship("Provider")


class Binding(Base):
    __tablename__ = "bindings"
    
    id = Column(String, primary_key=True)
    scope = Column(String, nullable=False)  # global/room/seat/agent_role
    scope_key = Column(String, nullable=False)
    preset_id = Column(String, ForeignKey("presets.id"), nullable=False)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    preset = relationship("Preset")