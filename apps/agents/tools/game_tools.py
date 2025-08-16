"""Game tools for Agno agents - Context-aware tool implementations"""

import httpx
from agno.tools import tool
from typing import Optional
import json
import logging
import asyncio
from contextvars import ContextVar

from config import settings

logger = logging.getLogger(__name__)

# Context variables to track current game and seat
_current_game_id: ContextVar[Optional[str]] = ContextVar('current_game_id', default=None)
_current_seat: ContextVar[Optional[int]] = ContextVar('current_seat', default=None)

# HTTP client for API calls
client = httpx.AsyncClient(base_url=settings.api_base_url)

def set_agent_context(game_id: str, seat: int):
    """Set the current agent context for tool execution"""
    _current_game_id.set(game_id)
    _current_seat.set(seat)

def get_agent_context() -> tuple[Optional[str], Optional[int]]:
    """Get the current agent context"""
    return _current_game_id.get(), _current_seat.get()

@tool
async def say(text: str) -> dict:
    """
    在当前允许的频道发言。
    在白天，这对应公共发言。在夜晚，如果角色是狼人，则对应狼人队聊。
    服务端会根据当前游戏阶段和玩家身份自动路由到正确的频道。
    """
    try:
        game_id, seat = get_agent_context()
        if not game_id or seat is None:
            return {
                "ok": False,
                "error": {"code": "NO_CONTEXT", "message": "Agent context not set"}
            }
        
        response = await client.post(
            "/agent/say",
            json={
                "game_id": game_id,
                "seat": seat,
                "text": text
            }
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Agent {seat} in game {game_id} says: {text}")
        return result
        
    except Exception as e:
        logger.error(f"Error in say tool: {e}")
        return {
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }

@tool
async def vote(target_seat: Optional[int]) -> dict:
    """
    在白天投票阶段进行投票。
    - target_seat: 要投票的席位号。
    - 若传入 null 或不传，则表示弃票。
    服务端会校验目标席位是否合法（例如，不能投给已死亡的玩家）。
    """
    try:
        game_id, seat = get_agent_context()
        if not game_id or seat is None:
            return {
                "ok": False,
                "error": {"code": "NO_CONTEXT", "message": "Agent context not set"}
            }
        
        response = await client.post(
            "/agent/vote",
            json={
                "game_id": game_id,
                "seat": seat,
                "target_seat": target_seat
            }
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Agent {seat} in game {game_id} votes for: {target_seat}")
        return result
    except Exception as e:
        logger.error(f"Error in vote tool: {e}")
        return {
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }

@tool
async def night_action(action: str, target_seat: Optional[int] = None) -> dict:
    """
    在夜间执行角色技能。
    服务端会严格根据玩家的角色、技能冷却/次数限制以及当前阶段来校验此行动是否合法。
    例如：女巫不能同时使用解药和毒药；守卫不能连续两晚守护同一个人。
    
    Available actions:
    - kill: 狼人击杀
    - save: 女巫救人
    - poison: 女巫毒杀
    - inspect: 预言家查验
    - guard: 守卫保护
    """
    try:
        game_id, seat = get_agent_context()
        if not game_id or seat is None:
            return {
                "ok": False,
                "error": {"code": "NO_CONTEXT", "message": "Agent context not set"}
            }
        
        response = await client.post(
            "/agent/night-action",
            json={
                "game_id": game_id,
                "seat": seat,
                "action": action,
                "target_seat": target_seat
            }
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Agent {seat} in game {game_id} night action: {action} on seat {target_seat}")
        return result
    except Exception as e:
        logger.error(f"Error in night_action tool: {e}")
        return {
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }

@tool
async def ask_gm_for_clarification(question: str) -> dict:
    """
    向 GM 提问以澄清游戏规则或当前状态。
    此工具用于处理 Agent 对游戏机制的困惑，避免其产生不合规的行动。
    GM 的回复将通过私密消息通道返回。
    """
    try:
        game_id, seat = get_agent_context()
        if not game_id or seat is None:
            return {
                "ok": False,
                "error": {"code": "NO_CONTEXT", "message": "Agent context not set"}
            }
        
        response = await client.post(
            "/agent/ask-gm",
            json={
                "game_id": game_id,
                "seat": seat,
                "question": question
            }
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Agent {seat} in game {game_id} asks GM: {question}")
        return result
    except Exception as e:
        logger.error(f"Error in ask_gm_for_clarification tool: {e}")
        return {
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }