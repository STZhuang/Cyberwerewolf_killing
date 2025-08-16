"""Core game models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class GamePhase(str, Enum):
    """游戏阶段"""
    LOBBY = "Lobby"
    ASSIGN_ROLES = "AssignRoles" 
    NIGHT = "Night"
    DAWN = "Dawn"
    DAY_TALK = "DayTalk"
    VOTE = "Vote"
    TRIAL = "Trial"
    DAY_RESULT = "DayResult"
    END = "End"

class Role(str, Enum):
    """角色类型"""
    VILLAGER = "Villager"
    WEREWOLF = "Werewolf"
    SEER = "Seer"
    WITCH = "Witch"
    GUARD = "Guard"
    HUNTER = "Hunter"
    IDIOT = "Idiot"

class Alignment(str, Enum):
    """阵营"""
    VILLAGE = "Village"
    WEREWOLF = "Werewolf"

class RoomStatus(str, Enum):
    """房间状态"""
    OPEN = "open"
    PLAYING = "playing" 
    CLOSED = "closed"

class User(BaseModel):
    """用户模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    created_at: datetime = Field(..., description="创建时间")
    banned: bool = Field(default=False, description="是否被禁用")

class RoomConfig(BaseModel):
    """房间配置"""
    roles: List[Role] = Field(..., description="角色配置")
    phase_durations: Dict[str, int] = Field(..., description="各阶段持续时间(秒)")
    max_players: int = Field(default=9, description="最大玩家数")

class Room(BaseModel):
    """房间模型"""
    id: str = Field(..., description="房间ID")
    code: str = Field(..., description="房间代码")
    host_id: str = Field(..., description="房主ID")
    status: RoomStatus = Field(..., description="房间状态")
    config: RoomConfig = Field(..., description="房间配置")
    created_at: datetime = Field(..., description="创建时间")

class Game(BaseModel):
    """游戏模型"""
    id: str = Field(..., description="游戏ID")
    room_id: str = Field(..., description="房间ID")
    seed: str = Field(..., description="随机种子")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    ended_at: Optional[datetime] = Field(None, description="结束时间")
    config: RoomConfig = Field(..., description="游戏配置")
    version: int = Field(default=1, description="版本号")
    current_phase: GamePhase = Field(default=GamePhase.LOBBY, description="当前阶段")
    current_round: int = Field(default=0, description="当前回合")

class GamePlayer(BaseModel):
    """游戏玩家"""
    game_id: str = Field(..., description="游戏ID")
    user_id: str = Field(..., description="用户ID")
    seat: int = Field(..., description="座位号")
    role: Role = Field(..., description="角色")
    alive: bool = Field(default=True, description="是否存活")
    alignment: Alignment = Field(..., description="阵营")
    is_bot: bool = Field(default=False, description="是否为AI")
    agent_id: Optional[str] = Field(None, description="Agent ID")

class EventType(str, Enum):
    """事件类型"""
    # 系统事件
    GAME_CREATED = "GameCreated"
    ROLES_ASSIGNED = "RolesAssigned"
    PHASE_CHANGED = "PhaseChanged"
    TIMER_STARTED = "TimerStarted"
    TIMER_ENDED = "TimerEnded"
    PLAYER_DIED = "PlayerDied"
    GAME_ENDED = "GameEnded"
    
    # 行为事件
    SPEAK = "Speak"
    VOTE = "Vote"
    NIGHT_ACTION = "NightAction"
    REVEAL = "Reveal"
    SYSTEM_NOTICE = "SystemNotice"
    
    # Agent事件
    AGENT_DECISION_REQUESTED = "AgentDecisionRequested"
    AGENT_DECISION_PRODUCED = "AgentDecisionProduced"

class Event(BaseModel):
    """事件模型 - 事件溯源核心"""
    id: str = Field(..., description="事件ID")
    game_id: str = Field(..., description="游戏ID")
    idx: int = Field(..., description="事件序号")
    timestamp: datetime = Field(..., description="时间戳")
    type: EventType = Field(..., description="事件类型")
    actor: Optional[str] = Field(None, description="行动者(座位号或system)")
    payload: Dict[str, Any] = Field(..., description="事件载荷")
    hash: str = Field(..., description="事件哈希")
    prev_hash: Optional[str] = Field(None, description="前一个事件哈希")

class ActionRecord(BaseModel):
    """幂等提交记录"""
    idempotency_key: str = Field(..., description="幂等键")
    request: Dict[str, Any] = Field(..., description="请求内容")
    status: str = Field(..., description="处理状态")
    result: Optional[Dict[str, Any]] = Field(None, description="处理结果")