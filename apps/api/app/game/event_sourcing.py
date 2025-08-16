"""Event sourcing system for game replay and audit"""

from typing import Dict, Any, List, Optional, Type
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import hashlib
import logging
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session
from app.database import Event as EventModel

logger = logging.getLogger(__name__)

@dataclass
class BaseEvent(ABC):
    """基础事件类"""
    game_id: str
    timestamp: datetime
    actor: Optional[str]  # seat number or "system"
    
    @abstractmethod
    def get_event_type(self) -> str:
        pass
    
    def to_payload(self) -> Dict[str, Any]:
        """转换为载荷字典"""
        data = asdict(self)
        # Remove base fields
        data.pop("game_id", None)
        data.pop("timestamp", None) 
        data.pop("actor", None)
        return data

# System Events
@dataclass
class GameCreatedEvent(BaseEvent):
    config: Dict[str, Any]
    players: List[Dict[str, Any]]
    
    def get_event_type(self) -> str:
        return "GameCreated"

@dataclass
class RolesAssignedEvent(BaseEvent):
    assignments: List[Dict[str, Any]]
    seed: str
    
    def get_event_type(self) -> str:
        return "RolesAssigned"

@dataclass
class PhaseChangedEvent(BaseEvent):
    from_phase: str
    to_phase: str
    round_number: int
    deadline: Optional[int] = None
    
    def get_event_type(self) -> str:
        return "PhaseChanged"

@dataclass
class TimerStartedEvent(BaseEvent):
    phase: str
    duration_seconds: int
    deadline: int
    
    def get_event_type(self) -> str:
        return "TimerStarted"

@dataclass
class TimerEndedEvent(BaseEvent):
    phase: str
    
    def get_event_type(self) -> str:
        return "TimerEnded"

@dataclass
class PlayerDiedEvent(BaseEvent):
    seat: int
    cause: str  # "voted", "killed", "poisoned"
    
    def get_event_type(self) -> str:
        return "PlayerDied"

@dataclass
class GameEndedEvent(BaseEvent):
    winner: str
    final_state: Dict[str, Any]
    
    def get_event_type(self) -> str:
        return "GameEnded"

# Action Events
@dataclass
class SpeakEvent(BaseEvent):
    seat: int
    content: str
    phase: str
    visibility: str = "public"  # public/team/private
    
    def get_event_type(self) -> str:
        return "Speak"

@dataclass
class VoteEvent(BaseEvent):
    seat: int
    target_seat: Optional[int]
    phase: str
    
    def get_event_type(self) -> str:
        return "Vote"

@dataclass
class VoteResultEvent(BaseEvent):
    votes: Dict[int, Optional[int]]  # voter -> target
    executed_seat: Optional[int]
    reason: str
    
    def get_event_type(self) -> str:
        return "VoteResult"

@dataclass
class NightActionEvent(BaseEvent):
    seat: int
    action: str
    target_seat: Optional[int]
    role: str
    
    def get_event_type(self) -> str:
        return "NightAction"

@dataclass
class NightResultEvent(BaseEvent):
    results: Dict[str, Any]
    
    def get_event_type(self) -> str:
        return "NightResult"

@dataclass
class SystemNoticeEvent(BaseEvent):
    message: str
    target_seats: Optional[List[int]] = None
    visibility: str = "public"
    
    def get_event_type(self) -> str:
        return "SystemNotice"

# Agent Events  
@dataclass
class AgentDecisionRequestedEvent(BaseEvent):
    seat: int
    context_hash: str
    allowed_actions: List[str]
    
    def get_event_type(self) -> str:
        return "AgentDecisionRequested"

@dataclass
class AgentDecisionProducedEvent(BaseEvent):
    seat: int
    decision: Dict[str, Any]
    model_info: Dict[str, Any]
    
    def get_event_type(self) -> str:
        return "AgentDecisionProduced"

class EventStore:
    """事件存储"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def append_event(self, event: BaseEvent) -> str:
        """追加事件到存储"""
        
        # Get last event to calculate hash chain
        last_event = self.db.query(EventModel).filter(
            EventModel.game_id == event.game_id
        ).order_by(EventModel.idx.desc()).first()
        
        # Calculate next index
        next_idx = (last_event.idx + 1) if last_event else 0
        
        # Calculate hash
        payload = event.to_payload()
        payload_json = json.dumps(payload, sort_keys=True)
        
        hash_input = f"{last_event.hash if last_event else ''}{event.get_event_type()}{payload_json}{next_idx}{event.timestamp.isoformat()}"
        event_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Create event record
        event_record = EventModel(
            game_id=event.game_id,
            idx=next_idx,
            timestamp=event.timestamp,
            type=event.get_event_type(),
            actor=event.actor,
            payload=payload,
            hash=event_hash,
            prev_hash=last_event.hash if last_event else None
        )
        
        self.db.add(event_record)
        self.db.commit()
        self.db.refresh(event_record)
        
        logger.info(f"Appended event {event.get_event_type()} (idx={next_idx}) to game {event.game_id}")
        
        return event_record.id
    
    def get_events(
        self, 
        game_id: str, 
        from_idx: int = 0, 
        to_idx: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[EventModel]:
        """获取事件列表"""
        
        query = self.db.query(EventModel).filter(
            EventModel.game_id == game_id,
            EventModel.idx >= from_idx
        )
        
        if to_idx is not None:
            query = query.filter(EventModel.idx <= to_idx)
        
        query = query.order_by(EventModel.idx)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_latest_event(self, game_id: str) -> Optional[EventModel]:
        """获取最新事件"""
        return self.db.query(EventModel).filter(
            EventModel.game_id == game_id
        ).order_by(EventModel.idx.desc()).first()
    
    def verify_chain_integrity(self, game_id: str) -> bool:
        """验证事件链完整性"""
        events = self.get_events(game_id)
        
        prev_hash = None
        for event in events:
            # Recalculate hash
            payload_json = json.dumps(event.payload, sort_keys=True)
            hash_input = f"{prev_hash or ''}{event.type}{payload_json}{event.idx}{event.timestamp.isoformat()}"
            calculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            if calculated_hash != event.hash:
                logger.error(f"Hash mismatch at event {event.idx} in game {game_id}")
                return False
                
            if event.prev_hash != prev_hash:
                logger.error(f"Chain break at event {event.idx} in game {game_id}")
                return False
            
            prev_hash = event.hash
        
        return True

class EventPublisher:
    """事件发布器 - 用于通知外部系统"""
    
    def __init__(self):
        self.subscribers: List = []
    
    def subscribe(self, handler):
        """订阅事件"""
        self.subscribers.append(handler)
    
    def publish(self, event: BaseEvent):
        """发布事件，支持同步与异步处理器"""
        import asyncio
        import inspect
        for handler in self.subscribers:
            try:
                if inspect.iscoroutinefunction(handler):
                    # Schedule async handler without blocking
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

class GameEventManager:
    """游戏事件管理器"""
    
    def __init__(self, db: Session):
        self.event_store = EventStore(db)
        self.publisher = EventPublisher()
    
    def emit(self, event: BaseEvent) -> str:
        """发出事件"""
        # Store event
        event_id = self.event_store.append_event(event)
        
        # Publish to subscribers
        self.publisher.publish(event)
        
        return event_id
    
    def replay_game(self, game_id: str, to_idx: Optional[int] = None) -> List[Dict[str, Any]]:
        """重放游戏到指定事件"""
        events = self.event_store.get_events(game_id, to_idx=to_idx)
        
        replay_data = []
        for event in events:
            replay_data.append({
                "idx": event.idx,
                "timestamp": event.timestamp.isoformat(),
                "type": event.type,
                "actor": event.actor,
                "payload": event.payload
            })
        
        return replay_data
    
    def get_game_summary(self, game_id: str) -> Dict[str, Any]:
        """获取游戏摘要"""
        events = self.event_store.get_events(game_id)
        
        summary = {
            "game_id": game_id,
            "total_events": len(events),
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": None,
            "winner": None,
            "rounds": 0,
            "phases": []
        }
        
        for event in events:
            if event.type == "GameEnded":
                summary["end_time"] = event.timestamp.isoformat()
                summary["winner"] = event.payload.get("winner")
            elif event.type == "PhaseChanged":
                summary["rounds"] = max(summary["rounds"], event.payload.get("round_number", 0))
                summary["phases"].append({
                    "phase": event.payload.get("to_phase"),
                    "round": event.payload.get("round_number"),
                    "timestamp": event.timestamp.isoformat()
                })
        
        return summary
