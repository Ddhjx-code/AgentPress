"""
Dialogue Specialist Agent专门处理器
对应prompts/dialogue_specialist.md，优化对话质量
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class DialogueSpecialistHandler(BaseAgentHandler):
    """
    Dialogue Specialist Agent专门处理器
    对应prompts/dialogue_specialist.md，负责对话优化和角色辨识度
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        优化对话质量和角色辨识度

        Args:
            task: 任务内容（通常包含需要优化的对话）
            **kwargs: 额外参数

        Returns:
            优化后的对话及相关信息
        """
        if "optimize_dialogue" in kwargs:
            return await self.optimize_dialogue(task)
        else:
            return await self.analyze_dialogue(task)

    async def optimize_dialogue(self, dialogue_content: str) -> Dict[str, Any]:
        """
        优化对话内容

        Args:
            dialogue_content: 需要优化的对话内容

        Returns:
            优化后的对话及分析结果
        """
        optimization_task = f"""你是一位对话策略专家，请优化以下对话内容：

待优化对话:
{dialogue_content}

优化要点：
1. 提高对话的生动性和自然度
2. 强化不同角色的说话风格辨识度
3. 确保对话服务于情节推进
4. 增强对话的情感表达力
5. 检查对话的逻辑合理性

请提供优化后的对话，并说明你的优化策略。"""

        result = await self.agent.run(task=optimization_task)
        optimized_content = extract_content(result.messages)

        return {
            "original_dialogue": dialogue_content,
            "optimized_dialogue": optimized_content,
            "improvement_notes": "提高了生动性、角色辨识度和情感表达",
            "agent": self.name
        }

    async def analyze_dialogue(self, content: str) -> Dict[str, Any]:
        """
        分析对话质量

        Args:
            content: 包含对话的内容

        Returns:
            对话质量分析结果
        """
        analysis_task = f"""你是一位对话策略专家，请分析以下内容中对话的质量：

待分析内容:
{content}

分析要点：
1. 每个角色的说话风格是否独特
2. 对话是否具有生动性
3. 对话是否推进了情节
4. 角色辨识度是否清晰
5. 对话情感表达是否到位

请提供以下格式的分析：
- 角色风格辨识度评级
- 对话生动性评级
- 情节推进建议
- 优化方案
- 总体评估"""

        result = await self.agent.run(task=analysis_task)
        analysis_content = extract_content(result.messages)
        parsed_json = extract_all_json(analysis_content)

        return {
            "dialogue_analysis": parsed_json,
            "analysis_notes": analysis_content,
            "content_length": len(content),
            "agent": self.name
        }

    async def enhance_character_voice(self, dialogue_content: str, character_profile: str = None) -> Dict[str, Any]:
        """
        强化角色声音特征

        Args:
            dialogue_content: 对话内容
            character_profile: 角色描述/特征

        Returns:
            增强角色特性的对话
        """
        enhancement_task = f"""你是一位对话策略专家，请增强对话中角色的声音特征：

对话内容:
{dialogue_content}

"""
        if character_profile:
            enhancement_task += f"""角色档案:
{character_profile}

"""
        enhancement_task += f"""请基于角色的个人特征（背景、性格、教育程度、职业等）来强化他们在对话中的独特声音。
确保：
1. 每个角色有独特的用词习惯
2. 每个角色的语调和语气符合其个性
3. 说话风格符合角色设定
4. 在保持对话自然的同时体现角色个性

返回强化角色声音后的对话版本。"""

        result = await self.agent.run(task=enhancement_task)
        enhanced_content = extract_content(result.messages)

        return {
            "original_dialogue": dialogue_content,
            "enhanced_dialogue": enhanced_content,
            "character_profile_used": character_profile,
            "agent": self.name
        }