"""
Editor Agent专门处理器
对应prompts/editor.md，提供整体质量评价
"""
from typing import Dict, Any
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from utils import extract_all_json, extract_content


class EditorAgentHandler(BaseAgentHandler):
    """
    Editor Agent专门处理器
    对应prompts/editor.md，提供全面的质量评估和发布建议
    """

    def __init__(self, agent: AssistantAgent):
        super().__init__(agent)

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        执行整体质量评估

        Args:
            task: 待评估的内容
            **kwargs: 额外参数

        Returns:
            质量评估结果
        """
        if "evaluate_content" in kwargs:
            return await self.evaluate_content(task)
        else:
            return await self.quality_assessment(task)

    async def evaluate_content(self, content: str) -> Dict[str, Any]:
        """
        评估内容的全面质量

        Args:
            content: 要评估的内容

        Returns:
            综合质量评估结果
        """
        evaluation_task = f"""你是一位经验丰富的编辑，专门提供综合质量评价和发布建议。

请全面评估以下内容：
{content}

评估维度：
1. 文学质量（叙事技艺、语言技巧、结构安排）
2. 娱乐性（吸引度、可读性、趣味性）
3. 逻辑连贯性（情节连贯、人物行为一致）
4. 情感触动（情感表达、共鸣度）
5. 创新度（创意元素、新颖性）

同时请提供：
- 总体评分（1-100分）
- 优势分析
- 改进建议
- 发布建议
- 目标读者群体
- 修订优先级"""

        result = await self.agent.run(task=evaluation_task)
        evaluation_content = extract_content(result.messages)
        parsed_json = extract_all_json(evaluation_content)

        return {
            "comprehensive_evaluation": parsed_json,
            "evaluation_notes": evaluation_content,
            "content_length": len(content),
            "agent": self.name
        }

    async def quality_assessment(self, content: str) -> Dict[str, Any]:
        """
        执行质量评估

        Args:
            content: 要评估的内容

        Returns:
            详细的质量评估报告
        """
        assessment_task = f"""你是一位专业的审阅师，提供高质量的综合质量评价。

内容长度: {len(content)} 字符

待评估内容:
{content}

请按以下结构提供评估：
1. 整体印象 - 1-2句话概括
2. 内容质量 - 故事性、创新性、逻辑性
3. 技术质量 - 语言、结构、表达
4. 潜在问题 - 需要注意的问题点
5. 优化建议 - 具体的改进方向
6. 发布前景 - 评估发布价值和建议

请以JSON格式返回评估结果。"""

        result = await self.agent.run(task=assessment_task)
        assessment_content = extract_content(result.messages)
        parsed_json = extract_all_json(assessment_content)

        return {
            "quality_assessment": parsed_json,
            "detailed_notes": assessment_content,
            "original_content_length": len(content),
            "agent": self.name
        }

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        返回质量评估的标准

        Returns:
            包含评估标准的信息
        """
        return {
            "standard": "综合编辑评估标准",
            "criteria": [
                {
                    "category": "文学技法",
                    "metrics": ["叙事技艺", "语言表达", "结构安排"]
                },
                {
                    "category": "内容价值",
                    "metrics": ["原创性", "思想深度", "情感共鸣"]
                },
                {
                    "category": "商业潜力",
                    "metrics": ["读者吸引力", "市场需求", "类型适配"]
                }
            ],
            "scoring_system": "百分制评分体系",
            "agent": self.name
        }