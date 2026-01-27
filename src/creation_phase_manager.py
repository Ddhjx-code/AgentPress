import asyncio
import re
from typing import Dict, List, Any
from datetime import datetime
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from core.chapter_decision_engine import ChapterDecisionEngine
from core.continuity_manager import ContinuityManager
from core.story_state_manager import StoryStateManager
from src.creation_context_builder import CreationContextBuilder
from config import CREATION_CONFIG, GROUPCHAT_CONFIGS
from utils import extract_content, extract_all_json


class CreationPhaseManager:
    """专门处理创作阶段的类，从NovelWritingPhases中分离出来"""

    def __init__(self, conversation_manager: ConversationManager,
                 documentation_manager: DocumentationManager,
                 agent_manager: AgentManager):
        self.conversation_manager = conversation_manager
        self.documentation_manager = documentation_manager
        self.agent_manager = agent_manager
        self.chapter_decision_engine = None  # For dynamic chapter decisions
        self.continuity_manager = None  # For cross-chapter consistency
        self.story_state_manager = None  # For tracking multi-chapter story state
        self.context_builder = CreationContextBuilder()
        self.progress_callback = None  # For progress notifications

    async def execute_creation_phase(self, research_data: Dict[str, Any]) -> str:
        """执行创作阶段的主要入口点"""
        # Initialize the managers
        if self.agent_manager:
            self.chapter_decision_engine = ChapterDecisionEngine(self.agent_manager)
            self.continuity_manager = ContinuityManager(self.agent_manager)
            self.story_state_manager = StoryStateManager()

        # 保存research_data以备后续检查使用（特别是字数建议）
        self.research_data = research_data

        # Use dynamic chapter decision instead of fixed number
        return await self.execute_dynamic_chapters_creation(research_data)

    async def execute_dynamic_chapters_creation(self, research_data: Dict[str, Any]) -> str:
        """AI驱动的动态章节创作"""
        print("\n" + "="*60)
        print("✍️  第二阶段：AI驱动的动态章节创作")
        print("="*60)

        if not self.agent_manager:
            # Fallback implementation using single chapter
            return await self._create_single_chapter(research_data)

        writer = self.agent_manager.get_agent("writer")
        if not writer:
            return "❌ 未找到writer代理"

        chapters = []
        target_per_chapter = CREATION_CONFIG.get("target_length_per_chapter", 2000)

        # Generate dynamic chapter plan
        chapter_plan = await self.chapter_decision_engine.create_chapter_outline(
            research_data.get("outline", "创意构思")
        )

        print(f"📖 基于AI分析的动态章节规划，预期创作章节: {len(chapter_plan) if chapter_plan else '动态确定'}")
        current_content = ""
        chapter_count = 0

        # Create story in state manager
        story_id = f"story_{datetime.now().timestamp()}"
        self.story_state_manager.create_story(
            story_id=story_id,
            title=research_data.get('outline', 'AI生成的故事'),
            initial_metadata={'research_data': research_data}
        )

        # 检查research_data中的字数建议 - 新增：从研究阶段获取AI提取的目标字数
        target_length = CREATION_CONFIG.get("total_target_length", 5000)
        ai_suggested_length = None

        # 检查是否从research阶段传递了AI识别的目标字数
        if "target_length_suggestion" in research_data and research_data["target_length_suggestion"]:
            suggested_info = research_data["target_length_suggestion"]
            if isinstance(suggested_info, dict) and "suggested" in suggested_info:
                ai_suggested_length = suggested_info["suggested"]

        # 目标字数优先级: 研究阶段AI分析 > CLI参数/配置文件 > 默认值
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
            # 从config manager获取当前设置（如果可用）
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", 5000)
            target_total_chars = CREATION_CONFIG.get("total_target_length", 6000)
            print(f"🔍 预计目标: 生成约 {target_chinese_chars} 汉字的故事内容 (使用配置值)")

        # 最终使用AI建议的汉字数作为主要目标
        if ai_suggested_length:
            target_length = target_total_chars
            # 另更新本地target_chinese_chars变量以便后续使用
            target_chinese_chars = ai_suggested_length
        else:
            target_length = target_total_chars

        print(f"📏 故事进度追踪 [ 0% ] (目标: {target_chinese_chars} 汉字)")

        print(f"📏 故事进度追踪 [ 0% ]")

        while True:  # Continue until AI decides to stop
            chapter_count += 1
            print(f"\n--- 📘 章节 {chapter_count} 开始创作 ---")
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

            # Prepare context for next chapter
            context = self.context_builder.build_context_for_chapter_creation(
                chapter_count, research_data, chapters, target_per_chapter, current_content
            )

            # Generate content for this iteration
            print(f"🤖 AI正在创作第 {chapter_count} 部分内容...", end="", flush=True)
            result = await writer.run(task=context)
            new_content = extract_content(result.messages)
            print(" 完成!")

            # Combine with existing content
            if current_content:
                current_content += "\n\n" + new_content
            else:
                current_content = new_content

            chapters.append(new_content)

            print(f"   ✅ 新增内容 {len(new_content)} 字符 | 累计: {len(current_content)} 字符")

            # Create chapter info dictionary
            chapter_info = {
                "chapter_num": chapter_count,
                "content": new_content,
                "word_count": len(new_content),
                "summary": new_content[:200] + "..." if len(new_content) > 200 else new_content,
                "title": f"第{chapter_count}章",  # Will be updated by decision engine
                "story_id": story_id
            }

            # Use chapter decision engine to determine if we should continue
            print(f"🧠 AI正在分析章节决策...", end="", flush=True)
            chapter_decision = await self.chapter_decision_engine.should_end_chapter(
                current_content,
                research_data
            )
            print(" 完成!")

            # Update chapter title from decision
            suggested_title = chapter_decision.get("suggested_title", f"第{chapter_count}章")
            chapter_info["title"] = suggested_title

            print(f"   🤖 章节分析: {chapter_decision['reasoning']} (置信度: {chapter_decision['confidence']:.2f})")

            # Create chapter in story state manager
            if self.story_state_manager:
                print(f"📝 正在记录章节状态...", end="", flush=True)
                chapter_state = self.story_state_manager.create_chapter(
                    story_id=story_id,
                    title=suggested_title,
                    content=new_content
                )
                print(f" 完成! ({chapter_state.chapter_id})")

            # Update continuity manager with current chapter
            if self.continuity_manager:
                await self.continuity_manager.update_for_chapter(new_content, chapter_info)

            # Check continuity for this chapter
            if self.continuity_manager:
                print(f"🔍 执行连续性检查...", end="", flush=True)
                continuity_report = await self.continuity_manager.check_continuity(
                    new_content, chapter_count
                )
                print(" 完成!")
                print(f"   📋 连续性检查: {continuity_report['summary']}")

                # If there are high-severity inconsistencies, we could consider revising
                high_severity_issues = [issue for issue in continuity_report.get('inconsistencies', [])
                                      if issue.get('severity') == 'high']
                if high_severity_issues:
                    print(f"   ⚠️  检测到 {len(high_severity_issues)} 个高严重性连续性问题")
                    for issue in high_severity_issues:
                        print(f"      - {issue['element']}: {issue['issue']}")

            # Create chapter in conversation manager
            self.conversation_manager.add_story_version(
                chapter_count,
                current_content,
                {"chapter_num": chapter_count, "decision": chapter_decision, "continuity": continuity_report}
            )

            # Apply consistency and complexity management if agents available
            doc_agent = self.agent_manager.get_agent("documentation_specialist")
            if doc_agent:
                print(f"📚 正在管理复杂度和连贯性...", end="", flush=True)
                await self._update_documentation_for_chapter(
                    new_content, chapter_count, doc_agent
                )
                print(" 完成!")

            # Apply environmental and emotional rhythm improvements if available
            env_agent = self.agent_manager.get_agent("write_enviroment_specialist")
            rate_agent = self.agent_manager.get_agent("write_rate_specialist")

            if env_agent or rate_agent:
                print(f"🎨 正在优化感官体验和情绪节拍...", end="", flush=True)
                # 优化感官呈现和情绪节奏（如果代理可用）
                if env_agent:
                    env_optimization = await self._optimize_environment_descriptions(new_content, chapter_info, env_agent)

                if rate_agent:
                    rate_optimization = await self._optimize_rhythm(new_content, chapter_info, rate_agent)
                print(" 完成!")

            # 计算中文汉字的实际数量（更符合用户直觉的指标）
            chinese_chars_count = len(re.findall(r'[\\u4e00-\\u9fff]', current_content))

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

            # 计算中文汉字的实际数量
            chinese_chars_count = len(re.findall(r'[\u4e00-\u9fff]', current_content))

            # 获取目标汉字数
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", 5000)

            print(f"📈 中文汉字统计: {chinese_chars_count} 汉字 (目标: {target_chinese_chars} 汉字)")

            # Check if we reached the target Chinese character count
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

            # Check overall story completion
            print(f"📊 正在评估整体进度...", end="", flush=True)
            story_evaluation = await self.chapter_decision_engine.evaluate_overall_progress(
                chapters, research_data
            )
            print(" 完成!")

            print(f"   📊 整体进度评估: {story_evaluation['summary']}")

            # 检查是否需要继续或者达到长度限制
            chinese_chars_count = len(re.findall(r'[\u4e00-\u9fff]', current_content))
            if not story_evaluation.get("is_continuing", False) or chinese_chars_count >= 5000:
                print(f"   ✅ AI认为故事已达到合适的结束点或已达到长度限制 ({chinese_chars_count} 中文汉字)")
                if self.progress_callback:
                    await self.progress_callback(
                        "章节创作",
                        "AI评估结束",
                        f"AI认为已达到合适的结束点，共 {chinese_chars_count} 中文汉字",
                        min(1.0, chinese_chars_count/5000.0)  # 进度不能超过100%
                    )
                break

        full_story = "\n\n".join(chapters)

        # 使用汉字数计算最终进度，更符合用户直觉
        final_chinese_chars = len(re.findall(r'[\\u4e00-\\u9fff]', full_story))
        target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))
        final_progress = min(100, int(final_chinese_chars / target_chinese_chars * 100))

        print(f"\n🎉 创作完成!")
        print(f"📈 最终进度: {final_progress}% | 共 {chapter_count} 段 | {final_chinese_chars} 中文汉字")
        print(f"📊 章节详情: {len(chapters)} 个章节")
        print(f"📝 AI驱动动态创作过程结束")

        # 通知进度回调 - 最终完成
        if self.progress_callback:
            await self.progress_callback(
                "章节创作",
                "创作完成",
                f"动态章节创作完成，共 {chapter_count} 章节，{final_chinese_chars} 中文汉字",
                1.0
            )

        # 添加创作阶段的会议纪要
        if hasattr(self.conversation_manager, 'add_meeting_minutes'):
            # 获取参与创作过程的代理
            active_agents = []
            if self.agent_manager.get_agent("writer"):
                active_agents.append("writer")
            if self.agent_manager.get_agent("documentation_specialist"):
                active_agents.append("documentation_specialist")
            if self.agent_manager.get_agent("write_enviroment_specialist"):
                active_agents.append("write_enviroment_specialist")
            if self.agent_manager.get_agent("write_rate_specialist"):
                active_agents.append("write_rate_specialist")
            if self.chapter_decision_engine:
                active_agents.append("chapter_decision_engine")
            if self.continuity_manager:
                active_agents.append("continuity_manager")

            # 使用汉字数而非总字符数来创建更准确的摘要
            final_chinese_chars = len(re.findall(r'[\\u4e00-\\u9fff]', full_story))
            target_chinese_chars = CREATION_CONFIG.get("min_chinese_chars", CREATION_CONFIG.get("total_target_length", 5000))

            # 创建摘要
            creation_summary = f"动态章节创作结束，共生成 {chapter_count} 个章节，总长度 {final_chinese_chars} 汉字，目标 {target_chinese_chars} 汉字"

            self.conversation_manager.add_meeting_minutes(
                stage="creation_phase",
                participants=active_agents,
                summary=creation_summary,
                decisions=[
                    f"生成章节: {chapter_count} 章",
                    f"总汉字数: {final_chinese_chars} 汉字",
                    f"目标达成: {'是' if final_chinese_chars >= target_chinese_chars else '否'}",
                    f"AI驱动决策: {'已启用' if CREATION_CONFIG.get('enable_dynamic_chapters', True) else '未启用'}"
                ],
                turn_count=chapter_count  # 每章一轮
            )

            # 实时保存阶段性报告
            if hasattr(self.conversation_manager, 'save_interim_report'):
                self.conversation_manager.save_interim_report("creation_phase")

        return full_story

    async def _create_single_chapter(self, research_data: Dict[str, Any]):
        """单章节创建的降级实现"""
        from core.config_manager import ConfigManager
        try:
            config_manager = ConfigManager()
            target_length = config_manager.get_creation_config().get("total_target_length", 5000)
        except ImportError:
            target_length = CREATION_CONFIG.get("total_target_length", 5000)

        chapters = [f"基于 {research_data.get('outline', '创意构思')} 展开的故事片段"]
        story = "\n\n".join(chapters)
        return story

    async def _update_documentation_for_chapter(self, chapter: str, chapter_num: int, doc_agent=None):
        """使用文档专门化代理更新文档"""
        if not doc_agent:
            doc_agent = self.agent_manager.get_agent("documentation_specialist")
        if not doc_agent:
            return

        # 任务让文档专家提取关键信息并更新档案
        doc_task = f"""
请从以下内容的第 {chapter_num} 部分中提取关键信息并更新档案：
{chapter}

返回JSON格式，包含：characters, timeline, world_rules, foreshadowing 等信息。
"""
        try:
            doc_result = await doc_agent.run(task=doc_task)
            doc_content = extract_content(doc_result.messages)
            self.documentation_manager.update_documentation(doc_content)

            # Also perform consistency check
            consistency_task = f"""
基于当前档案检查以下内容的一致性：
章节内容：{chapter[:2000]}
"""
            consistency_result = await doc_agent.run(task=consistency_task)
            consistency_content = extract_content(consistency_result.messages)

            # Save to conversation history
            self.conversation_manager.add_documentation(
                chapter_num,
                extract_all_json(doc_content),
                extract_all_json(consistency_content)
            )
        except Exception as e:
            print(f"   ⚠️  档案更新出错: {e}")

    async def _optimize_environment_descriptions(self, chapter: str, chapter_info: dict, env_agent=None):
        """使用环境专家优化环境描述"""
        if not env_agent:
            env_agent = self.agent_manager.get_agent("environment_specialist")
        if not env_agent:
            return

        # 环境专家的优化任务
        env_task = f"""
请评估以下章节的环境描写、感官细节和氛围营造效果：
{chapter}

请针对以下方面提供优化建议：
- 增强环境描写的生动性
- 补充感官细节
- 优化氛围营造
- 让环境描写更好地服务于情节和情绪

返回JSON格式，包含：suggested_improvements, enhanced_environment_descriptions
"""
        try:
            env_result = await env_agent.run(task=env_task)
            env_content = extract_content(env_result.messages)
            env_data = extract_all_json(env_content)
            return env_data
        except Exception as e:
            print(f"   ⚠️  环境描写优化出错: {e}")
            return None

    async def _optimize_rhythm(self, chapter: str, chapter_info: dict, rhythm_agent=None):
        """使用节奏专家优化叙事节奏"""
        if not rhythm_agent:
            rhythm_agent = self.agent_manager.get_agent("rhythm_specialist")
        if not rhythm_agent:
            return

        # 节奏专家的优化任务
        rhythm_task = f"""
请评估以下章节的叙事节奏、情绪曲线和信息安排：
{chapter}

请针对以下方面提供优化建议：
- 调整叙事节奏的快慢变化
- 优化情绪曲线的设计
- 改善信息密度的安排
- 提升读者注意力引导效果

返回JSON格式，包含：rhythm_analysis, suggested_improvements
"""
        try:
            rhythm_result = await rhythm_agent.run(task=rhythm_task)
            rhythm_content = extract_content(rhythm_result.messages)
            rhythm_data = extract_all_json(rhythm_content)
            return rhythm_data
        except Exception as e:
            print(f"   ⚠️  节奏调整优化出错: {e}")
            return None