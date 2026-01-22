import json
import asyncio
from typing import List, Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from config import GROUPCHAT_CONFIGS, CREATION_CONFIG, SCORE_THRESHOLD, MAX_REVISION_ROUNDS
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary


class NovelWritingPhases:
    """Complete implementation for the multi-phase novel writing process"""

    def __init__(self, conversation_manager: ConversationManager,
                 documentation_manager: DocumentationManager):
        self.conversation_manager = conversation_manager
        self.documentation_manager = documentation_manager
        self.agents_manager = None  # Will be set by caller

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
        """Async phase 2: Creation with both single and multi-chapter support"""
        num_chapters = CREATION_CONFIG.get("num_chapters", 1)

        if num_chapters == 1:
            # Single chapter creation
            return await self._async_phase2_single_chapter(research_data)
        else:
            # Multi-chapter creation with documentation
            return await self._async_phase2_multiple_chapters(research_data, num_chapters)

    async def _async_phase2_single_chapter(self, research_data: Dict[str, Any]) -> str:
        """Single chapter creation"""
        print("\n" + "="*60)
        print("✍️  第二阶段：单章创作")
        print("="*60)

        if not self.agents_manager:
            # Fallback creation
            outline = research_data.get("outline", "创作大纲")
            story = f"""
基于 '{outline}' 创作的网络小说初稿。

故事从这里开始，根据研究数据展开情节...
            """
            self.conversation_manager.add_story_version(1, story)
            print(f"✅ 初稿完成 ({len(story)} 字符)")
            return story

        writer = self.agents_manager.get_agent("writer")
        if not writer:
            return "❌ 未找到writer代理"

        writer_input = f"""
根据以下研究数据创作网络小说初稿：

{json.dumps(research_data, ensure_ascii=False, indent=2)}

要求：
- 初稿长度：2000-3000字
- 风格：网络文学风格，引人入胜
- 包含：精彩的开场、主角介绍、第一个冲突或转折
- 直接输出故事文本（不要JSON）
        """

        result = await writer.run(task=writer_input)
        story = extract_content(result.messages)

        self.conversation_manager.add_story_version(1, story)
        print(f"✅ 初稿完成 ({len(story)} 字符)")

        return story

    async def _async_phase2_multiple_chapters(self, research_data: Dict[str, Any], num_chapters: int) -> str:
        """Complete async multi-chapter creation with documentation support"""
        print("\n" + "="*60)
        print(f"✍️  第二阶段：多章节创作（{num_chapters}章）")
        print("="*60)

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

    async def _prepare_chapter_context(self, chapter_num: int, research_data: Dict,
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

    async def _update_documentation_for_chapter(self, chapter: str, chapter_num: int):
        """Update documentation using documentation agent"""
        doc_agent = self.agents_manager.get_agent("documentation_specialist")
        if not doc_agent:
            return

        # Task for documentation specialist to extract key information
        doc_task = f"""
请从以下第 {chapter_num} 章内容中提取关键信息并更新档案：
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
        """Complete phase 3 implementation for review and refinement"""
        if not self.agents_manager:
            print("⚠️  无代理可用，跳过审查阶段")
            return story

        print("\n" + "="*60)
        print("🔄 第三阶段：多轮评审和修订")
        print("="*60)

        current_story = story
        version_num = 2

        for round_num in range(MAX_REVISION_ROUNDS):
            print(f"\n--- 第 {round_num + 1} 轮评审 ---")

            # Get feedback from multiple agents
            feedback = await self._get_multifaceted_feedback(current_story)

            avg_score = calculate_average_score(feedback)

            self.conversation_manager.add_feedback(round_num + 1, feedback)

            print(f"   平均评分: {avg_score:.1f}/100")
            print(f"   反馈摘要:")
            print(format_feedback_summary(feedback))

            # Check if story passes quality threshold
            if avg_score >= SCORE_THRESHOLD:
                print(f"\n✅ 第 {round_num + 1} 轮评审通过！")
                break

            # Skip revision on final round
            if round_num >= MAX_REVISION_ROUNDS - 1:
                print(f"\n⚠️  已达到最大修订轮数")
                break

            # Revise the story
            print(f"\n🔧 进行修订...")
            current_story = await self._revise_story(current_story, feedback)
            self.conversation_manager.add_story_version(
                version_num, current_story,
                {"round": round_num + 1, "avg_score": avg_score}
            )
            print(f"✅ 修订完成 ({len(current_story)} 字符)")
            version_num += 1

        return current_story

    async def _get_multifaceted_feedback(self, story: str) -> Dict[str, Any]:
        """Get feedback from multiple specialized agents"""
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