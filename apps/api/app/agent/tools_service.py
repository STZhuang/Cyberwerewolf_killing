"""Agent tools service - implements D03 specification tool APIs"""

# Configure Python path for SDK imports
from app.path_config import *

from typing import Dict, Any, Optional, Literal
import logging
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session

from app.game.game_service import GameService
from cyber_werewolves.models.agent_models import ToolResult, GameContext
from app.agent.context_builder import AgentContextBuilder

logger = logging.getLogger(__name__)

class AgentToolsService:
    """Agent工具服务 - 提供严格约束的工具接口"""
    
    def __init__(self, db: Session, game_service: GameService):
        self.db = db
        self.game_service = game_service
        self.context_builder = AgentContextBuilder(db, game_service.state_machine)
        
    async def say(self, game_id: str, seat: int, text: str) -> ToolResult:
        """发言工具"""
        try:
            # Validate context and permissions
            context = self._get_and_validate_context(game_id, seat)
            if not self._is_action_allowed(context, "say"):
                return ToolResult(
                    ok=False,
                    error={"code": "ACTION_NOT_ALLOWED", "message": "Speaking not allowed in current context"}
                )
            
            # Content validation
            if not text or not text.strip():
                return ToolResult(
                    ok=False,
                    error={"code": "EMPTY_CONTENT", "message": "Message content cannot be empty"}
                )
            
            if len(text) > 1000:  # Length limit
                return ToolResult(
                    ok=False,
                    error={"code": "MESSAGE_TOO_LONG", "message": "Message exceeds maximum length"}
                )
            
            # Submit through game service
            result = await self.game_service.submit_speak(game_id, seat, text.strip())
            
            return ToolResult(
                ok=True,
                message="Message sent successfully",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error in say tool: {e}")
            return ToolResult(
                ok=False,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
    
    async def vote(self, game_id: str, seat: int, target_seat: Optional[int]) -> ToolResult:
        """投票工具"""
        try:
            # Validate context and permissions
            context = self._get_and_validate_context(game_id, seat)
            if not self._is_action_allowed(context, "vote"):
                return ToolResult(
                    ok=False,
                    error={"code": "INVALID_PHASE", "message": "Voting not allowed in current phase"}
                )
            
            # Validate target
            if target_seat is not None:
                valid_targets = context.constraints.get("vote_targets", [])
                if target_seat not in valid_targets:
                    return ToolResult(
                        ok=False,
                        error={"code": "TARGET_INVALID", "message": f"Invalid vote target: {target_seat}"}
                    )
            
            # Submit through game service
            result = await self.game_service.submit_vote(game_id, seat, target_seat)
            
            return ToolResult(
                ok=True,
                message=f"Vote cast for {target_seat}" if target_seat else "Abstained from voting",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error in vote tool: {e}")
            return ToolResult(
                ok=False,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
    
    async def night_action(
        self, 
        game_id: str, 
        seat: int,
        action: Literal["kill", "save", "poison", "inspect", "guard"],
        target_seat: Optional[int] = None
    ) -> ToolResult:
        """夜间行动工具"""
        try:
            # Validate context and permissions
            context = self._get_and_validate_context(game_id, seat)
            action_name = f"night_action_{action}"
            
            if not self._is_action_allowed(context, action_name):
                return ToolResult(
                    ok=False,
                    error={"code": "SKILL_NOT_AVAILABLE", "message": f"Action {action} not available for your role"}
                )
            
            # Validate target based on action
            if target_seat is not None:
                constraint_key = f"{action}_targets"
                valid_targets = context.constraints.get(constraint_key, [])
                
                if target_seat not in valid_targets:
                    return ToolResult(
                        ok=False,
                        error={"code": "TARGET_INVALID", "message": f"Invalid {action} target: {target_seat}"}
                    )
            
            # Some actions require targets
            if action in ["kill", "inspect", "guard", "save", "poison"] and target_seat is None:
                return ToolResult(
                    ok=False,
                    error={"code": "TARGET_REQUIRED", "message": f"Action {action} requires a target"}
                )
            
            # Submit through game service
            result = await self.game_service.submit_night_action(game_id, seat, action, target_seat)
            
            return ToolResult(
                ok=True,
                message=f"Night action {action} submitted successfully",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error in night_action tool: {e}")
            return ToolResult(
                ok=False,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
    
    async def ask_gm_for_clarification(self, game_id: str, seat: int, question: str) -> ToolResult:
        """向GM询问澄清"""
        try:
            # Basic validation
            if not question or not question.strip():
                return ToolResult(
                    ok=False,
                    error={"code": "EMPTY_QUESTION", "message": "Question cannot be empty"}
                )
            
            if len(question) > 500:
                return ToolResult(
                    ok=False,
                    error={"code": "QUESTION_TOO_LONG", "message": "Question exceeds maximum length"}
                )
            
            # Log the question for GM review
            logger.info(f"Agent question from game {game_id}, seat {seat}: {question}")
            
            # Call the agent service to ask GM
            import httpx
            import asyncio
            
            async def notify_gm():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "http://localhost:8001/gm/ask",
                            json={
                                "game_id": game_id,
                                "question": question.strip()
                            },
                            timeout=10.0
                        )
                        response.raise_for_status()
                        return response.json()
                except Exception as e:
                    logger.warning(f"Failed to notify GM: {e}")
                    return {"response": "GM is currently unavailable, but your question has been recorded."}
            
            # Execute GM notification
            gm_response = await notify_gm()
            
            return ToolResult(
                ok=True,
                message="Question submitted to GM",
                data={
                    "question": question.strip(),
                    "gm_response": gm_response.get("response", "No response from GM"),
                    "status": "answered",
                    "response": "Your question has been recorded. The GM will respond during the next appropriate phase."
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ask_gm_for_clarification tool: {e}")
            return ToolResult(
                ok=False,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
    
    def _get_and_validate_context(self, game_id: str, seat: int) -> GameContext:
        """获取并验证上下文"""
        
        # Build observation
        observation = self.context_builder.build_observation(game_id, seat)
        
        # Get allowed actions and constraints
        allowed_actions = self.context_builder.get_allowed_actions(game_id, seat)
        constraints = self.context_builder.get_action_constraints(game_id, seat)
        
        return GameContext(
            observation=observation,
            allowed_actions=allowed_actions,
            constraints=constraints
        )
    
    def _is_action_allowed(self, context: GameContext, action: str) -> bool:
        """检查行动是否被允许"""
        return action in context.allowed_actions
    
    def get_context_for_agent(self, game_id: str, seat: int) -> GameContext:
        """为Agent获取完整上下文"""
        return self._get_and_validate_context(game_id, seat)
    
    def validate_agent_request(self, game_id: str, seat: int, action: str, params: Dict[str, Any]) -> ToolResult:
        """验证Agent请求的合法性"""
        try:
            context = self._get_and_validate_context(game_id, seat)
            
            if not self._is_action_allowed(context, action):
                return ToolResult(
                    ok=False,
                    error={"code": "ACTION_NOT_ALLOWED", "message": f"Action {action} not allowed"}
                )
            
            # Additional parameter validation can be added here
            
            return ToolResult(ok=True, message="Request is valid")
            
        except Exception as e:
            logger.error(f"Error validating agent request: {e}")
            return ToolResult(
                ok=False,
                error={"code": "VALIDATION_ERROR", "message": str(e)}
            )
    
    def create_context_hash(self, game_id: str, seat: int) -> str:
        """创建上下文哈希用于审计"""
        context = self._get_and_validate_context(game_id, seat)
        
        # Create a deterministic hash of the visible context
        context_str = f"{game_id}:{seat}:{context.observation.game_info.round}:{context.observation.game_info.phase}:{len(context.observation.chat_history.public_chat_tail)}"
        
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]