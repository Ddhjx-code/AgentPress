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

    async def execute_research(self, novel_concept: str, previous_context: str = "", previous_documentation: Dict = None) -> Dict[str, Any]:
        """
        执行完整的创意研究和规划阶段

        Args:
            novel_concept: 小说创意概念
            previous_context: 之前的续写上下文（用于长篇小说续写）
            previous_documentation: 之前的文档数据（用于保持一致性）

        Returns:
            包含研究和规划结果的字典
        """
        print("\\n" + "="*60)
        print("🔍 第一阶段：创意研究与规划")
        print("="*60)

        # 如果有之前的上下文，通知用户
        if previous_context:
            print(f"📚 检测到续写模式，已加载之前章节内容作为上下文参考")
            if previous_documentation:
                print(f"📝 已加载之前的故事文档，将用于保持一致性")

        # 处理上下文：如果续写，合并概念与上下文和其他文档信息
        full_context = novel_concept

        if previous_context:
            # 从previous_documentation提取结构化信息
            documentation_summary = ""
            if previous_documentation and isinstance(previous_documentation, dict):
                documentation_summary += "## 文档摘要供参考：\n"

                # 添加角色信息
                if "characters" in previous_documentation and previous_documentation["characters"]:
                    characters = list(previous_documentation["characters"].keys())
                    if characters:
                        documentation_summary += f"角色列表：{', '.join(characters[:10])}{'...' if len(characters) > 10 else ''}\n"

                # 添加世界设定
                if "world_rules" in previous_documentation and previous_documentation["world_rules"]:
                    rules = list(previous_documentation["world_rules"].keys())
                    documentation_summary += f"世界规则：{', '.join(rules[:10])}{'...' if len(rules) > 10 else ''}\n"

                # 添加重要地点
                if "settings_locations" in previous_documentation and previous_documentation["settings_locations"]:
                    locations = list(previous_documentation["settings_locations"].keys())
                    documentation_summary += f"重要地点：{', '.join(locations[:10])}{'...' if len(locations) > 10 else ''}\n"

                documentation_summary += "\n"

            full_context = f"## 续写模式 - 已有上下文:\n{previous_context}\n\n{documentation_summary}## 新的续写要求:\n{novel_concept}\n\n请基于已有内容和设定继续创作，并保持风格、人物和设定的一致性。重要的是要注意角色发展和情节连贯性。"

        # 1. 执行跨文化符号策略分析 (Mythologist)
        print("\\n📖 开始跨文化符号策略分析...")
        mythologist_handler = self.agent_handlers_map.get_handler("mythologist")
        if mythologist_handler:
            mythologist_result = await mythologist_handler.process(full_context)
            symbol_analysis = mythologist_result.get("parsed_json", {})
        else:
            symbol_analysis = {}
            print("⚠️  Mythologist代理不可用")

        # 2. 使用Writer代理生成初步大纲 - 同时考虑字数要求和上下文
        writer_handler = self.agent_handlers_map.get_handler("writer")
        if writer_handler:
            print("📋 生成初步大纲...")

            # 尝试从概念中提取用户指定的字数要求
            import re
            # 查找类似"13000字", "5000字以上", "#字数：15000字以上"等模式
            word_count_patterns = [
                r"(?i:要求?[:：]?\s*(\d+)[字萬萬])",  # 匹配"要求XXX字"
                r"(?i:要求?\s*(\d+)[,，]?\s*[字萬萬]\s*以上)",  # 匹配"XXX字以上"
                r"(?i:[#\n]字数?[：:]?\s*(\d+)[,，]?\s*[字萬萬])",  # 匹配"#字数XXX字"或"字数：XXX字"
                r"(?i:[#]类型[:：]?\s*[^\\n]*\n.*?(\d+)[,，]?\s*[字萬萬])",  # 匹配"类型：...XXX字"
            ]

            specified_target = None
            for pattern in word_count_patterns:
                match = re.search(pattern, novel_concept)
                if match:
                    raw_number = match.group(1)
                    # 处理"萬"字符
                    if '萬' in raw_number or '万' in raw_number:
                        number = raw_number.replace('萬', '').replace('万', '')
                        specified_target = int(number) * 10000
                    else:
                        specified_target = int(raw_number)
                    break

            if specified_target:
                print(f"📊 检测到概念中的目标字数要求: {specified_target} 字")
            else:
                # 额外检查 "字以上" 或其他模式
                more_pattern = r'(\d+)[,，]?\s*字\s*以上'
                more_match = re.search(more_pattern, novel_concept)
                if more_match:
                    specified_target = int(more_match.group(1))
                    print(f"📊 检测到概念中的最低字数要求: {specified_target} 字（以上）")

            # 创建针对续写的任务描述
            if previous_context:
                outline_task = f"""您正在续写一部小说。以下是有用的参考信息：

## 之前的创作内容（请保持一致性）：
{previous_context}

## 新的续写要求：
{novel_concept}

请基于已有内容继续创作，并保持以下方面的一致性：
1. 人物性格和关系
2. 世界观和规则
3. 写作风格和语调
4. 情节连贯性

同时请完成以下任务：
1. 核心冲突和情节主线（延续之前的故事线）
2. 主要角色设定（使用已有角色）
3. 本部分章节结构规划
4. 预期风格和基调的延续
5. 与前面内容的衔接点"""
            else:
                outline_task = f"""基于以下创意概念提供初步的创作大纲：

创意概念: {novel_concept}

请特别关注创意概念中指定的篇幅要求，并制定相应的创作规划。
如果概念中指定了目标字数，请严格遵循该要求。

创作大纲要求包含：
1. 核心冲突和情节主线
2. 主要角色设定
3. 基本结构规划（包含预计的章节划分以满足篇幅要求）
4. 预期风格和基调
5. 篇幅规划策略"""

            outline_result = await writer_handler.process(outline_task)
            outline = outline_result.get("content", "")

            # 确定目标长度，优先级：用户概念 > AI分析 > 配置 > 默认值
            target_length = 5000  # 默认值

            # 优先使用从用户概念中解析的目标字数
            if specified_target:
                target_length = specified_target
            elif symbol_analysis and isinstance(symbol_analysis, dict):
                if "target_length" in symbol_analysis:
                    # 只有当AI建议的长度不同于用户指定时才更新
                    if not specified_target:  # 如果用户没有指定，则使用AI分析的
                        target_length = symbol_analysis["target_length"].get("suggested", 5000)
                elif not specified_target:  # 如果用户没有指定，则使用AI分析的
                    if symbol_analysis.get("suggested_length"):
                        target_length = symbol_analysis["suggested_length"]

            print(f"🎯 确定最终创作字目标: {'概念指定' if specified_target else 'AI分析' if symbol_analysis else '默认配置'} -> {target_length} 字符")
        else:
            outline = f"基于 {novel_concept} 的粗略规划"
            print("⚠️  Writer代理不可用")

        # 3. 保存研究阶段结果到文档管理器 - 使用符合DocumentationManager结构的数据
        research_doc_data = {
            "characters": {},  # 研究阶段可能还没有特定的角色
            "timeline": [{"event": "concept_analysis", "description": novel_concept, "timestamp": __import__('datetime').datetime.now().isoformat()}],
            "world_rules": {},  # 在后面阶段提取
            "plot_points": [outline] if outline else [],  # 故事大纲作为一个情节点
            "settings_locations": {},  # 研究阶段可能还没有特定设置
            "updated_at": __import__('datetime').datetime.now().isoformat()
        }

        import json
        self.doc_manager.update_documentation(json.dumps(research_doc_data, ensure_ascii=False))

        # 4. 记录AI代理讨论会议纪要
        participants = []
        if self.agent_handlers_map.get_handler("mythologist"):
            participants.append("mythologist")
        if self.agent_handlers_map.get_handler("writer"):
            participants.append("writer")

        meeting_summary = f"完成创意概念研究，生成创作大纲，目标长度建议{target_length}字符"
        decisions = [
            f"研究概念: {novel_concept[:50]}{'...' if len(novel_concept) > 50 else ''}",
            f"生成大纲长度: {len(outline)} 字符",
            f"建议目标长度: {target_length} 字符"
        ]
        self.conversation_manager.add_meeting_minutes(
            stage="research_phase",
            participants=participants,
            summary=meeting_summary,
            decisions=decisions,
            turn_count=2  # mythologist和writer的交互轮次
        )

        # 5. 记录对话历史
        research_summary = {
            "concept": novel_concept,
            "outline": outline,
            "symbol_analysis": symbol_analysis,
            "target_length": target_length,
            "research_timestamp": __import__('datetime').datetime.now().isoformat()
        }
        self.conversation_manager.add_research_summary("initial_research", research_summary)

        # 5. 计算中文汉字数量（包含扩展中文字符）
        import re
        # 匹配更广范围的中文字符，包括基本汉字、扩展A、B、C、D区以及中文标点符号
        chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]'
        chinese_chars_count = len(re.findall(chinese_pattern, outline))
        print(f"\\n📊 研究阶段完成统计：概述内容 {len(outline)} 字符 | {chinese_chars_count} 中文字符")

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