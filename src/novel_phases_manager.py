import json
import asyncio
from typing import List, Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from core.chapter_decision_engine import ChapterDecisionEngine
from core.continuity_manager import ContinuityManager
from core.story_state_manager import StoryStateManager
from config import GROUPCHAT_CONFIGS, CREATION_CONFIG, SCORE_THRESHOLD, MAX_REVISION_ROUNDS
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary


class NovelWritingPhases:
    """Complete implementation for the multi-phase novel writing process"""

    def __init__(self, conversation_manager: ConversationManager,
                 documentation_manager: DocumentationManager):
        self.conversation_manager = conversation_manager
        self.documentation_manager = documentation_manager
        self.agents_manager = None  # Will be set by caller
        self.chapter_decision_engine = None  # For dynamic chapter decisions
        self.continuity_manager = None  # For cross-chapter consistency
        self.story_state_manager = None  # For tracking multi-chapter story state
        self.progress_callback = None  # For progress notifications

    async def async_phase1_research_and_planning(self, novel_concept: str) -> Dict[str, Any]:
        """Async version of phase 1 with complete implementation"""
        print("\n" + "="*60)
        print("📚 第一阶段：创意研究和规划")
        print("="*60)

        if not self.agents_manager:
            # Fallback implementation
            return {
                "outline": f"基于 {novel_concept} 的大纲",
                "world_setting": "山海经世界观",
                "character_profiles": [],
                "key_conflicts": [],
                "research_data": f"背景研究：{novel_concept}"
            }

        config = GROUPCHAT_CONFIGS["research_phase"]
        agent_list = self.agents_manager.get_agents(config["agents"])

        print(f"\n🔧 GroupChat 配置:")
        print(f"   Agents: {[agent.name for agent in agent_list]}")
        print(f"   Max turns: {config['max_turns']}")

        # Sequential research and planning
        mythologist = self.agents_manager.get_agent("mythologist")
        writer = self.agents_manager.get_agent("writer")

        if mythologist:
            myth_task = f"分析这个网络小说创意的世界观设定：{novel_concept}\n返回JSON格式的分析结果。"
            myth_result = await mythologist.run(task=myth_task)
            myth_content = extract_content(myth_result.messages)

        if writer:
            research_summary = myth_content if 'myth_content' in locals() else novel_concept
            writer_task = f"""
根据以下背景信息设计故事大纲：{research_summary}

创意需求：{novel_concept}

请设计：
1. 故事的三幕结构
2. 主要角色及性格
3. 核心冲突和转折点
4. 预期的故事走向

返回JSON格式。
            """

            writer_result = await writer.run(task=writer_task)
            writer_content = extract_content(writer_result.messages)

        conversation = (myth_content if 'myth_content' in locals() else '') + "\n---\n" + (writer_content if 'writer_content' in locals() else '')
        self.conversation_manager.add_conversation("phase1_research", conversation)

        # Extract actual research data
        combined_json = {}
        for content in [myth_content if 'myth_content' in locals() else '', writer_content if 'writer_content' in locals() else '']:
            json_objects = extract_all_json(content)
            for json_obj in json_objects:
                if isinstance(json_obj, dict):
                    combined_json.update(json_obj)

        # Ensure we have default values
        result = {
            "outline": combined_json.get("outline", f"基于 {novel_concept} 的大纲"),
            "world_setting": combined_json.get("world_setting", "山海经世界观"),
            "character_profiles": combined_json.get("character_profiles", [
                {"name": "主角", "role": "hero", "trait": "勇敢"}
            ]),
            "key_conflicts": combined_json.get("key_conflicts", ["初期冲突"]),
            "research_data": combined_json.get("research_data", f"背景研究：{novel_concept}"),
            "background": combined_json.get("background", f"背景设定：{novel_concept}")
        }

        print(f"✅ 研究阶段完成")
        print(f"   提取字段: {list(result.keys())}")

        return result

    async def async_phase2_creation(self, research_data: Dict[str, Any]) -> str:
        """Async phase 2: Creation with dynamic AI-driven chapter decisions"""
        # Initialize the chapter decision engine, continuity manager and story state manager
        self.chapter_decision_engine = ChapterDecisionEngine(self.agents_manager)
        self.continuity_manager = ContinuityManager(self.agents_manager)

        # Initialize story state manager and create story state
        self.story_state_manager = StoryStateManager()

        # Use dynamic chapter decision instead of fixed number
        return await self._async_phase2_dynamic_chapters(research_data)

    async def _async_phase2_dynamic_chapters(self, research_data: Dict[str, Any]) -> str:
        """Dynamic chapter creation using AI decision engine"""
        print("\n" + "="*60)
        print("✍️  第二阶段：AI驱动的动态章节创作")
        print("="*60)

        if not self.agents_manager:
            # Fallback implementation using single chapter
            return await self._async_phase2_single_chapter(research_data)

        writer = self.agents_manager.get_agent("writer")
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
        from datetime import datetime
        story_id = f"story_{datetime.now().timestamp()}"
        self.story_state_manager.create_story(
            story_id=story_id,
            title=research_data.get('outline', 'AI生成的故事'),
            initial_metadata={'research_data': research_data}
        )

        while True:  # Continue until AI decides to stop
            chapter_count += 1
            print(f"\n--- 章节 {chapter_count} ---")

            # Prepare context for next chapter
            context = self._prepare_creation_context(
                chapter_count, research_data, chapters, target_per_chapter, current_content
            )

            # Generate content for this iteration
            result = await writer.run(task=context)
            new_content = extract_content(result.messages)

            # Combine with existing content
            if current_content:
                current_content += "\n\n" + new_content
            else:
                current_content = new_content

            chapters.append(new_content)

            print(f"   ✅ 新增内容（{len(new_content)} 字符）")

            # Create chapter info dictionary
            chapter_info = {
                "chapter_num": chapter_count,
                "content": new_content,
                "word_count": len(new_content),
                "summary": new_content[:200] + "..." if len(new_content) > 200 else new_content,
                "title": f"第{chapter_count}章"  # Will be updated by decision engine
            }

            # Use chapter decision engine to determine if we should continue
            chapter_decision = await self.chapter_decision_engine.should_end_chapter(
                current_content,
                research_data
            )

            # Update chapter title from decision
            suggested_title = chapter_decision.get("suggested_title", f"第{chapter_count}章")
            chapter_info["title"] = suggested_title

            print(f"   🤖 AI章节分析: {chapter_decision['reasoning']} (置信度: {chapter_decision['confidence']:.2f})")

            # Create chapter in story state manager
            if self.story_state_manager:
                chapter_state = self.story_state_manager.create_chapter(
                    story_id=story_id,
                    title=suggested_title,
                    content=new_content
                )
                print(f"   📌 章节状态已记录: {chapter_state.chapter_id}")

            # Update continuity manager with current chapter
            if self.continuity_manager:
                await self.continuity_manager.update_for_chapter(new_content, chapter_info)

            # Check continuity for this chapter
            if self.continuity_manager:
                continuity_report = await self.continuity_manager.check_continuity(
                    new_content, chapter_count
                )
                print(f"   🔍 连续性检查: {continuity_report['summary']}")

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

            # Apply documentation if agent available
            doc_agent = self.agents_manager.get_agent("documentation_specialist")
            if doc_agent:
                await self._update_documentation_for_chapter(
                    current_content, chapter_count, doc_agent
                )

            # Check if AI suggests ending the story - 更严格的章节控制
            if chapter_decision.get("should_end", False) or chapter_count >= 1:  # 限制为1章以控制长度
                print(f"   📝 AI认为当前是合适的章节结束点或达到章数限制，停止生成更多章节")
                break

            # 检查总长度 - 增加总长度强制限制
            current_total_length = len(current_content)
            if current_total_length >= CREATION_CONFIG.get("total_target_length", 3000):
                print(f"   📏 总长度达到目标限制 ({current_total_length} 字符，目标: {CREATION_CONFIG.get('total_target_length', 3000)} 字符)，停止生成")
                break

            # Check overall story completion
            story_evaluation = await self.chapter_decision_engine.evaluate_overall_progress(
                chapters, research_data
            )

            print(f"   📊 整体进度评估: {story_evaluation['summary']}")

            # 检查是否需要继续或者达到长度限制
            if not story_evaluation.get("is_continuing", False) or current_total_length >= CREATION_CONFIG.get("total_target_length", 3000):
                print(f"   ✅ AI认为故事已达到合适的结束点或已达到长度限制")
                break

        full_story = "\n\n".join(chapters)

        print(f"\n🤖 AI驱动动态创作完成！共 {chapter_count} 段，{len(full_story)} 字")
        return full_story

    def _prepare_creation_context(self, chapter_num: int, research_data: Dict,
                                previous_chapters: List[str], target_length: int, current_content: str) -> str:
        """Prepare content creation context using current information"""
        context = f"""
第 {chapter_num} 部分创作要求 (动态章节)

【故事研究数据】
{json.dumps(research_data, ensure_ascii=False, indent=2)[:1000]}

【整体进展】
已创作了 {len(previous_chapters)} 个部分内容

【已有内容片段（供参考连贯性）】
"""
        if previous_chapters:
            context += f"...({len(previous_chapters)} 个较早的片段)\n{previous_chapters[-1][-500:]}\n\n"
        else:
            context += "这是开篇内容\n\n"

        context += f"""
【当前内容长度】
当前总内容长度: {len(current_content)} 字符

【本段创作要求】
建议长度: {target_length} 字左右
- 保持叙述连贯性
- 引入新情节点或发展现有冲突
- 为可能的后续章节创建悬念或自然终结点
- 专注高质量的叙事内容
- 直接输出内容，无需额外说明
"""
        return context

    async def _async_phase2_multiple_chapters(self, research_data: Dict[str, Any], num_chapters: int) -> str:
        """Legacy async multi-chapter creation (for compatibility) - but enhanced with some dynamic features"""
        print("\n" + "="*60)
        print(f"✍️  第二阶段：传统多章节创作（{num_chapters}章-已弃用，改为AI驱动）")
        print("="*60)

        # 提示用户现在应该使用AI驱动的动态模式
        print("💡 提示: 系统已升级为AI驱动的动态章节模式，将在下一个版本中启用")

        if not self.agents_manager:
            # Simulated multi-chapter for fallback
            chapters = []
            for ch in range(1, num_chapters + 1):
                part = f"第{ch}章：{research_data.get('outline', '章节内容')[:50]}的展开..."
                chapters.append(part)
                self.conversation_manager.add_story_version(ch, part)

            story = "\n\n".join(chapters)
            return story

        # Get writer and documentation specialist if available
        writer = self.agents_manager.get_agent("writer")
        doc_agent = self.agents_manager.get_agent("documentation_specialist")

        if not writer:
            return "❌ 未找到writer代理"

        chapters = []
        target_length = CREATION_CONFIG.get("target_length_per_chapter", 2000)

        for chapter_num in range(1, num_chapters + 1):
            print(f"\n--- 第 {chapter_num} 章 ---")

            # Create context with previous chapters and documentation
            context = await self._prepare_chapter_context(
                chapter_num, research_data, chapters, target_length
            )

            # Create chapter
            chapter_result = await writer.run(task=context)
            chapter = extract_content(chapter_result.messages)
            chapters.append(chapter)

            print(f"   ✅ 完成（{len(chapter)} 字）")

            # If we have the chapter decision engine available, try to use its insights
            if self.chapter_decision_engine:
                chapter_decision = await self.chapter_decision_engine.should_end_chapter(
                    chapter, research_data
                )
                print(f"   🤖 AI章节分析: {chapter_decision['reasoning']}")

            # Apply documentation and consistency checks
            if doc_agent:
                await self._update_documentation_for_chapter(chapter, chapter_num)
            else:
                # Just update documentation if no agent
                chapter_info = {
                    "chapter_num": chapter_num,
                    "word_count": len(chapter),
                    "summary": chapter[:200] + "..."
                }
                doc_content = json.dumps(chapter_info, ensure_ascii=False)
                self.documentation_manager.update_documentation(doc_content)

            # Save to conversation manager
            self.conversation_manager.add_story_version(
                chapter_num, chapter, {"chapter_num": chapter_num, "length": len(chapter)}
            )

            # Periodic consistency checks every few chapters
            if chapter_num % 3 == 0:
                print(f"   🔄 执行中期一致性检查...")
                # Add intermediate review here if needed

        # Combine all chapters
        full_story = "\n\n".join(chapters)

        print(f"\n✅ 多章节创作完成！共 {len(chapters)} 章，{len(full_story)} 字")

        return full_story

    def _prepare_chapter_context(self, chapter_num: int, research_data: Dict,
                                previous_chapters: List[str], target_length: int) -> str:
        """Prepare creation context including documentation"""
        context = f"""
第 {chapter_num} 章创作

【故事背景】
{json.dumps(research_data, ensure_ascii=False, indent=2)[:1000]}

【已有文档】
{self.documentation_manager.get_documentation()[:1000]}

【当前进展】
"""
        if previous_chapters:
            context += f"前 {len(previous_chapters)} 章已创作\n"
            # Include last chapter as reference
            context += f"上次结尾内容：{previous_chapters[-1][-300:]}\n"
        else:
            context += "这是开篇章节\n"

        context += f"""
【创作要求】
- 长度：约 {target_length} 字
- 风格：网络文学风格，保持故事连贯性
- 与已有文档和背景保持一致
- 推进情节发展
- 直接输出章节内容
"""

        return context

    async def _update_documentation_for_chapter(self, chapter: str, chapter_num: int, doc_agent=None):
        """Update documentation using documentation agent"""
        if not doc_agent:
            doc_agent = self.agents_manager.get_agent("documentation_specialist")
        if not doc_agent:
            return

        # Task for documentation specialist to extract key information
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

    async def phase3_review_refinement(self, story: str) -> str:
        """Complete phase 3 implementation for review and refinement with parallel processing"""
        if not self.agents_manager:
            print("⚠️  无代理可用，跳过审查阶段")
            return story

        print("\n" + "="*60)
        print("🔄 第三阶段：多轮评审和修订")
        print("="*60)

        # 通知进度回调开始评审阶段
        if self.progress_callback:
            await self.progress_callback("质量检查", "总体进度", "开始多代理并行评审流程...")

        current_story = story
        version_num = 2

        # 限制评审轮数以控制token消耗，只进行一轮评审
        max_review_rounds = min(MAX_REVISION_ROUNDS, 1)
        for round_num in range(max_review_rounds):
            print(f"\n--- 第 {round_num + 1} 轮评审 ---")

            if self.progress_callback:
                await self.progress_callback(
                    "质量检查",
                    f"轮次 {round_num + 1}",
                    f"正在进行第 {round_num + 1} 轮审查评估...",
                    (round_num / max_review_rounds) if max_review_rounds > 0 else 1.0
                )

            # 通过并行处理获得来自多个代理的反馈
            feedback = await self._get_multifaceted_feedback_parallel(current_story)

            avg_score = calculate_average_score(feedback)

            self.conversation_manager.add_feedback(round_num + 1, feedback)

            print(f"   平均评分: {avg_score:.1f}/100")
            print(f"   反馈摘要:")
            print(format_feedback_summary(feedback))

            # 通知进度回调
            if self.progress_callback:
                await self.progress_callback(
                    "质量检查",
                    f"轮次 {round_num + 1} 完成",
                    f"获得反馈并计算平均分: {avg_score:.1f}/100",
                    (round_num + 0.5) / max_review_rounds if max_review_rounds > 0 else 1.0
                )

            # Check if story passes quality threshold
            if avg_score >= SCORE_THRESHOLD:
                print(f"\n✅ 第 {round_num + 1} 轮评审通过！")
                if self.progress_callback:
                    await self.progress_callback(
                        "质量检查",
                        "评审完成",
                        f"故事达到质量要求 (第 {round_num + 1} 轮通过)",
                        1.0
                    )
                break

            # 检查总长度，避免过长
            current_length = len(current_story)
            if current_length > CREATION_CONFIG.get("total_target_length", 3000) * 1.2:  # 允许1.2倍的扩展
                print(f"\n⚠️  内容长度已超过目标 ({current_length} 字符)，跳过修订阶段")
                break

            # 在我们的优化版本中，跳过修订以控制token消耗
            print(f"\n✅ 完成评审，跳过修订阶段以控制token消耗和长度")
            if self.progress_callback:
                await self.progress_callback(
                    "质量检查",
                    "评审完成",
                    f"跳过修订阶段以控制长度和成本",
                    1.0
                )
            break  # 即使只有1轮，也要确保不会进行完整修订            version_num += 1

        return current_story

    async def _get_multifaceted_feedback_parallel(self, story: str) -> Dict[str, Any]:
        """Get feedback from multiple specialized agents in parallel processing using asyncio.gather"""
        if not self.agents_manager:
            return {"default": {"score": 75, "comments": "No agents available", "suggestions": ["Improve character development"]}}

        agents_to_review = [
            ("fact_checker", "事实与逻辑检查"),
            ("dialogue_specialist", "对话质量评估"),
            ("editor", "整体质量把控")
        ]

        # Create async tasks for all the agents to run them in parallel
        tasks = []
        agent_instances = []

        for agent_name, description in agents_to_review:
            agent = self.agents_manager.get_agent(agent_name)
            if agent:
                agent_instances.append((agent, agent_name, description))
                task = self._run_single_review(agent, agent_name, story)
                tasks.append(task)

        # Execute all review tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        feedback = {}
        for i, (agent, agent_name, description) in enumerate(agent_instances):
            print(f"   📝 {description}中...")
            try:
                # Check if result had an exception
                if i < len(results) and isinstance(results[i], Exception):
                    print(f"   ❌ {agent_name} 评审出错: {results[i]}")
                    feedback[agent_name] = {"score": 60, "error": str(results[i])}
                else:
                    result = results[i]
                    review_data = self._extract_json(result)
                    feedback[agent_name] = result or {
                        "score": 75,
                        "comments": f"Default {agent_name} review",
                        "suggestions": ["General improvement"]
                    }
            except Exception as e:
                print(f"   ❌ {agent_name} 评审出错: {e}")
                feedback[agent_name] = {"score": 60, "error": str(e)}

        return feedback

    async def _run_single_review(self, agent, agent_name: str, story: str):
        """Run a single review task"""
        review_result = await agent.run(task=self._create_review_task(story, agent_name))
        review_content = extract_content(review_result.messages)
        return review_content

    async def _get_multifaceted_feedback(self, story: str) -> Dict[str, Any]:
        """Get feedback from multiple specialized agents - legacy non-parallel version"""
        if not self.agents_manager:
            return {"default": {"score": 75, "comments": "No agents available", "suggestions": ["Improve character development"]}}

        feedback = {}

        agents_to_review = [
            ("fact_checker", "事实与逻辑检查"),
            ("dialogue_specialist", "对话质量评估"),
            ("editor", "整体质量把控")
        ]

        for agent_name, description in agents_to_review:
            agent = self.agents_manager.get_agent(agent_name)
            if agent:
                print(f"   📝 {description}中...")
                try:
                    review_result = await agent.run(task=self._create_review_task(story, agent_name))
                    review_content = extract_content(review_result.messages)
                    review_data = self._extract_json(review_content)
                    feedback[agent_name] = review_data or {
                        "score": 75,
                        "comments": f"Default {agent_name} review",
                        "suggestions": ["General improvement"]
                    }
                except Exception as e:
                    print(f"   ❌ {agent_name} 评审出错: {e}")
                    feedback[agent_name] = {"score": 60, "error": str(e)}

        return feedback

    def _create_review_task(self, story: str, agent_type: str) -> str:
        """Create appropriate review task based on agent type"""
        if agent_type == "fact_checker":
            return f"""
请检查以下故事的事实准确性、逻辑一致性和情节连贯性：
{story[:3000]}

返回评分和改进建议。
"""
        elif agent_type == "dialogue_specialist":
            return f"""
请评估以下故事的对话质量、人物语言特色和表达效果：
{story[:3000]}

返回评分和改进建议。
"""
        else:  # editor
            return f"""
请从整体上评估以下故事的文学质量、情节推进和读者吸引力：
{story[:3000]}

返回评分和改进建议。
"""

    async def _revise_story(self, story: str, feedback: Dict[str, Any]) -> str:
        """Apply revision based on feedback"""
        if not self.agents_manager:
            return story  # No revision without agents

        writer = self.agents_manager.get_agent("writer")
        if not writer:
            return story

        revision_prompt = f"""
根据评审反馈修改故事：

原始故事：
{story[:4000]}

评审反馈：
{json.dumps(feedback, ensure_ascii=False, indent=2)}

请在保持原故事核心的情节下，根据以上反馈进行改进，并返回完整修订版。
"""

        revision_result = await writer.run(task=revision_prompt)
        return extract_content(revision_result.messages)

    async def phase4_final_check(self, story: str) -> str:
        """Complete phase 4 implementation for final quality check"""
        if not self.agents_manager:
            print("⚠️  无代理可用，添加最终标记")
            return f"{story} [已完成最终检查]"

        print("\n" + "="*60)
        print("🎯 第四阶段：最终检查")
        print("="*60)

        editor = self.agents_manager.get_agent("editor")
        if not editor:
            return f"{story} [未找到编辑，无修改]"

        final_check_task = f"""
对以下故事进行最终质量检查：

{story[:5000]}

请从发布角度进行全面评估，重点关注：
1. 整体质量与完成度
2. 是否适合网络文学平台
3. 读者阅读体验
4. 出版/发布准备度

返回JSON格式的最终评估报告。
"""

        check_result = await editor.run(task=final_check_task)
        check_content = extract_content(check_result.messages)

        self.conversation_manager.add_conversation("phase4_final_check", check_content)

        # Extract check results
        check_results = self._extract_json(check_content)
        overall_score = check_results.get("final_score", "N/A") if check_results else "N/A"

        print(f"✅ 最终检查完成，评分: {overall_score}")

        return f"{story} [最终版，评分: {overall_score}]"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text with error handling"""
        json_objects = extract_all_json(text)
        return json_objects[0] if json_objects else {}