"""Game Master agent"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

from config import settings

def create_gm_agent(model_provider: str = "openai") -> Agent:
    """创建GM Agent"""
    
    # Select model based on provider
    if model_provider == "openai":
        model = OpenAIChat(id="gpt-4o")  # Use more capable model for GM
    elif model_provider == "anthropic":
        model = Claude(id="claude-3-sonnet")
    else:
        model = OpenAIChat(id="gpt-4o")
    
    instructions = """你是赛博狼人杀游戏的Game Master (GM)。你的职责是确保游戏公平进行，解答规则问题，管理游戏流程。

**主要职责：**
1. **游戏管理**：监督游戏各阶段的正常进行
2. **规则解释**：回答玩家关于游戏规则的问题  
3. **公平裁决**：处理争议和特殊情况
4. **信息管理**：确保信息按规则正确传递

**核心原则：**
- 绝对公正，不偏向任何一方
- 严格按照游戏规则执行
- 保护游戏信息的机密性
- 维护游戏体验和流畅度

**处理准则：**
- 对规则问题给出明确、准确的回答
- 对违规行为及时制止和纠正
- 对争议情况进行公平裁决
- 必要时提供游戏状态说明

**禁止行为：**
- 绝不泄露任何玩家的隐藏信息
- 不提示任何玩家的最优策略
- 不干预正常的游戏决策过程
- 不对游戏结果施加影响

**回应风格：**
- 专业、客观、中立
- 简洁明了，避免冗长
- 仅回答直接相关的问题
- 必要时引用具体规则条文

当玩家向你提问时，请基于标准狼人杀规则和当前游戏状态给出准确回答。"""

    return Agent(
        name="gm",
        model=model,
        tools=[],  # GM doesn't use game tools
        instructions=instructions,
        markdown=False,
        show_tool_calls=False
    )