"""
最终检查阶段管理器
重构后的最终检查阶段，使用专业agent处理器执行综合检查
"""
from typing import Dict, Any
from core.agent_handlers_map import AgentHandlersMap
from core.conversation_manager import ConversationManager
from src.agents.fact_checker_agent import FactCheckerHandler
from src.agents.editor_agent import EditorAgentHandler
from src.agents.documentation_specialist_agent import DocumentationSpecialistHandler
from utils import extract_content


class FinalCheckPhase:
    """
    重构后的最终检查阶段管理器
    执行最终的质量和一致性检查
    """

    def __init__(self, agent_handlers_map: AgentHandlersMap, conversation_manager: ConversationManager):
        """
        初始化最终检查阶段管理器

        Args:
            agent_handlers_map: agent处理器映射服务
            conversation_manager: 对话管理器
        """
        self.agent_handlers_map = agent_handlers_map
        self.conversation_manager = conversation_manager

    async def execute_final_check(self, story: str) -> str:
        """
        执行最终综合性检查

        Args:
            story: 需要最终检查的故事故事

        Returns:
            通过最终检查的故事故事
        """
        print("\\n" + "="*60)
        print("✅ 第四阶段：最终质量检查")
        print("="*60)

        print(f"📊 待检查内容长度: {len(story)} 字符")

        # 1. 执行全面的事实检查和逻辑一致性验证
        fact_checker_handler = self.agent_handlers_map.get_handler("fact_checker")
        if fact_checker_handler:
            print("\\n🏗️  Fact-Checker正在进行全面一致性检查...")
            fact_check_result = await fact_checker_handler.validate_logic(story)

            fact_check_notes = fact_check_result.get("raw_content", "")
            print(f"   - 验证结果: {len(fact_check_notes)} 字符反馈")
        else:
            print("⚠️  FactChecker代理不可用")

        # 2. 执行最终质量审核
        editor_handler = self.agent_handlers_map.get_handler("editor")
        if editor_handler:
            print("🧐 Editor正在进行最终质量审核...")
            final_evaluation = await editor_handler.evaluate_content(story)

            evaluation_score = 0
            if final_evaluation.get("comprehensive_evaluation"):
                eval_data = final_evaluation["comprehensive_evaluation"]
                if isinstance(eval_data, dict) and "overall_score" in eval_data:
                    evaluation_score = eval_data["overall_score"]
            print(f"   - 整体质量得分: {evaluation_score}/100")
        else:
            print("⚠️  Editor代理不可用")

        # 3. 执行完整的连贯性检查
        doc_specialist_handler = self.agent_handlers_map.get_handler("documentation_specialist")
        if doc_specialist_handler:
            print("📚 Documentation-Specialist正在进行连贯性验证...")

            # 假设我们有存档的数据
            existing_archive = doc_specialist_handler.get_archived_data()
            continuity_result = await doc_specialist_handler.check_continuity(story, existing_archive)

            continuity_check = continuity_result.get("continuity_check", {})
            issue_count = len(continuity_check.get("issues", [])) if isinstance(continuity_check, dict) else 0
            print(f"   - 连贯性检查完成，发现 {issue_count} 个潜在问题")
        else:
            print("⚠️  DocumentationSpecialist代理不可用")

        # 4. 检查整体结构完整性
        print("\\n📋 执行结构完整性检查...")

        # 检查是否包含必要组成部分
        structure_check = self._check_narrative_structure(story)

        print(f"   - 结构完整性: {'✅' if structure_check['complete'] else '⚠️'}")
        print(f"   - 情节完整性: {structure_check['arc_status']}")
        print(f"   - 首尾呼应: {structure_check['bookend_status']}")

        # 5. 合并所有检查结果，必要时进行最终优化
        final_story = await self._apply_final_optimizations(story, fact_check_result, final_evaluation)

        # 6. 记录最终检查报告
        final_check_report = {
            "original_length": len(story),
            "final_length": len(final_story),
            "fact_check_performed": fact_checker_handler is not None,
            "quality_eval_performed": editor_handler is not None,
            "continuity_check_performed": doc_specialist_handler is not None,
            "structural_integrity": structure_check,
            "completion_timestamp": __import__('datetime').datetime.now().isoformat()
        }

        self.conversation_manager.add_final_check_report(final_check_report)

        print(f"\\n🎯 最终检查完成")
        print(f"   - 初始长度: {len(story)} 字符")
        print(f"   - 最终长度: {len(final_story)} 字符")
        print(f"   - 检查项: {len([x for x in [fact_checker_handler, editor_handler, doc_specialist_handler] if x])}/3 个代理参与")

        return final_story

    def _check_narrative_structure(self, story: str) -> Dict[str, Any]:
        """
        检查基本的故事结构

        Args:
            story: 待检查的故事

        Returns:
            结构检查结果
        """
        # 简单的结构检查 - 检查是否包含基本的故事元素
        lower_story = story.lower()

        # 关键结构词检查
        has_opening = any(word in lower_story for word in ["开始", "开头", "第一章", "从前", "很久以前", "突然"])
        has_conflict = any(word in lower_story for word in ["但是", "然而", "问题", "挑战", "困难", "冲突", "危险"])
        has_resolution = any(word in lower_story for word in ["解决", "克服", "最后", "结尾", "终于", "结局", "结果"])

        complete = has_opening and has_conflict and has_resolution

        arc_status = "完整" if complete else ("部分完整" if has_opening and has_conflict else "不完整")
        bookend_status = "是" if story.startswith(tuple(story.split()[:5])) and story.endswith(tuple(story.split()[-5:])) else "否"

        return {
            "complete": complete,
            "arc_status": arc_status,
            "bookend_status": bookend_status,
            "has_opening": has_opening,
            "has_conflict": has_conflict,
            "has_resolution": has_resolution
        }

    async def _apply_final_optimizations(self, story: str, fact_check_result: Dict, evaluation_result: Dict) -> str:
        """
        根据检查结果应用最终优化

        Args:
            story: 原始故事
            fact_check_result: 事实检查结果
            evaluation_result: 质量评价结果

        Returns:
            优化后的故事
        """
        optimization_task = f"""请基于以下检查结果对故事进行最终优化：

待优化故事:
{story}

事实检查结果:
{str(fact_check_result.get('raw_content', '')) if fact_check_result else ''}

质量评价结果:
{str(evaluation_result.get('evaluation_notes', '')) if evaluation_result else ''}

请解决检查中发现的问题，进行最终优化，返回一个高质量、逻辑一致、结构完整的版本。"""

        # 使用Writer代理执行最终优化
        writer_handler = self.agent_handlers_map.get_handler("writer")
        if writer_handler:
            print("✍️  Writer正在执行最终优化...")
            final_optimization_result = await writer_handler.process(optimization_task)
            final_content = final_optimization_result.get("content", story)

            # 记录优化说明
            optimization_summary = {
                "optimization_task": "基于多重检查结果进行最终优化",
                "original_length": len(story),
                "optimized_length": len(final_content),
                "optimization_notes": "修复一致性问题，提高整体质量"
            }
            self.conversation_manager.add_optimization_note(optimization_summary)

            return final_content

        else:
            print("⚠️  Writer代理不可用，返回原始版本")
            return story