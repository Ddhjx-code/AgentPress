"""
评审修订阶段管理器
重构后的评审阶段，使用专业agent处理器执行评审任务
"""
from typing import Dict, Any
from core.agent_handlers_map import AgentHandlersMap
from core.conversation_manager import ConversationManager
from src.agents.editor_agent import EditorAgentHandler
from src.agents.fact_checker_agent import FactCheckerHandler
from src.agents.dialogue_specialist_agent import DialogueSpecialistHandler
from config import SCORE_THRESHOLD, MAX_REVISION_ROUNDS
from utils import calculate_average_score, format_feedback_summary


class ReviewPhase:
    """
    重构后的评审阶段管理器
    协调多个专门化agent处理器进行质量评估和修订
    """

    def __init__(self, agent_handlers_map: AgentHandlersMap, conversation_manager: ConversationManager):
        """
        初始化评审阶段管理器

        Args:
            agent_handlers_map: agent处理器映射服务
            conversation_manager: 对话管理器
        """
        self.agent_handlers_map = agent_handlers_map
        self.conversation_manager = conversation_manager
        self.progress_callback = None  # 用于进度通知

    async def execute_review(self, story: str) -> str:
        """
        执行评审和修订阶段

        Args:
            story: 需要评审的故事故事

        Returns:
            评审后修订的故事故事
        """
        print("\\n" + "="*60)
        print("🧐 第三阶段：多维度质量评审与修订")
        print("="*60)

        print(f"📊 待评审内容长度: {len(story)} 字符")

        current_version = story
        revision_round = 0

        while revision_round < MAX_REVISION_ROUNDS:
            print(f"\\n--- 🔄 第 {revision_round + 1} 轮评审 ---")

            # 1. Editor整体质量评估
            editor_handler = self.agent_handlers_map.get_handler("editor")
            if editor_handler:
                print("🔍 Editor正在评估整体质量...")
                editor_result = await editor_handler.evaluate_content(current_version)

                # 从评估中提取评分
                overall_score = 0
                if editor_result.get("comprehensive_evaluation"):
                    eval_data = editor_result["comprehensive_evaluation"]
                    if isinstance(eval_data, dict) and "overall_score" in eval_data:
                        overall_score = eval_data["overall_score"]
                    else:
                        # 尝试从评估文本中提取评分
                        import re
                        score_match = re.search(r'(\d+)(?:分|分值|分数)', str(editor_result.get("evaluation_notes", "")))
                        if score_match:
                            overall_score = min(100, int(score_match.group(1)))
                        else:
                            overall_score = 75  # 默认分值
            else:
                overall_score = 70  # 默认分值
                print("⚠️  Editor代理不可用")

            print(f"📈 整体评分: {overall_score}/100")

            # 2. FactChecker逻辑一致性检查
            fact_checker_handler = self.agent_handlers_map.get_handler("fact_checker")
            if fact_checker_handler:
                print("🏗️  FactChecker正在验证逻辑一致性...")
                consistency_result = await fact_checker_handler.validate_logic(current_version)
            else:
                print("⚠️  FactChecker代理不可用")

            # 3. DialogueSpecialist对话优化
            dialogue_handler = self.agent_handlers_map.get_handler("dialogue_specialist")
            if dialogue_handler:
                print("💬 DialogueSpecialist正在优化对话质量...")
                dialogue_analysis = await dialogue_handler.analyze_dialogue(current_version)
            else:
                print("⚠️  DialogueSpecialist代理不可用")

            # 4. 检查是否达到阈值
            if overall_score >= SCORE_THRESHOLD:
                print(f"✅ 评审完成 - 达到质量阈值 ({SCORE_THRESHOLD}分)")
                break

            # 5. 执行修订，获取改进版本
            current_version = await self._perform_revision(
                current_version,
                editor_result,
                consistency_result if 'consistency_result' in locals() else None,
                dialogue_analysis if 'dialogue_analysis' in locals() else None
            )

            revision_round += 1

            # 通知进度回调
            if self.progress_callback:
                await self.progress_callback(
                    "评审阶段",
                    f"修订第{revision_round}轮",
                    f"已完成第{revision_round}轮修订，当前得分{overall_score}",
                    (revision_round/MAX_REVISION_ROUNDS)*0.5 + 0.5  # 最终阶段占据后50%
                )

        # 记录评审结果
        review_summary = {
            "initial_length": len(story),
            "final_length": len(current_version),
            "revision_rounds": revision_round,
            "final_score": overall_score
        }

        self.conversation_manager.add_review_summary(review_summary)

        print(f"\\n📈 评审阶段完成统计")
        print(f"   - 修订轮次: {revision_round}")
        print(f"   - 最终长度: {len(current_version)} 字符")
        print(f"   - 最终质量得分: {overall_score}/100")

        return current_version

    async def _perform_revision(self, story: str, editor_feedback: Dict,
                                consistency_feedback: Dict = None,
                                dialogue_feedback: Dict = None) -> str:
        """
        基于反馈执行修订

        Args:
            story: 原始故事
            editor_feedback: Editor的反馈
            consistency_feedback: FactChecker的反馈
            dialogue_feedback: DialogueSpecialist的反馈

        Returns:
            修订后的故事版本
        """
        revision_instruction = f"""基于以下反馈对故事进行修订：

原始故事:
{story}

"""
        if editor_feedback:
            revision_instruction += f"""Editor的整体质量评估:
{str(editor_feedback.get('evaluation_notes', ''))}
{str(editor_feedback.get('comprehensive_evaluation', ''))}

"""
        if consistency_feedback:
            revision_instruction += f"""FactChecker的逻辑一致性反馈:
{str(consistency_feedback.get('validation_result', ''))}
{str(consistency_feedback.get('raw_content', ''))}

"""
        if dialogue_feedback:
            revision_instruction += f"""DialogueSpecialist的对话优化反馈:
{str(dialogue_feedback.get('dialogue_analysis', ''))}
{str(dialogue_feedback.get('analysis_notes', ''))}

"""

        revision_instruction += """请基于以上反馈对故事进行修订，重点关注：
1. 提升整体质量
2. 解决逻辑不一致问题
3. 优化对话质量
4. 保持故事的吸引力和可读性

返回修订后的完整故事版本。"""

        # 使用Writer代理执行修订
        writer_handler = self.agent_handlers_map.get_handler("writer")
        if writer_handler:
            print("✍️  Writer正在执行修订...")
            revision_result = await writer_handler.process(revision_instruction)
            return revision_result.get("content", story)
        else:
            print("⚠️  Writer代理不可用，返回原始版本")
            return story