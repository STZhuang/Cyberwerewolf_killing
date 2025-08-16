"""Agent manager for handling LLM players with dynamic configuration"""

from typing import Dict, Any, Optional
import logging
import asyncio
import httpx
from datetime import datetime

from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat

from agents.werewolf_agent import create_werewolf_agent
from agents.seer_agent import create_seer_agent
from agents.villager_agent import create_villager_agent
from agents.witch_agent import create_witch_agent
from agents.guard_agent import create_guard_agent
from agents.hunter_agent import create_hunter_agent
from agents.idiot_agent import create_idiot_agent
from agents.gm_agent import create_gm_agent
from config import settings

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent管理器 - 负责创建和管理游戏中的AI玩家"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self.game_agents: Dict[str, Dict[int, str]] = {}  # game_id -> {seat: agent_id}
        self.gm_agents: Dict[str, str] = {}  # game_id -> gm_agent_id
        self.http_client = httpx.AsyncClient(base_url=settings.api_base_url if hasattr(settings, 'api_base_url') else "http://localhost:8000")
    
    def create_agent_for_role(
        self,
        agent_id: str,
        role: str,
        custom_llm_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """为指定角色创建Agent"""
        
        try:
            # Complete role to agent mapping
            agent_creators = {
                "Werewolf": create_werewolf_agent,
                "Seer": create_seer_agent,
                "Villager": create_villager_agent,
                "Witch": create_witch_agent,
                "Guard": create_guard_agent,
                "Hunter": create_hunter_agent,
                "Idiot": create_idiot_agent
            }
            
            if role in agent_creators:
                model = self._create_model_from_config(custom_llm_config)
                agent = agent_creators[role](model)
            else:
                logger.error(f"Unknown role: {role}")
                return None
            
            self.agents[agent_id] = agent
            logger.info(f"Created {role} agent: {agent_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent for role {role}: {e}")
            return None
    
    def _create_model_from_config(self, llm_config: Optional[Dict[str, Any]] = None) -> Any:
        """从配置创建模型实例"""
        llm_config = llm_config or {}
        # 从 llm_config 的 provider_config 或 model_config 中获取配置
        provider_config = llm_config.get("provider", {})
        model_config = llm_config.get("model_config", {})

        provider = provider_config.get("type", "openai")
        # 兼容旧版，model_id 可能在 llm_config 或 model_config 中
        model_id = llm_config.get("model_id") or model_config.get("model_id", "gpt-4o-mini")

        # base_url 和 api_key 优先从 llm_config 中获取，以便于覆盖
        base_url = llm_config.get("base_url") or provider_config.get("base_url")
        api_key = llm_config.get("api_key")

        # temperature 和 max_tokens
        temperature = llm_config.get("temperature") or model_config.get("temperature", 0.7)
        max_tokens = llm_config.get("max_tokens") or model_config.get("max_tokens", 2048)

        logger.info(f"Creating model with provider: {provider}, model_id: {model_id}")

        model_params = {
            "id": model_id,
            "base_url": base_url,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # 移除值为 None 的参数
        model_params = {k: v for k, v in model_params.items() if v is not None}

        if provider == "anthropic":
            return Claude(**model_params)

        # 默认为 openai
        return OpenAIChat(**model_params)

    async def create_agent_with_dynamic_config(
        self,
        agent_id: str,
        role: str,
        room_id: Optional[str] = None,
        seat: Optional[int] = None
    ) -> Optional[Any]:
        """使用动态LLM配置创建Agent"""
        
        try:
            # Resolve model configuration via D01 API
            model_config = await self._resolve_model_config(
                room_id=room_id,
                seat=seat,
                role=role
            )
            
            # Create agent with resolved provider
            agent = self.create_agent_for_role(agent_id, role, custom_llm_config=model_config)
            
            # Store configuration for later reference
            if hasattr(agent, 'model_config'):
                agent.model_config = model_config
            
            logger.info(f"Created {role} agent {agent_id} with dynamic config: {model_config.get('model_config', {}).get('model_id', 'unknown')}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent with dynamic config, falling back to default: {e}")
            # Fallback to regular creation
            return self.create_agent_for_role(agent_id, role)
    
    async def _resolve_model_config(
        self,
        room_id: Optional[str] = None,
        seat: Optional[int] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """通过D01 API解析LLM模型配置"""
        
        params = {}
        if room_id:
            params['room_id'] = room_id
        if seat:
            params['seat'] = seat
        if role:
            params['role'] = role
        
        try:
            response = await self.http_client.get("/api/resolve-model", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to resolve model config: {e}, using defaults")
            # Return default configuration
            return {
                "provider": {
                    "id": "prov-openai-default",
                    "type": "openai",
                    "base_url": "https://api.openai.com/v1"
                },
                "model_config": {
                    "model_id": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "tools_allowed": True
                }
            }
    
    def create_gm_agent(self, game_id: str, custom_llm_config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """创建GM Agent"""
        
        try:
            gm_agent_id = f"gm_{game_id}"

            # 使用与角色 Agent 相同的逻辑创建模型
            model_config = custom_llm_config or {}
            if not model_config.get("model_id") and not model_config.get("model_config", {}).get("model_id"):
                 # 为 GM 使用更强大的模型
                 model_config.setdefault("model_config", {})["model_id"] = "gpt-4o"

            model = self._create_model_from_config(model_config)
            agent = create_gm_agent(model)
            
            self.agents[gm_agent_id] = agent
            self.gm_agents[game_id] = gm_agent_id
            
            logger.info(f"Created GM agent for game {game_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating GM agent: {e}")
            return None
    
    def register_game_agent(self, game_id: str, seat: int, agent_id: str):
        """注册游戏中的Agent"""
        if game_id not in self.game_agents:
            self.game_agents[game_id] = {}
        
        self.game_agents[game_id][seat] = agent_id
        logger.info(f"Registered agent {agent_id} for game {game_id}, seat {seat}")
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """获取Agent实例"""
        return self.agents.get(agent_id)
    
    def get_game_agent(self, game_id: str, seat: int) -> Optional[Any]:
        """获取游戏中指定座位的Agent"""
        game_agents = self.game_agents.get(game_id, {})
        agent_id = game_agents.get(seat)
        
        if agent_id:
            return self.agents.get(agent_id)
        return None
    
    def get_gm_agent(self, game_id: str) -> Optional[Any]:
        """获取游戏的GM Agent"""
        gm_agent_id = self.gm_agents.get(game_id)
        if gm_agent_id:
            return self.agents.get(gm_agent_id)
        return None
    
    async def process_agent_decision(
        self, 
        game_id: str, 
        seat: int, 
        context: Dict[str, Any],
        prompt: str
    ) -> Dict[str, Any]:
        """处理Agent决策"""
        
        try:
            agent = self.get_game_agent(game_id, seat)
            if not agent:
                raise ValueError(f"No agent found for game {game_id}, seat {seat}")
            
            # Format context into a readable prompt
            context_prompt = self._format_context_prompt(context, prompt)
            
            logger.info(f"Processing decision for agent at game {game_id}, seat {seat}")
            
            # Set agent context for tool execution
            from tools.game_tools import set_agent_context
            set_agent_context(game_id, seat)
            
            # Run agent
            response = await agent.arun(context_prompt)
            
            # Extract tool calls from response
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_calls.append({
                        "tool": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })
            
            return {
                "response": response.content if hasattr(response, 'content') else str(response),
                "tool_calls": tool_calls,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing agent decision: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def ask_gm(self, game_id: str, question: str) -> str:
        """向GM提问"""
        
        try:
            gm_agent = self.get_gm_agent(game_id)
            if not gm_agent:
                return "GM不可用，请稍后重试。"
            
            prompt = f"玩家询问：{question}\n\n请基于狼人杀规则给出回答。"
            
            response = await gm_agent.arun(prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Error asking GM: {e}")
            return "抱歉，GM暂时无法回答您的问题。"
    
    def _format_context_prompt(self, context: Dict[str, Any], additional_prompt: str = "") -> str:
        """格式化上下文为Agent可读的提示"""
        
        observation = context.get("observation", {})
        game_info = observation.get("game_info", {})
        self_info = observation.get("self", {})
        public_state = observation.get("public_state", {})
        chat_history = observation.get("chat_history", {})
        private_notes = observation.get("private_notes", [])
        allowed_actions = context.get("allowed_actions", [])
        
        prompt = f"""
**当前游戏状态：**
- 游戏ID: {game_info.get('game_id', 'unknown')}
- 回合: {game_info.get('round', 0)}
- 阶段: {game_info.get('phase', 'unknown')}
- 截止时间: {game_info.get('phase_deadline_ts', '无')}

**你的信息：**
- 座位: {self_info.get('seat', 'unknown')}
- 角色: {self_info.get('role', 'unknown')}
- 存活: {'是' if self_info.get('alive', True) else '否'}
- 状态: {self_info.get('status', {})}

**公开信息：**
- 玩家总数: {public_state.get('player_count', 0)}
- 存活玩家: {public_state.get('alive_seats', [])}
- 已公开身份: {public_state.get('revealed_identities', [])}
- 昨夜结果: {public_state.get('last_night_result', {})}

**最近发言：**
"""
        
        # Add public chat
        public_chat = chat_history.get("public_chat_tail", [])
        if public_chat:
            prompt += "公共发言：\n"
            for msg in public_chat[-10:]:  # Last 10 messages
                prompt += f"  {msg.get('seat', '?')}号: {msg.get('text', '')}\n"
        
        # Add team chat if available
        team_chat = chat_history.get("team_chat_tail", [])
        if team_chat:
            prompt += "\n队内发言：\n"
            for msg in team_chat[-5:]:  # Last 5 team messages
                prompt += f"  {msg.get('seat', '?')}号: {msg.get('text', '')}\n"
        
        # Add private notes
        if private_notes:
            prompt += "\n**私密通知：**\n"
            for note in private_notes[-5:]:  # Last 5 notes
                prompt += f"  {note.get('content', '')}\n"
        
        # Add allowed actions
        prompt += f"\n**可用行动：** {', '.join(allowed_actions)}\n"
        
        # Add additional prompt
        if additional_prompt:
            prompt += f"\n**当前任务：** {additional_prompt}\n"
        
        prompt += "\n请根据当前状态做出最佳决策。记住要使用相应的工具函数来执行你的行动。"
        
        return prompt
    
    def cleanup_game_agents(self, game_id: str):
        """清理游戏结束后的Agent"""
        
        try:
            # Remove game agents
            if game_id in self.game_agents:
                game_agent_ids = list(self.game_agents[game_id].values())
                for agent_id in game_agent_ids:
                    if agent_id in self.agents:
                        del self.agents[agent_id]
                del self.game_agents[game_id]
            
            # Remove GM agent
            if game_id in self.gm_agents:
                gm_agent_id = self.gm_agents[game_id]
                if gm_agent_id in self.agents:
                    del self.agents[gm_agent_id]
                del self.gm_agents[game_id]
            
            logger.info(f"Cleaned up agents for game {game_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up agents for game {game_id}: {e}")
    
    async def shutdown(self):
        """关闭Agent管理器，清理资源"""
        try:
            await self.http_client.aclose()
            logger.info("Agent manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global agent manager instance
agent_manager = AgentManager()