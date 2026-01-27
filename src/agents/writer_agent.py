"""
Writer Agent专门处理器
对应prompts/writer.md，执行核心内容创作
"""
from typing import Dict, Any, List, Optional
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_content


class WriterAgentHandler(BaseAgentHandler):
    """
    Writer Agent专门处理器
    对应prompts/writer.md，负责核心故事内容创作
    应用三幕剧、角色驱动、节奏调控等写作策略
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, target_length: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        执行内容创作任务

        Args:
            task: 创作任务描述
            target_length: 目标长度
            **kwargs: 额外参数

        Returns:
            包含创作内容和元数据的字典
        """
        # 构建完整的创作任务描述
        writing_context = task
        if target_length:
            writing_context += f"\n\n请创作约 {target_length} 字符的内容。"

        # 执行创作任务
        result = await self.agent.run(task=writing_context)
        content = extract_content(result.messages)

        # 返回包含元数据的结果
        return {
            "content": content,
            "word_count": len(content),
            "target_length": target_length,
            "agent": self.name
        }

    async def apply_writing_strategies(self, base_content: str, strategy_combinations: List[str]) -> Dict[str, Any]:
        """
        应用写作策略对内容进行优化

        Args:
            base_content: 基础内容
            strategy_combinations: 要应用的策略组合列表

        Returns:
            优化后的内容和相关信息
        """
        optimization_task = f"""请在以下内容中应用指定的写作策略：

基础内容:
{base_content}

应用策略:
{', '.join(strategy_combinations)}

请基于以上策略对内容进行优化，确保内容质量得到提升。

只返回优化后的内容，不返回其他信息。"""

        result = await self.agent.run(task=optimization_task)
        optimized_content = extract_content(result.messages)

        return {
            "original_content": base_content,
            "optimized_content": optimized_content,
            "applied_strategies": strategy_combinations,
            "improvement_ratio": len(optimized_content) / max(1, len(base_content))
        }

    async def generate_with_structure(self, concept: str, structure: str = "三幕剧") -> Dict[str, Any]:
        """
        按照特定结构生成内容

        Args:
            concept: 创作概念
            structure: 要使用的结构类型

        Returns:
            包含分段内容和完整内容的字典
        """
        structure_map = {
            "三幕剧": "三幕剧结构：建置 → 对抗 → 解决",
            "英雄之旅": "英雄之旅：启程 → 启蒙 → 归返",
            "多线并行": "多线并行结构：A/B故事交织",
            "倒叙钩子": "倒叙钩子结构：开篇呈现高潮片段，再回溯原因"
        }

        structure_desc = structure_map.get(structure, structure)

        task = f"""请根据以下概念按照{structure_desc}创作内容：

创作概念: {concept}

请明确指出你选择的结构，并在内容中体现该结构的特征。"""

        result = await self.agent.run(task=task)
        content = extract_content(result.messages)

        return {
            "content": content,
            "structure_used": structure_desc,
            "concept": concept,
            "word_count": len(content),
            "agent": self.name
        }