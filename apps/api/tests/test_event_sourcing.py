"""Test event sourcing system"""

import pytest
from datetime import datetime

from app.game.event_sourcing import (
    GameCreatedEvent, SpeakEvent, VoteEvent, EventStore, 
    GameEventManager
)


@pytest.mark.unit
def test_event_creation():
    """Test creating events"""
    event = GameCreatedEvent(
        game_id="test-game",
        timestamp=datetime.utcnow(),
        actor="system",
        config={"test": "config"},
        players=[{"seat": 1, "user_id": "user1"}]
    )
    
    assert event.game_id == "test-game"
    assert event.get_event_type() == "GameCreated"
    
    payload = event.to_payload()
    assert "config" in payload
    assert "players" in payload
    assert "game_id" not in payload  # Should be removed in payload


@pytest.mark.unit
def test_event_store(db_session):
    """Test event store operations"""
    event_store = EventStore(db_session)
    
    # Create test event
    event = SpeakEvent(
        game_id="test-game",
        timestamp=datetime.utcnow(),
        actor="1",
        seat=1,
        content="Hello, world!",
        phase="DayTalk",
        visibility="public"
    )
    
    # Append event
    event_id = event_store.append_event(event)
    
    assert event_id is not None
    
    # Retrieve events
    events = event_store.get_events("test-game")
    
    assert len(events) == 1
    assert events[0].type == "Speak"
    assert events[0].payload["content"] == "Hello, world!"


@pytest.mark.unit
def test_event_chain_integrity(db_session):
    """Test event chain hash integrity"""
    event_store = EventStore(db_session)
    
    # Create multiple events
    events = [
        SpeakEvent(
            game_id="test-game",
            timestamp=datetime.utcnow(),
            actor="1",
            seat=1,
            content=f"Message {i}",
            phase="DayTalk",
            visibility="public"
        )
        for i in range(3)
    ]
    
    # Append all events
    for event in events:
        event_store.append_event(event)
    
    # Verify chain integrity
    integrity_check = event_store.verify_chain_integrity("test-game")
    
    assert integrity_check is True


@pytest.mark.unit
def test_game_event_manager(db_session):
    """Test game event manager"""
    event_manager = GameEventManager(db_session)
    
    # Test event emission
    event = VoteEvent(
        game_id="test-game",
        timestamp=datetime.utcnow(),
        actor="1",
        seat=1,
        target_seat=2,
        phase="Vote"
    )
    
    event_id = event_manager.emit(event)
    
    assert event_id is not None
    
    # Test game replay
    replay_data = event_manager.replay_game("test-game")
    
    assert len(replay_data) == 1
    assert replay_data[0]["type"] == "Vote"
    assert replay_data[0]["payload"]["seat"] == 1
    assert replay_data[0]["payload"]["target_seat"] == 2


@pytest.mark.unit
def test_game_summary(db_session):
    """Test game summary generation"""
    event_manager = GameEventManager(db_session)
    
    # Create test events
    events = [
        GameCreatedEvent(
            game_id="test-game",
            timestamp=datetime.utcnow(),
            actor="system",
            config={"roles": ["Villager", "Werewolf"]},
            players=[{"seat": 1}, {"seat": 2}]
        ),
        SpeakEvent(
            game_id="test-game",
            timestamp=datetime.utcnow(),
            actor="1",
            seat=1,
            content="Test message",
            phase="DayTalk",
            visibility="public"
        )
    ]
    
    # Emit events
    for event in events:
        event_manager.emit(event)
    
    # Get summary
    summary = event_manager.get_game_summary("test-game")
    
    assert summary["game_id"] == "test-game"
    assert summary["total_events"] == 2
    assert summary["start_time"] is not None