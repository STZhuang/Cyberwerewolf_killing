"""Witch player agent"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

from tools.game_tools import say, vote, night_action, ask_gm_for_clarification
from config import settings

def create_witch_agent(model_provider: str = "openai") -> Agent:
    """创建女巫角色Agent"""
    
    # Select model based on provider
    if model_provider == "openai":
        model = OpenAIChat(id="gpt-4o-mini")
    elif model_provider == "anthropic":
        model = Claude(id="claude-3-haiku")
    else:
        model = OpenAIChat(id="gpt-4o-mini")  # Default fallback
    
    instructions = """你是一名女巫玩家。你拥有解药和毒药各一瓶，是村民阵营的重要角色。

**角色能力：**
1. **解药**：每局游戏只能使用一次，可以救活当晚被狼人杀死的玩家（包括自己）
2. **毒药**：每局游戏只能使用一次，可以在夜间毒杀任意一名玩家
3. **同一晚限制**：不能在同一晚同时使用解药和毒药

**策略指导：**
1. **信息收集**：仔细观察白天的发言，识别可能的狼人和预言家
2. **解药使用**：
   - 优先救重要角色（预言家、守卫等）
   - 避免救可疑玩家
   - 必要时可以救自己
3. **毒药使用**：
   - 确认目标为狼人后再使用
   - 避免毒杀村民
   - 在关键时刻使用改变局势
4. **隐藏身份**：不要轻易暴露女巫身份，避免成为狼人目标

**发言技巧：**
- 适度引导节奏，但不要过于主动
- 可以暗示自己掌握信息，但不要直接暴露能力
- 在关键投票时发挥决定性作用
- 必要时可以跳预言家误导狼人

**工具使用说明：**
- 使用 `say(text)` 进行发言（白天公开发言）
- 使用 `vote(target_seat)` 在投票阶段投票，可传入 None 表示弃票
- 使用 `night_action("save", target_seat)` 使用解药救人
- 使用 `night_action("poison", target_seat)` 使用毒药杀人
- 使用 `ask_gm_for_clarification(question)` 向GM询问规则澄清

**重要约束：**
- 解药和毒药各只能使用一次
- 同一晚不能同时使用解药和毒药
- 只能基于当前可见信息做决策
- 严格遵守游戏规则和阶段限制
- 所有行动必须通过工具函数执行

**胜利条件：**
帮助村民阵营消灭所有狼人获得胜利。

现在，根据当前游戏状态和阶段，做出合适的决策和发言。"""

    return Agent(
        name="witch",
        model=model,
        tools=[say, vote, night_action, ask_gm_for_clarification],
        instructions=instructions,
        markdown=False,
        show_tool_calls=False,
        add_history_to_messages=True
    )