"""
Fact Checker Agent专门处理器
对应prompts/fact_checker.md，负责逻辑验证和一致性检查
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class FactCheckerHandler(BaseAgentHandler):
    """
    Fact Checker Agent专门处理器
    对应prompts/fact_checker.md，负责逻辑自洽和设定一致性的验证
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        执行逻辑验证和一致性检查

        Args:
            task: 检查任务内容
            **kwargs: 额外参数

        Returns:
            包含检查结果的字典
        """
        return await self.validate_logic(task)

    async def validate_logic(self, content: str) -> Dict[str, Any]:
        """
        验证内容的逻辑自洽性

        Args:
            content: 要验证的内容

        Returns:
            逻辑验证结果
        """
        validation_task = f"""你是一位故事架构师，请检查以下内容的逻辑自洽性和设定一致性：

待检查内容:
{content}

检查要点：
1. 内在逻辑一致性（情节因果关系、角色行为动机）
2. 世界观设定的一致性（时间、地点、规则）
3. 人物设定一致性（性格、能力、关系）
4. 时间线和因果关系的合理性
5. 避免逻辑漏洞和矛盾

请提供以下格式的反馈：
- 逻辑评分（1-100）
- 发现的不一致点
- 修正建议
- 整体架构评价"""

        result = await self.agent.run(task=validation_task)
        content_result = extract_content(result.messages)
        parsed_json = extract_all_json(content_result)

        return {
            "validation_result": parsed_json,
            "raw_content": content_result,
            "checked_content_length": len(content),
            "agent": self.name
        }

    async def check_building_strategies(self, content: str, context: str = None) -> Dict[str, Any]:
        """
        检查内容并应用构建策略

        Args:
            content: 要检查的内容
            context: 相关上下文

        Returns:
            带有构建策略建议的检查结果
        """
        building_task = f"""你是一位故事架构师，专门运用构建策略库来强化故事的逻辑架构。

待检查内容:
{content}

"""
        if context:
            building_task += f"""相关上下文:
{context}

"""

        building_task += f"""请从以下角度对内容进行检查并提供应用策略：
1. 世界观构建策略
2. 人物关系构建策略
3. 情节递进构建策略
4. 冲突解决构建策略
5. 设定维护构建策略

提供具体的构建策略建议，以及如何强化逻辑架构的措施。

请按照JSON格式返回，包括策略建议、评分、和应用方案。"""

        result = await self.agent.run(task=building_task)
        content_result = extract_content(result.messages)
        parsed_json = extract_all_json(content_result)

        return {
            "building_strategies": parsed_json,
            "strategy_application": content_result,
            "raw_content": content,
            "agent": self.name
        }

    def get_building_library(self) -> Dict[str, Any]:
        """
        返回构建策略库的基本信息

        Returns:
            构建策略库信息
        """
        return {
            "name": "构建策略库",
            "version": "1.0",
            "strategies": [
                "世界观构建",
                "逻辑连贯性构建",
                "人物关系构建",
                "情节递进构建",
                "架构稳定性检验"
            ]
        }