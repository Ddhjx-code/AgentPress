"""
研究规划阶段管理器
重构后的研究阶段，专门负责创意概念的分析和规划
"""
from typing import Dict, Any
from core.agent_handlers_map import AgentHandlersMap
from src.documentation_manager import DocumentationManager
from core.conversation_manager import ConversationManager
from src.agents.mythologist_agent import MythologistAgentHandler
from config import GROUPCHAT_CONFIGS, CREATION_CONFIG
from utils import extract_content
import re


class ResearchPhase:
    """
    重构后的研究规划阶段
    使用专业agent处理器执行研究任务
    """

    def __init__(self, agent_handlers_map: AgentHandlersMap, documentation_manager: DocumentationManager,
                 conversation_manager: ConversationManager):
        """
        初始化研究阶段管理器

        Args:
            agent_handlers_map: agent处理器映射服务
            documentation_manager: 文档管理器
            conversation_manager: 对话管理器
        """
        self.agent_handlers_map = agent_handlers_map
        self.doc_manager = documentation_manager
        self.conversation_manager = conversation_manager

    async def execute_research(self, novel_concept: str) -> Dict[str, Any]:
        """
        执行完整的创意研究和规划阶段

        Args:
            novel_concept: 小说创意概念

        Returns:
            包含研究和规划结果的字典
        """
        print("\\n" + "="*60)
        print("🔍 第一阶段：创意研究与规划")
        print("="*60)

        # 1. 执行跨文化符号策略分析 (Mythologist)
        print("\\n📖 开始跨文化符号策略分析...")
        mythologist_handler = self.agent_handlers_map.get_handler("mythologist")
        if mythologist_handler:
            mythologist_result = await mythologist_handler.process(novel_concept)
            symbol_analysis = mythologist_result.get("parsed_json", {})
        else:
            symbol_analysis = {}
            print("⚠️  Mythologist代理不可用")

        # 2. 使用Writer代理生成初步大纲
        writer_handler = self.agent_handlers_map.get_handler("writer")
        if writer_handler:
            print("📋 生成初步大纲...")
            outline_task = f"""基于以下创意概念提供初步的创作大纲：

创意概念: {novel_concept}

请考虑Mythologist的分析结果，制定包含以下内容的大纲：
1. 核心冲突和情节主线
2. 主要角色设定
3. 基本结构规划
4. 预期风格和基调"""

            outline_result = await writer_handler.process(outline_task)
            outline = outline_result.get("content", "")

            # 从分析结果中提取目标长度建议
            target_length = 5000  # 默认值
            if symbol_analysis and isinstance(symbol_analysis, dict):
                if "target_length" in symbol_analysis:
                    target_length = symbol_analysis["target_length"].get("suggested", 5000)
                elif symbol_analysis.get("suggested_length"):
                    target_length = symbol_analysis["suggested_length"]
        else:
            outline = f"基于 {novel_concept} 的粗略规划"
            print("⚠️  Writer代理不可用")

        # 3. 保存研究阶段结果到文档管理器
        research_summary = {
            "concept": novel_concept,
            "outline": outline,
            "symbol_analysis": symbol_analysis,
            "target_length": target_length,
            "research_timestamp": __import__('datetime').datetime.now().isoformat()
        }

        self.doc_manager.update_documentation(str(research_summary))

        # 4. 记录对话历史
        self.conversation_manager.add_research_summary("initial_research", research_summary)

        # 5. 计算中文汉字数量
        chinese_chars_count = len(re.findall(r'[\\u4e00-\\u9fff]', outline))
        print(f"\\n📊 研究阶段完成统计：概述内容 {len(outline)} 字符 | {chinese_chars_count} 中文汉字")

        # 6. 返回研究阶段成果
        research_data = {
            "concept": novel_concept,
            "outline": outline,
            "symbol_analysis": symbol_analysis,
            "target_length_suggestion": {
                "suggested": target_length,
                "confidence": (symbol_analysis.get("target_length", {}).get("confidence", 0.6)
                          if isinstance(symbol_analysis, dict) else 0.6)
            }
        }

        print("\\n✅ 研究和规划阶段完成")
        return research_data