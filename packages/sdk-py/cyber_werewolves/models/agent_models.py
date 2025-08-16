"""Agent observation and context models - implements D03 specification"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .game_models import GamePhase, Role

class GameInfo(BaseModel):
    """游戏基础信息"""
    game_id: str = Field(..., description="游戏ID")
    round: int = Field(..., description="当前回合")
    phase: GamePhase = Field(..., description="当前阶段")
    phase_deadline_ts: Optional[int] = Field(None, description="阶段截止时间戳")

class SelfInfo(BaseModel):
    """自身信息"""
    seat: int = Field(..., description="座位号")
    alive: bool = Field(..., description="是否存活")
    role: Role = Field(..., description="角色")
    status: Dict[str, Any] = Field(default_factory=dict, description="角色相关状态")

class PublicState(BaseModel):
    """公开状态"""
    player_count: int = Field(..., description="玩家总数")
    alive_seats: List[int] = Field(..., description="存活座位列表")
    revealed_identities: List[Dict[str, Any]] = Field(default_factory=list, description="已公开身份")
    last_night_result: Dict[str, Any] = Field(default_factory=dict, description="上夜结果")

class ChatMessage(BaseModel):
    """聊天消息"""
    idx: int = Field(..., description="消息序号")
    seat: int = Field(..., description="发言者座位")
    text: str = Field(..., description="消息内容")

class ChatHistory(BaseModel):
    """聊天历史"""
    public_chat_tail: List[ChatMessage] = Field(default_factory=list, description="最近公共发言")
    team_chat_tail: List[ChatMessage] = Field(default_factory=list, description="队内聊天")

class PrivateNote(BaseModel):
    """私密通知"""
    idx: int = Field(..., description="通知序号")
    content: str = Field(..., description="通知内容")

class AgentObservation(BaseModel):
    """Agent可见上下文 - 严格信息隔离"""
    game_info: GameInfo = Field(..., description="游戏信息")
    self: SelfInfo = Field(..., description="自身信息")  
    public_state: PublicState = Field(..., description="公开状态")
    chat_history: ChatHistory = Field(..., description="聊天历史")
    private_notes: List[PrivateNote] = Field(default_factory=list, description="私密通知")

class GameContext(BaseModel):
    """游戏上下文 - 用于Agent决策"""
    observation: AgentObservation = Field(..., description="可见观察")
    allowed_actions: List[str] = Field(..., description="允许的行动列表")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="行动约束")

class ToolResult(BaseModel):
    """工具调用结果"""
    ok: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="结果消息")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    error: Optional[Dict[str, str]] = Field(None, description="错误信息")