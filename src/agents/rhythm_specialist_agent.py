"""
Rhythm Specialist Agent专门处理器
对应prompts/write_rate_specialist.md，优化叙事节奏
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class RhythmSpecialistHandler(BaseAgentHandler):
    """
    Rhythm Specialist Agent专门处理器
    对应prompts/write_rate_specialist.md，优化叙事节奏和情绪曲线
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        执行节奏和情绪曲线优化任务

        Args:
            task: 节奏优化任务
            **kwargs: 额外参数

        Returns:
            节奏优化结果
        """
        if "optimize_rhythm" in kwargs:
            return await self.optimize_rhythm(task)
        else:
            return await self.analyze_narrative_rhythm(task)

    async def optimize_rhythm(self, content: str) -> Dict[str, Any]:
        """
        优化叙事节奏

        Args:
            content: 需要优化节奏的内容

        Returns:
            包含优化节奏的反馈
        """
        rhythm_task = f"""你是一位情绪节拍师，请评估并优化以下章节的叙事节奏：

章节内容:
{content}

优化要点：
1. 调整叙事节奏的快慢变化
2. 优化情绪曲线的设计
3. 改善信息密度的安排
4. 提升读者注意力引导效果
5. 优化剧情张弛度的安排

请特别关注：
- 场景转换的节奏
- 对话与叙述的平衡
- 紧张与缓和的交替
- 情绪波动的曲线设计

返回优化后的版本，确保节奏变化符合故事发展需要，同时保持读者的阅读兴趣。"""

        result = await self.agent.run(task=rhythm_task)
        optimized_content = extract_content(result.messages)

        return {
            "original_content": content,
            "rhythm_optimized_content": optimized_content,
            "optimization_focus": "叙事节奏和情绪曲线优化",
            "agent": self.name
        }

    async def analyze_narrative_rhythm(self, content: str) -> Dict[str, Any]:
        """
        分析叙事节奏质量

        Args:
            content: 待分析的内容

        Returns:
            节奏分析结果
        """
        analysis_task = f"""你是一位情绪节拍师，请深入分析以下内容的叙事节奏结构：

内容长度: {len(content)} 字符
内容:
{content}

请提供全面的节奏与情绪分析，包括但不限于：
- 叙事节奏分析
- 情绪曲线上升/下降点
- 信息密度评估
- 读者专注力变化模式
- 节奏与内容匹配度
- 节奏优化建议
- 情绪节拍设计评价

请返回JSON格式的详细分析，包含节奏分析、情绪轨迹、优化建议和实现方案。"""

        result = await self.agent.run(task=analysis_task)
        analysis_content = extract_content(result.messages)
        parsed_json = extract_all_json(analysis_content)

        return {
            "rhythm_analysis": parsed_json,
            "rhythm_notes": analysis_content,
            "content_length": len(content),
            "agent": self.name
        }

    async def optimize_emotional_beat(self, content: str, target_emotion: str = None) -> Dict[str, Any]:
        """
        基于目标情绪优化情绪节拍

        Args:
            content: 原始内容
            target_emotion: 目标情绪

        Returns:
            优化情绪节拍的内容
        """
        beat_optimization_task = f"""你是一位情绪节拍师，请分析并优化以下内容的情绪节拍曲线：

内容:
{content}

"""
        if target_emotion:
            beat_optimization_task += f"""当前需达到的特别情绪目标: {target_emotion}

"""

        beat_optimization_task += f"""请优化内容的节奏以达到或维持目标情绪，特别注意：
1. 关键情节的情感引导
2. 句式长短与情绪的配合
3. 场景切换的情绪过渡
4. 通过节奏变化强化情感传递
5. 保持情感张力同时不过度疲劳读者

返回优化后的内容，确保情绪节拍与故事内容自然融合。"""

        result = await self.agent.run(task=beat_optimization_task)
        optimized_content = extract_content(result.messages)

        return {
            "original_content": content,
            "target_emotion": target_emotion,
            "emotion_optimized_content": optimized_content,
            "agent": self.name
        }