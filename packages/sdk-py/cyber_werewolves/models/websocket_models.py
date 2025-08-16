"""WebSocket message models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class MessageType(str, Enum):
    """WebSocket消息类型"""
    SPEAK = "speak"
    VOTE = "vote" 
    NIGHT_ACTION = "night_action"
    SYSTEM = "system"
    STATE = "state"
    ACK = "ack"
    ERROR = "error"

class Visibility(str, Enum):
    """消息可见性"""
    PUBLIC = "public"
    TEAM = "team"
    PRIVATE = "private"
    SYSTEM = "system"

class WebSocketMessage(BaseModel):
    """WebSocket消息统一格式"""
    type: MessageType = Field(..., description="消息类型")
    req_id: Optional[str] = Field(None, description="请求ID")
    timestamp: int = Field(..., description="时间戳")
    payload: Dict[str, Any] = Field(..., description="消息载荷")

class SpeakPayload(BaseModel):
    """发言载荷"""
    content: str = Field(..., description="发言内容")

class VotePayload(BaseModel):
    """投票载荷"""
    target_seat: Optional[int] = Field(None, description="投票目标座位")

class NightActionPayload(BaseModel):
    """夜间行动载荷"""
    action: str = Field(..., description="行动类型")
    target_seat: Optional[int] = Field(None, description="目标座位")

class SystemPayload(BaseModel):
    """系统消息载荷"""
    message: str = Field(..., description="系统消息")
    phase: Optional[str] = Field(None, description="阶段信息")

class StatePayload(BaseModel):
    """状态更新载荷"""
    phase: str = Field(..., description="当前阶段")
    round: int = Field(..., description="当前回合")
    deadline: Optional[int] = Field(None, description="截止时间")
    players: List[Dict[str, Any]] = Field(..., description="玩家状态")

class ErrorPayload(BaseModel):
    """错误载荷"""
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")

class BroadcastMessage(BaseModel):
    """广播消息"""
    type: MessageType = Field(..., description="消息类型")
    payload: Dict[str, Any] = Field(..., description="消息载荷")
    visibility: Visibility = Field(default=Visibility.PUBLIC, description="可见性")
    target_seats: Optional[List[int]] = Field(None, description="目标座位列表")