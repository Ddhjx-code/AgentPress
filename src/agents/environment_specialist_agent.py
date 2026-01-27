"""
Environment Specialist Agent专门处理器
对应prompts/write_enviroment_specialist.md，优化环境描写
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class EnvironmentSpecialistHandler(BaseAgentHandler):
    """
    Environment Specialist Agent专门处理器
    对应prompts/write_enviroment_specialist.md，优化环境描写和氛围营造
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        执行环境描写优化任务

        Args:
            task: 环境描写优化任务
            **kwargs: 额外参数

        Returns:
            环境优化结果
        """
        if "enhance_environment" in kwargs:
            return await self.enhance_environment_description(task)
        else:
            return await self.optimize_environment(task)

    async def enhance_environment_description(self, content: str) -> Dict[str, Any]:
        """
        增强环境描写

        Args:
            content: 包含环境描述的内容

        Returns:
            增强后的环境描写结果
        """
        enhancement_task = f"""你是一位感官呈现专家，请优化以下内容中的环境描写：

原始内容:
{content}

优化重点：
1. 增强环境描写的生动性
2. 补充感官细节（视觉、听觉、嗅觉、触觉、味觉）
3. 优化氛围营造（情绪、环境、情节氛围）
4. 让环境描写更好地服务于情节和情绪
5. 创建沉浸式的感官体验

请返回增强后的版本，确保环境描写与情节内容紧密结合，既不过于冗长也不过于简略。"""

        result = await self.agent.run(task=enhancement_task)
        enhanced_content = extract_content(result.messages)

        return {
            "original_content": content,
            "enhanced_environment": enhanced_content,
            "enhancement_focus": "感官细节和氛围营造优化",
            "agent": self.name
        }

    async def optimize_environment(self, scene_content: str) -> Dict[str, Any]:
        """
        优化场景中的环境细节

        Args:
            scene_content: 包含场景的内容

        Returns:
            包含环境优化建议的结果
        """
        optimization_task = f"""你是一位感官呈现专家，请分析并优化以下场景的环境描写：

场景内容:
{scene_content}

分析和优化要点：
- 评估当前环境描写的感官细节
- 识别可以增强的感官层面
- 提供具体优化建议
- 优化环境与情节的结合度
- 创建更生动的环境氛围

请返回以下内容：
1. 环境描写质量评估
2. 感官细节优化建议
3. 氛围营造改进建议
4. 优化后的环境描述
5. 与情节结合度的提升方案"""

        result = await self.agent.run(task=optimization_task)
        optimization_content = extract_content(result.messages)
        parsed_json = extract_all_json(optimization_content)

        return {
            "environment_analysis": parsed_json,
            "optimization_notes": optimization_content,
            "original_length": len(scene_content),
            "agent": self.name
        }

    async def create_sensory_implementation(self, content: str, mood_target: str = None) -> Dict[str, Any]:
        """
        创建针对特定情绪的感官实现

        Args:
            content: 原始内容
            mood_target: 目标情绪

        Returns:
            针对特定情绪优化的感官环境
        """
        mood_specific_task = f"""你是一位感官呈现专家，专门针对特定情绪创建环境描写。

原始内容:
{content}

"""
        if mood_target:
            mood_specific_task += f"""目标情绪/氛围: {mood_target}

"""

        mood_specific_task += f"""请特别关注感官细节的运用，以营造目标氛围：
- 视觉细节：颜色、光线、形状
- 听觉细节：声音层次、音质、节奏
- 嗅觉细节：气味特质、浓淡
- 触觉细节：温度、质地、空间感
- 味觉细节：相关味觉感受（如金属味、苦涩等）

返回增强感官体验的版本，确保环境描写与目标情绪/氛围高度契合。"""

        result = await self.agent.run(task=mood_specific_task)
        enhanced_content = extract_content(result.messages)

        return {
            "original_content": content,
            "mood_target": mood_target,
            "sensory_enhanced_content": enhanced_content,
            "agent": self.name
        }