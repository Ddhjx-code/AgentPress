"""
创作阶段管理器
AI驱动的动态章节创作，使用专业agent处理器执行
"""
import asyncio
import re
from typing import Dict, Any, List
from datetime import datetime
from core.agent_handlers_map import AgentHandlersMap
from src.documentation_manager import DocumentationManager
from core.conversation_manager import ConversationManager
from core.chapter_decision_engine import ChapterDecisionEngine
from core.continuity_manager import ContinuityManager
from core.story_state_manager import StoryStateManager
from config import CREATION_CONFIG
from utils import extract_content


class CreationPhase:
    """
    重构后的创作阶段管理器
    使用专业的agent处理器执行动态章节创作
    """

    def __init__(self, agent_handlers_map: AgentHandlersMap, documentation_manager: DocumentationManager,
                 conversation_manager: ConversationManager):
        """
        初始化创作阶段管理器

        Args:
            agent_handlers_map: agent处理器映射服务
            documentation_manager: 文档管理器
            conversation_manager: 对话管理器
        """
        self.agent_handlers_map = agent_handlers_map
        self.documentation_manager = documentation_manager
        self.conversation_manager = conversation_manager
        self.chapter_decision_engine = None  # 将在执行时初始化
        self.continuity_manager = None      # 将在执行时初始化
        self.story_state_manager = None     # 将在执行时初始化
        self.progress_callback = None       # 用于进度通知

    async def execute_creation(self, research_data: Dict[str, Any]) -> str:
        """
        执行AI驱动的动态章节创作

        Args:
            research_data: 研究阶段生成的数据

        Returns:
            创作完成的故事内容
        """
        print("\\n" + "="*60)
        print("✍️  第二阶段：AI驱动的动态章节创作")
        print("="*60)

        # 初始化管理器
        self.chapter_decision_engine = ChapterDecisionEngine(self.agent_handlers_map)
        self.continuity_manager = ContinuityManager(self.agent_handlers_map)
        self.story_state_manager = StoryStateManager()

        # 保存research_data以备后续检查使用（主要是字数建议）
        self.research_data = research_data

        # 使用动态章节决策替代固定的章节数量
        return await self.execute_dynamic_chapters_creation(research_data)

    async def execute_dynamic_chapters_creation(self, research_data: Dict[str, Any]) -> str:
        """
        执行AI驱动的动态章节创作

        Args:
            research_data: 研究阶段的数据

        Returns:
            完整的故事内容
        """
        # 初始化章节评估记录
        chapter_evaluations = {}

        # 初始化必要的处理器
        writer_handler = self.agent_handlers_map.get_handler("writer")
        if not writer_handler:
            print("❌ 未找到writer处理器")
            return "❌ 未找到writer处理器"

        chapters = []
        target_per_chapter = CREATION_CONFIG.get("target_length_per_chapter", 2000)

        # 生成动态章节规划
        chapter_plan = await self.chapter_decision_engine.create_chapter_outline(
            research_data.get("outline", "创意构思")
        )

        print(f"📖 基于AI分析的动态章节规划，预期创作章节: {len(chapter_plan) if chapter_plan else '动态确定'}")
        current_content = ""
        chapter_count = 0

        # 在状态管理器中创建故事
        story_id = f"story_{datetime.now().timestamp()}"
        self.story_state_manager.create_story(
            story_id=story_id,
            title=research_data.get('outline', 'AI生成的故事'),
            initial_metadata={'research_data': research_data}
        )

        # 检查research_data中的字数建议
        target_length = CREATION_CONFIG.get("total_target_length", 5000)

        # 获取AI建议的目标字数
        ai_suggested_length = None
        if "target_length_suggestion" in research_data and research_data["target_length_suggestion"]:
            suggested_info = research_data["target_length_suggestion"]
            if isinstance(suggested_info, dict) and "suggested" in suggested_info:
                ai_suggested_length = int(suggested_info["suggested"])

        # 计算最终目标字数
        if ai_suggested_length:
            target_chinese_chars = ai_suggested_length
            target_total_chars = int(ai_suggested_length * 1.5)  # 预留空间给标点和非汉字字符
            print(f"🎯 使用AI从概念中识别的目标: {target_chinese_chars} 汉字")
        else:
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", 5000)
            target_total_chars = CREATION_CONFIG.get("total_target_length", 6000)
            print(f"🔍 预计目标: 生成约 {target_chinese_chars} 汉字的故事内容 (使用配置值)")

        # 最终使用AI建议的汉字数作为主要目标
        if ai_suggested_length:
            target_length = target_total_chars
            target_chinese_chars = ai_suggested_length
        else:
            target_length = target_total_chars

        print(f"📏 故事进度追踪 [ 0% ] (目标: {target_chinese_chars} 汉字)")

        # 初始化章节评估记录
        chapter_evaluations = {}

        while True:  # 继续直到AI决定停止
            chapter_count += 1
            print(f"\\n--- 📘 章节 {chapter_count} 开始创作 ---")
            print(f"📊 进度: 已生成 {len(current_content)} / 预计 {target_length} 字符")

            current_progress = min(100, int(len(current_content) / target_length * 100))
            print(f"📈 进度条: {'█' * (current_progress // 2)}{'░' * (50 - current_progress // 2)} {current_progress}%")

            # 通知进度回调
            if self.progress_callback:
                await self.progress_callback(
                    "章节创作",
                    f"章节 {chapter_count}",
                    f"正在创作第 {chapter_count} 章节，已经生成 {len(current_content)} 字符，进度 {current_progress}%",
                    current_progress / 100.0
                )

            # 准备下一章的上下文
            context = f"""请基于以下信息创作第{chapter_count}章内容：

研究数据: {str(research_data)}
当前已生成内容: {current_content[-1000:] if current_content else '无'}

创作要求：
- 保持与研究阶段规划的一致性
- 符合整体故事发展方向
- 当前章节长度建议: {target_per_chapter} 字符
- 与前文保持连贯性
"""

            # 生成此章节的内容
            print(f"🤖 AI正在创作第 {chapter_count} 部分内容...", end="", flush=True)
            chapter_result = await writer_handler.process(context)
            new_content = chapter_result.get("content", "")
            print(" 完成!")

            # 与现有内容合并
            if current_content:
                current_content += "\\n\\n" + new_content
            else:
                current_content = new_content

            chapters.append(new_content)

            print(f"   ✅ 新增内容 {len(new_content)} 字符 | 累计: {len(current_content)} 字符")

            # 创建章节信息字典
            chapter_info = {
                "chapter_num": chapter_count,
                "content": new_content,
                "word_count": len(new_content),
                "summary": new_content[:200] + "..." if len(new_content) > 200 else new_content,
                "title": f"第{chapter_count}章",  # 将通过决策引擎更新
                "story_id": story_id
            }

            # 使用章节决策引擎来确定是否继续
            print(f"🧠 AI正在分析章节决策...", end="", flush=True)
            chapter_decision = await self.chapter_decision_engine.should_end_chapter(
                current_content,
                research_data
            )
            print(" 完成!")

            # 使用Editor进行单章节评审（利用其精细的章节评估能力）
            editor_handler = self.agent_handlers_map.get_handler("editor")
            if editor_handler:
                print(f"🔍 Editor正在进行单章节评估...", end="", flush=True)
                try:
                    # 使用Editor的单章评审功能
                    chapter_evaluation = await editor_handler.evaluate_content(new_content)

                    # 保存章节评审结果
                    if "chapter_evaluations" not in locals():
                        chapter_evaluations = {}
                    chapter_evaluations[chapter_count] = chapter_evaluation.get("comprehensive_evaluation", {})

                    # 检查是否有需要立即处理的技巧缺口
                    evaluation_data = chapter_evaluation.get("comprehensive_evaluation", {})
                    if isinstance(evaluation_data, dict) and "reader_experience" in evaluation_data:
                        reader_exp = evaluation_data["reader_experience"]
                        engagement_level = reader_exp.get("engagement_level", "medium")
                        drop_off_risk = reader_exp.get("drop_off_risk", "medium")

                        if drop_off_risk.lower() == "high" or engagement_level.lower() == "low":
                            print(f" ⚠️ 检测到第{chapter_count}章可能影响阅读体验")
                            # 这里可以考虑实现基于Editor评审的章节优化
                            if "actionable_suggestions" in evaluation_data:
                                print(f"   📝 Editor建议: {len(evaluation_data['actionable_suggestions'])} 项优化")
                    print(" 完成!")
                except Exception as e:
                    print(f" 跳过 (错误: {str(e)})")
                    pass
            else:
                print(f"📝 Editor代理不可用，跳过单章节评审")

            # 从决策中更新章节标题
            suggested_title = chapter_decision.get("suggested_title", f"第{chapter_count}章")
            chapter_info["title"] = suggested_title

            print(f"   🤖 章节分析: {chapter_decision['reasoning']} (置信度: {chapter_decision['confidence']:.2f})")

            # 在故事状态管理器中创建章节
            if self.story_state_manager:
                print(f"📝 正在记录章节状态...", end="", flush=True)
                chapter_state = self.story_state_manager.create_chapter(
                    story_id=story_id,
                    title=suggested_title,
                    content=new_content
                )
                print(f" 完成! ({chapter_state.chapter_id})")

            # 更新连续性管理器
            if self.continuity_manager:
                await self.continuity_manager.update_for_chapter(new_content, chapter_info)

            # 执行连贯性检查
            if self.continuity_manager:
                print(f"🔍 执行连续性检查...", end="", flush=True)
                continuity_report = await self.continuity_manager.check_continuity(
                    new_content, chapter_count
                )
                print(" 完成!")
                print(f"   📋 连续性检查: {continuity_report['summary']}")

                # 如果有高严重性不一致性，请考虑修订
                high_severity_issues = [issue for issue in continuity_report.get('inconsistencies', [])
                                      if issue.get('severity') == 'high']
                if high_severity_issues:
                    print(f"   ⚠️  检测到 {len(high_severity_issues)} 个高严重性连续性问题")
                    for issue in high_severity_issues:
                        print(f"      - {issue['element']}: {issue['issue']}")

            # 创建聊天记录
            self.conversation_manager.add_story_version(
                chapter_count,
                current_content,
                {"chapter_num": chapter_count, "decision": chapter_decision, "continuity": continuity_report}
            )

            # 应用一致性及复杂性管理（如果代理可用）
            doc_handler = self.agent_handlers_map.get_handler("documentation_specialist")
            if doc_handler:
                print(f"📚 正在管理复杂度和连贯性...", end="", flush=True)
                await self._update_documentation_for_chapter(
                    new_content, chapter_count, doc_handler
                )
                print(" 完成!")

            # 应用环境和情绪节拍优化（如果可用）
            env_handler = self.agent_handlers_map.get_handler("write_enviroment_specialist")
            rate_handler = self.agent_handlers_map.get_handler("write_rate_specialist")

            if env_handler or rate_handler:
                print(f"🎨 正在优化感官体验和情绪节拍...", end="", flush=True)
                # 优化感官呈现和情绪节拍（如果代理可用）
                if env_handler:
                    env_optimization = await self._optimize_environment_descriptions(new_content, chapter_info, env_handler)

                if rate_handler:
                    rate_optimization = await self._optimize_rhythm(new_content, chapter_info, rate_handler)
                print(" 完成!")

            # 计算中文字符的实际数量（更符合用户直觉的指标，包含扩展中文字符）
            import re
            # 匹配更广范围的中文字符，包括基本汉字、扩展A、B、C、D区以及中文标点符号
            chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]'
            chinese_chars_count = len(re.findall(chinese_pattern, current_content))

            # 获取目标汉字数 - 优先使用min_chinese_chars，如果未设置则使用total_target_length
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))

            # 用汉字数量计算主要进度，这是用户真正关心的
            chinese_progress = min(100, int(chinese_chars_count / target_chinese_chars * 100))
            print(f"📊 进度摘要: [{chinese_progress}%] 总计 {len(chapters)} 章节 | {chinese_chars_count} 中文汉字 (目标: {target_chinese_chars})")

            # 通知进度回调 - 使用汉字进度作为主要指标
            if self.progress_callback:
                await self.progress_callback(
                    "章节创作",
                    f"章节完成 {chapter_count}",
                    f"第 {chapter_count} 章节生成完成，当前汉字进度 {chinese_progress}% ({chinese_chars_count}/{target_chinese_chars} 汉字)",
                    chinese_progress / 100.0  # 使用汉字进度作为主要指标
                )

            # 计算中文字符的实际数量
            import re
            # 匹配更广范围的中文字符，包括基本汉字、扩展A、B、C、D区以及中文标点符号
            chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]'
            chinese_chars_count = len(re.findall(chinese_pattern, current_content))

            # 获取目标汉字数
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", 5000)

            print(f"📈 中文汉字统计: {chinese_chars_count} 汉字 (目标: {target_chinese_chars} 汉字)")

            # 检查是否达到目标汉字数
            if chinese_chars_count >= target_chinese_chars:
                print(f"🎯 达到目标汉字数 {target_chinese_chars} 字，停止生成更多章节")
                if self.progress_callback:
                    await self.progress_callback(
                        "章节创作",
                        "达到目标",
                        f"已完成目标汉字数 {target_chinese_chars} 字",
                        1.0
                    )
                break
            elif chapter_decision.get("should_end", False):
                print(f"🤖 AI认为当前可以结束章节，但继续生成以达到目标汉字数")
                # 如果AI认为可以结束但还没达到目标汉字数，则继续
                continue

            # 检查整体故事完成度
            print(f"📊 正在评估整体进度...", end="", flush=True)
            story_evaluation = await self.chapter_decision_engine.evaluate_overall_progress(
                chapters, research_data
            )
            print(" 完成!")

            print(f"   📊 整体进度评估: {story_evaluation['summary']}")

            # 检查是否需要继续或达到长度限制
            chinese_chars_count = len(re.findall(r'[\\u4e00-\\u9fff]', current_content))
            if not story_evaluation.get("is_continuing", False) or chinese_chars_count >= 5000:
                print(f"   ✅ AI认为故事已达到合适的结束点或已达到长度限制 ({chinese_chars_count} 中文汉字)")
                if self.progress_callback:
                    # 使用实际目标汉字数来计算进度，而不是固定5000
                    target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))
                    actual_progress = min(1.0, chinese_chars_count/max(target_chinese_chars, 1))  # 确保分母不为0
                    await self.progress_callback(
                        "章节创作",
                        "AI评估结束",
                        f"AI认为已达到合适的结束点，共 {chinese_chars_count} 中文汉字 (目标: {target_chinese_chars})",
                        actual_progress
                    )
                break

        full_story = "\\n\\n".join(chapters)

        # 使用汉字数计算最终进度，更符合用户直觉
        import re
        # 匹配更广范围的中文字符，包括基本汉字、扩展A、B、C、D区以及中文标点符号
        chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]'
        final_chinese_chars = len(re.findall(chinese_pattern, full_story))
        target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))
        final_progress = min(100, int(final_chinese_chars / target_chinese_chars * 100))

        print(f"\\n🎉 创作完成!")
        print(f"📈 最终进度: {final_progress}% | 共 {chapter_count} 段 | {final_chinese_chars} 中文汉字")
        print(f"📊 章节详情: {len(chapters)} 个章节")
        print(f"📝 AI驱动动态创作过程结束")

        # 通知进度回调 - 最终完成
        if self.progress_callback:
            # 计算实际进度百分比，避免总是显示100%
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))
            final_progress = min(1.0, final_chinese_chars/max(target_chinese_chars, 1))  # 确保分母不为0
            await self.progress_callback(
                "章节创作",
                "创作完成",
                f"动态章节创作完成，共 {chapter_count} 章节，{final_chinese_chars} 中文汉字 (目标: {target_chinese_chars})",
                final_progress  # 使用实际进度而不是恒定的1.0
            )

        # 添加创作阶段的会议纪要
        if hasattr(self.conversation_manager, 'add_meeting_minutes'):
            # 获取参与创作过程的处理器
            active_handlers = []
            if self.agent_handlers_map.get_handler("writer"):
                active_handlers.append("writer")
            if self.agent_handlers_map.get_handler("documentation_specialist"):
                active_handlers.append("documentation_specialist")
            if self.agent_handlers_map.get_handler("write_enviroment_specialist"):
                active_handlers.append("write_enviroment_specialist")
            if self.agent_handlers_map.get_handler("write_rate_specialist"):
                active_handlers.append("write_rate_specialist")
            if self.chapter_decision_engine:
                active_handlers.append("chapter_decision_engine")
            if self.continuity_manager:
                active_handlers.append("continuity_manager")

            # 使用汉字数而非总字符数来创建更准确的摘要
            import re
            # 匹配更广范围的中文字符，包括基本汉字、扩展A、B、C、D区以及中文标点符号
            chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]'
            final_chinese_chars = len(re.findall(chinese_pattern, full_story))
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))

            # 创建摘要
            creation_summary = f"动态章节创作结束，共生成 {chapter_count} 个章节，总长度 {final_chinese_chars} 汉字，目标 {target_chinese_chars} 汉字"

            # 添加章节评审总结
            eval_summary_parts = []
            if 'chapter_evaluations' in locals() and chapter_evaluations:
                high_risk_chapters = []
                for ch_num, eval_data in chapter_evaluations.items():
                    if isinstance(eval_data, dict) and "reader_experience" in eval_data:
                        reader_exp = eval_data["reader_experience"]
                        if reader_exp.get("drop_off_risk", "").lower() == "high" or reader_exp.get("engagement_level", "").lower() == "low":
                            high_risk_chapters.append(str(ch_num))

                if high_risk_chapters:
                    eval_summary_parts.append(f"高风险章节: {', '.join(high_risk_chapters)}")

            eval_summary = "; ".join(eval_summary_parts) if eval_summary_parts else "无特别风险章节"

            self.conversation_manager.add_meeting_minutes(
                stage="creation_phase",
                participants=active_handlers,
                summary=creation_summary,
                decisions=[
                    f"生成章节: {chapter_count} 章",
                    f"总汉字数: {final_chinese_chars} 汉字",
                    f"目标达成: {'是' if final_chinese_chars >= target_chinese_chars else '否'}",
                    f"AI驱动决策: {'已启用' if CREATION_CONFIG.get('enable_dynamic_chapters', True) else '未启用'}",
                    f"章节评审: {eval_summary}"
                ],
                turn_count=chapter_count  # 每章一轮
            )

            # 实时保存阶段性报告
            if hasattr(self.conversation_manager, 'save_interim_report'):
                self.conversation_manager.save_interim_report("creation_phase")

        return full_story

    async def _update_documentation_for_chapter(self, chapter: str, chapter_num: int, doc_handler=None):
        """
        使用文档专门化处理器更新文档
        """
        if not doc_handler:
            doc_handler = self.agent_handlers_map.get_handler("documentation_specialist")
        if not doc_handler:
            return

        # 要求文档专家提取关键信息并更新档案
        try:
            doc_task = f"""
请从以下内容的第 {chapter_num} 部分中提取关键信息并更新档案：
{chapter}

返回JSON格式，包含：characters, timeline, world_rules, foreshadowing 等信息。
"""
            doc_result = await doc_handler.update_archive(chapter, chapter_num)
            doc_content = doc_result.get("raw_content", "")

            # 也进行一致性检查
            consistency_content = await doc_handler.check_continuity(
                chapter,
                self.documentation_manager.get_documentation() if self.documentation_manager else None
            )

            # 保存到对话历史
            self.conversation_manager.add_documentation(
                chapter_num,
                doc_result.get("archive_update", {}),
                consistency_content.get("continuity_check", {})
            )
        except Exception as e:
            print(f"   ⚠️  档案更新出错: {e}")

    async def _optimize_environment_descriptions(self, chapter: str, chapter_info: dict, env_handler=None):
        """
        使用环境专家优化环境描述
        """
        if not env_handler:
            env_handler = self.agent_handlers_map.get_handler("write_enviroment_specialist")
        if not env_handler:
            return

        try:
            env_result = await env_handler.enhance_environment_description(chapter)
            return env_result
        except Exception as e:
            print(f"   ⚠️  环境描写优化出错: {e}")
            return None

    async def _optimize_rhythm(self, chapter: str, chapter_info: dict, rhythm_handler=None):
        """
        使用节拍专家优化叙事节奏
        """
        if not rhythm_handler:
            rhythm_handler = self.agent_handlers_map.get_handler("write_rate_specialist")
        if not rhythm_handler:
            return

        try:
            rhythm_result = await rhythm_handler.analyze_narrative_rhythm(chapter)
            return rhythm_result
        except Exception as e:
            print(f"   ⚠️  节奏调整优化出错: {e}")
            return None