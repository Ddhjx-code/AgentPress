"""
Mythologist Agent专门处理器
对应prompts/mythologist.md，提供跨文化符号策略
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class MythologistAgentHandler(BaseAgentHandler):
    """
    Mythologist Agent专门处理器
    对应prompts/mythologist.md，提供跨文化符号策略和创意方向
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        分析故事概念并提供跨文化符号策略

        Args:
            task: 故事概念或创作意图
            **kwargs: 额外参数

        Returns:
            包含符号分析和创意策略的JSON数据
        """
        # 构建针对mythologist角色的任务
        mythologist_task = f"""你是一位精通全球神话、民间传说、宗教象征与历史母题的创意顾问。

请分析以下故事创意，识别可嫁接的文化符号，并提供3-5个可操作的创作方向：

故事创意: {task}

请严格按照JSON格式回复，包含以下字段：
- user_concept: 用户提供的故事创意
- core_archetypes: 核心原型
- cross_cultural_sources: 跨文化资料来源
- creative_directions: 创作方向列表
- target_length: 建议长度（如果可以评估）
- symbolic_objects_to_explore: 值得探索的象征物

确保每个创作方向都提供具体的策略组合，引用'writer'代理的技巧库标准命名。"""

        result = await self.agent.run(task=mythologist_task)
        content = extract_content(result.messages)
        parsed_json = extract_all_json(content)

        # 如果未能解析出JSON，至少返回内容
        return {
            "raw_content": content,
            "parsed_json": parsed_json,
            "original_task": task,
            "agent": self.name
        }

    async def analyze_symbols(self, concept: str) -> Dict[str, Any]:
        """
        专门分析符号层面的内容

        Args:
            concept: 要分析的概念

        Returns:
            符号分析结果
        """
        symbol_analysis_task = f"""请从符号学角度分析以下概念，识别其中的跨文化符号原型：

概念: {concept}

请提供：
1. 核心符号元素识别
2. 相关跨文化原型
3. 符号的冲突张力点
4. 在故事中的可能表现形式

请按照JSON格式回复，包括以上四个部分的内容。"""

        result = await self.agent.run(task=symbol_analysis_task)
        content = extract_content(result.messages)
        parsed_json = extract_all_json(content)

        return {
            "symbol_analysis": parsed_json,
            "raw_content": content,
            "concept": concept,
            "agent": self.name
        }