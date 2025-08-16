"""Agent manager for handling LLM players with dynamic configuration"""

from typing import Dict, Any, Optional
import logging
import asyncio
import httpx
from datetime import datetime

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
        model_provider: str = "openai",
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
                # 如果提供了自定义 LLM 配置，使用它创建 agent
                if custom_llm_config:
                    agent = self._create_agent_with_custom_llm(
                        role, agent_creators[role], custom_llm_config
                    )
                else:
                    agent = agent_creators[role](model_provider)
            else:
                logger.error(f"Unknown role: {role}")
                return None
            
            self.agents[agent_id] = agent
            logger.info(f"Created {role} agent: {agent_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent for role {role}: {e}")
            return None
    
    def _create_agent_with_custom_llm(
        self, 
        role: str, 
        agent_creator, 
        llm_config: Dict[str, Any]
    ) -> Optional[Any]:
        """使用自定义 LLM 配置创建 Agent"""
        
        try:
            from agno.models.openai import OpenAIChat
            from agno.agent import Agent
            
            # 创建自定义的 OpenAIChat 实例
            custom_model = OpenAIChat(
                id=llm_config.get("model_id", "gpt-4o-mini"),
                base_url=llm_config.get("base_url", "https://api.openai.com/v1"),
                api_key=llm_config.get("api_key") if llm_config.get("api_key") else None,
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 2048)
            )
            
            # 获取角色特定的配置（工具和指令）
            agent_config = self._get_role_config(role)
            
            # 创建 Agent 实例
            agent = Agent(
                name=f"{role} Agent",
                model=custom_model,
                tools=agent_config["tools"],
                instructions=agent_config["instructions"],
                markdown=False,
                show_tool_calls=False,
                add_history_to_messages=True
            )
            
            logger.info(f"Created {role} agent with custom LLM: {llm_config['model_id']}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent with custom LLM: {e}")
            return None
    
    def _get_role_config(self, role: str) -> Dict[str, Any]:
        """获取角色特定的工具和指令配置"""
        
        from tools.game_tools import say, vote, night_action, ask_gm_for_clarification
        
        base_tools = [say, vote, ask_gm_for_clarification]
        
        # 角色特定的配置
        role_configs = {
            "Werewolf": {
                "tools": base_tools + [night_action],
                "instructions": """你是狼人阵营的玩家。目标：消灭所有村民阵营玩家。
                
**夜间行动：**
- 与其他狼人协商击杀目标
- 使用 `night_action('kill', target_seat)` 击杀村民
                
**白天策略：**
- 隐藏身份，伪装成村民
- 引导村民投票其他玩家
- 支持对村民有利的提案来获取信任"""
            },
            "Seer": {
                "tools": base_tools + [night_action],
                "instructions": """你是预言家，村民阵营的重要角色。目标：找出狼人并引导村民获胜。

**夜间行动：**
- 使用 `night_action('inspect', target_seat)` 查验玩家身份
- 优先查验可疑玩家

**白天策略：**
- 适时公布查验结果
- 引导村民投票狼人
- 保护其他村民角色"""
            },
            "Witch": {
                "tools": base_tools + [night_action],
                "instructions": """你是女巫，拥有解药和毒药各一瓶。目标：帮助村民阵营获胜。

**夜间行动：**
- 使用 `night_action('save', target_seat)` 救人（解药）
- 使用 `night_action('poison', target_seat)` 毒杀（毒药）
- 每种药水只能使用一次，同一晚不能同时使用

**白天策略：**
- 隐藏身份，避免被狼人针对
- 根据情况选择性透露信息"""
            },
            "Guard": {
                "tools": base_tools + [night_action],
                "instructions": """你是守卫，可以保护其他玩家。目标：帮助村民阵营获胜。

**夜间行动：**
- 使用 `night_action('guard', target_seat)` 守护玩家
- 不能守护自己
- 不能连续两晚守护同一玩家

**白天策略：**
- 保持低调，避免暴露身份
- 观察并分析可疑行为"""
            },
            "Villager": {
                "tools": base_tools,
                "instructions": """你是普通村民。目标：通过逻辑推理找出狼人。

**白天策略：**
- 仔细听取发言，分析逻辑漏洞
- 支持神职角色的判断
- 避免跟风投票，要有自己的理由"""
            },
            "Hunter": {
                "tools": base_tools,
                "instructions": """你是猎人，死亡时可以开枪带走一名玩家。目标：帮助村民阵营获胜。

**白天策略：**
- 保持低调，避免被狼人针对
- 准备好开枪目标（系统会在你死亡时处理）"""
            },
            "Idiot": {
                "tools": base_tools,
                "instructions": """你是白痴，被投票出局时会翻牌但不死亡，失去投票权但保留发言权。

**白天策略：**
- 可以相对激进地发言
- 身份暴露后继续帮助村民分析"""
            }
        }
        
        return role_configs.get(role, {
            "tools": base_tools,
            "instructions": f"你是 {role} 角色，请根据游戏规则行动。"
        })
    
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
            
            # Get the appropriate agent creator
            agent_creators = {
                "Werewolf": create_werewolf_agent,
                "Seer": create_seer_agent,
                "Villager": create_villager_agent,
                "Witch": create_witch_agent,
                "Guard": create_guard_agent,
                "Hunter": create_hunter_agent,
                "Idiot": create_idiot_agent
            }
            
            if role not in agent_creators:
                logger.error(f"Unknown role: {role}")
                return None
            
            # Determine model provider from configuration
            provider_type = model_config.get("provider", {}).get("type", "openai")
            
            # Create agent with resolved provider
            agent = agent_creators[role](provider_type)
            
            # Store configuration for later reference
            if hasattr(agent, 'model_config'):
                agent.model_config = model_config
            
            self.agents[agent_id] = agent
            logger.info(f"Created {role} agent {agent_id} with dynamic config: {model_config.get('model_config', {}).get('model_id', 'unknown')}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent with dynamic config, falling back to default: {e}")
            # Fallback to regular creation
            return self.create_agent_for_role(agent_id, role, "openai")
    
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
    
    def create_gm_agent(self, game_id: str, model_provider: str = "openai") -> Optional[Any]:
        """创建GM Agent"""
        
        try:
            gm_agent_id = f"gm_{game_id}"
            agent = create_gm_agent(model_provider)
            
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