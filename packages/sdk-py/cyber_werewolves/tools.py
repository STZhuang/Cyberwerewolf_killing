"""Agent tools - implements D03 specification tool APIs"""

import os
import asyncio
import httpx
from typing import Optional, Dict, Any, Literal
from .models.agent_models import ToolResult

# HTTP client for API calls
class AgentToolsClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("CYBER_WEREWOLVES_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("CYBER_WEREWOLVES_API_KEY")
        self.session = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = httpx.AsyncClient(base_url=self.base_url, headers=headers)
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        session = await self._get_session()
        try:
            response = await session.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"ok": False, "error": {"code": f"HTTP_{e.response.status_code}", "message": str(e)}}
        except Exception as e:
            return {"ok": False, "error": {"code": "REQUEST_FAILED", "message": str(e)}}

# Global client instance
_client = AgentToolsClient()

def say(game_id: str, seat: int, text: str) -> Dict[str, Any]:
    """
    在当前允许的频道发言。
    在白天，这对应公共发言。在夜晚，如果角色是狼人，则对应狼人队聊。
    服务端会根据当前游戏阶段和玩家身份自动路由到正确的频道。
    """
    try:
        # Use asyncio to run the async call
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_async_say(game_id, seat, text))
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(_async_say(game_id, seat, text))

async def _async_say(game_id: str, seat: int, text: str) -> Dict[str, Any]:
    """Async implementation of say tool"""
    return await _client._make_request(
        "POST", 
        "/agent/say", 
        json={
            "game_id": game_id,
            "seat": seat,
            "text": text
        }
    )

def vote(game_id: str, seat: int, target_seat: Optional[int]) -> Dict[str, Any]:
    """
    在白天投票阶段进行投票。
    - target_seat: 要投票的席位号。
    - 若传入 null 或不传，则表示弃票。
    服务端会校验目标席位是否合法（例如，不能投给已死亡的玩家）。
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_async_vote(game_id, seat, target_seat))
    except RuntimeError:
        return asyncio.run(_async_vote(game_id, seat, target_seat))

async def _async_vote(game_id: str, seat: int, target_seat: Optional[int]) -> Dict[str, Any]:
    """Async implementation of vote tool"""
    return await _client._make_request(
        "POST", 
        "/agent/vote", 
        json={
            "game_id": game_id,
            "seat": seat,
            "target_seat": target_seat
        }
    )

def night_action(
    game_id: str,
    seat: int,
    action: Literal["kill", "save", "poison", "inspect", "guard"],
    target_seat: Optional[int] = None
) -> Dict[str, Any]:
    """
    在夜间执行角色技能。
    服务端会严格根据玩家的角色、技能冷却/次数限制以及当前阶段来校验此行动是否合法。
    例如：女巫不能同时使用解药和毒药；守卫不能连续两晚守护同一个人。
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_async_night_action(game_id, seat, action, target_seat))
    except RuntimeError:
        return asyncio.run(_async_night_action(game_id, seat, action, target_seat))

async def _async_night_action(
    game_id: str,
    seat: int,
    action: Literal["kill", "save", "poison", "inspect", "guard"],
    target_seat: Optional[int] = None
) -> Dict[str, Any]:
    """Async implementation of night_action tool"""
    return await _client._make_request(
        "POST", 
        "/agent/night-action", 
        json={
            "game_id": game_id,
            "seat": seat,
            "action": action,
            "target_seat": target_seat
        }
    )

def ask_gm_for_clarification(game_id: str, seat: int, question: str) -> Dict[str, Any]:
    """
    向 GM 提问以澄清游戏规则或当前状态。
    此工具用于处理 Agent 对游戏机制的困惑，避免其产生不合规的行动。
    GM 的回复将通过私密消息通道返回。
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_async_ask_gm(game_id, seat, question))
    except RuntimeError:
        return asyncio.run(_async_ask_gm(game_id, seat, question))

async def _async_ask_gm(game_id: str, seat: int, question: str) -> Dict[str, Any]:
    """Async implementation of ask_gm_for_clarification tool"""
    return await _client._make_request(
        "POST", 
        "/agent/ask-gm", 
        json={
            "game_id": game_id,
            "seat": seat,
            "question": question
        }
    )