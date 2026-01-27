"""
Documentation Specialist Agent专门处理器
对应prompts/documentation_specialist.md，维护故事连贯性
"""
from typing import Dict, Any, List, Optional
from autogen_agentchat.agents import AssistantAgent
from .base_agent_handler import BaseAgentHandler
from src.documentation_manager import DocumentationManager
from utils import extract_all_json, extract_content


class DocumentationSpecialistHandler(BaseAgentHandler):
    """
    Documentation Specialist Agent专门处理器
    对应prompts/documentation_specialist.md，负责维护文档和连贯性
    """

    def __init__(self, agent: AssistantAgent, documentation_manager: Optional[DocumentationManager] = None):
        super().__init__(agent)
        self.doc_manager = documentation_manager

    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        处理文档和连贯性任务

        Args:
            task: 文档管理任务描述
            **kwargs: 额外参数

        Returns:
            包含文档更新信息的字典
        """
        # 判断是文档更新任务还是连贯性检查任务
        if "current_archive" in kwargs and "new_content" in kwargs:
            return await self.update_archive(kwargs["new_content"], kwargs.get("chapter_num", 1))
        else:
            return await self.check_continuity(task)

    async def update_archive(self, new_content: str, chapter_num: int = 1) -> Dict[str, Any]:
        """
        更新文档档案

        Args:
            new_content: 新添加的内容
            chapter_num: 章节号

        Returns:
            更新后的文档档案信息
        """
        update_task = f"""你是一位故事档案员，请从以下新章节内容中提取信息并更新档案：

章节号: {chapter_num}
新章节内容:
{new_content}

请严格按照JSON格式返回档案更新信息，包括：
- characters: 人物档案更新
- timeline: 时间线信息
- world_rules: 世界观规则更新
- plot_points: 情节要点
- foreshadowing: 伏笔管理
- chapter_summary: 章节摘要"""

        result = await self.agent.run(task=update_task)
        content = extract_content(result.messages)
        parsed_json = extract_all_json(content)

        # 保存到文档管理器
        if self.doc_manager:
            self.doc_manager.update_documentation(content)

        return {
            "archive_update": parsed_json,
            "raw_content": content,
            "chapter_num": chapter_num,
            "new_content_length": len(new_content),
            "agent": self.name
        }

    async def check_continuity(self, content_to_check: str, existing_archive: str = None) -> Dict[str, Any]:
        """
        检查内容的连贯性

        Args:
            content_to_check: 要检查的内容
            existing_archive: 现有档案数据

        Returns:
            连贯性检查结果
        """
        continuity_task = f"""你是一位连贯性检查员，请分析以下内容是否与已有档案一致：

"""
        if existing_archive:
            continuity_task += f"""当前档案摘要:
{existing_archive}

"""
        continuity_task += f"""待检查的新内容:
{content_to_check}

请进行以下检查：
1. 人物一致性（性格、能力、说话风格）
2. 时间线一致性（时间间隔、天数计算、季节变化）
3. 世界观一致性（已建立的规则、地理距离、社会等级）
4. 伏笔一致性（回收的一致性、遗漏的伏笔）
5. 人物成长一致性（变化是否有铺垫）

请返回JSON格式的检查结果，包括：
- is_consistent: 是否一致性
- overall_score: 整体分数
- issues: 发现的问题列表
- warnings: 警告信息
- positive_notes: 做得好的地方
- overall_feedback: 整体评价"""

        result = await self.agent.run(task=continuity_task)
        content = extract_content(result.messages)
        parsed_json = extract_all_json(content)

        return {
            "continuity_check": parsed_json,
            "raw_content": content,
            "content_length": len(content_to_check),
            "agent": self.name
        }

    async def generate_summary(self, content: str, chapter_num: int = 1) -> Dict[str, Any]:
        """
        为章节生成摘要

        Args:
            content: 章节内容
            chapter_num: 章节号

        Returns:
            章节摘要信息
        """
        summary_task = f"""请为以下章节生成摘要：

章节号: {chapter_num}
章节内容:
{content}

请生成简洁但全面的摘要（50-100字），包含：主要人物、关键事件和情节进展。"""

        result = await self.agent.run(task=summary_task)
        summary = extract_content(result.messages)

        return {
            "chapter_num": chapter_num,
            "summary": summary,
            "original_content_length": len(content),
            "agent": self.name
        }

    def get_archived_data(self) -> Optional[Dict]:
        """
        获取存档的数据信息

        Returns:
            存储的文档数据（如果有文档管理器的话）
        """
        if self.doc_manager and hasattr(self.doc_manager, 'get_documentation'):
            return self.doc_manager.get_documentation()
        return None