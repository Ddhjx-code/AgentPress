# phases.py
import json
import asyncio
from typing import Dict, Any, List
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary
from agents_manager import AgentsManager
from conversation_manager import ConversationManager
from config import GROUPCHAT_CONFIGS, SCORE_THRESHOLD, MAX_REVISION_ROUNDS,CREATION_CONFIG


class DocumentationManager:
    """故事档案管理（维护一致性）"""
    
    def __init__(self, doc_agent: AssistantAgent):
        self.doc_agent = doc_agent
        self.characters = {}      # 人物档案
        self.timeline = []        # 时间线
        self.world_rules = {}     # 世界观规则
        self.foreshadowing = []   # 伏笔清单
        self.chapters_summary = []  # 章节摘要
    
    async def extract_chapter_info(self, chapter: str, chapter_num: int) -> Dict[str, Any]:
        """从章节提取信息并更新档案"""
        
        task = f"""
请从以下第 {chapter_num} 章的内容中提取信息，并按照你的系统提示词中要求的 JSON 格式返回。

【第 {chapter_num} 章内容】
{chapter}
        """
        
        result = await self.doc_agent.run(task=task)
        content = extract_content(result.messages)
        data = self._extract_json(content)
        
        if data:
            self._update_records(data)
        
        return data
    
    async def check_consistency(self, chapter: str, chapter_num: int) -> Dict[str, Any]:
        """检查新章节是否与档案一致"""
        
        current_summary = self._get_summary()
        
        task = f"""
请检查以下新章节是否与已建立的档案一致。

【当前档案摘要】
{current_summary}

【第 {chapter_num} 章新内容】
{chapter[:2000]}
        """
        
        result = await self.doc_agent.run(task=task)
        content = extract_content(result.messages)
        data = self._extract_json(content)
        
        return data or {"is_consistent": True, "overall_score": 100}
    
    def get_summary(self) -> str:
        """获取档案摘要供 Writer 查看"""
        
        summary = f"""
【已有人物】
"""
        for name, info in self.characters.items():
            summary += f"- {name}: {info.get('personality', '')}\n"
        
        summary += f"\n【时间线进度】\n"
        if self.chapters_summary:
            summary += f"已创作 {len(self.chapters_summary)} 章\n"
            summary += f"总计约 {sum(s.get('word_count', 0) for s in self.chapters_summary)} 字\n"
        
        summary += f"\n【已建立的规则】\n"
        for rule_name, rule_desc in self.world_rules.items():
            summary += f"- {rule_name}: {rule_desc}\n"
        
        summary += f"\n【待回收伏笔】\n"
        pending = [f for f in self.foreshadowing if not f.get('resolved')]
        summary += f"共 {len(pending)} 个\n"
        
        return summary
    
    def _update_records(self, chapter_data: Dict):
        """更新档案记录"""
        
        # 更新人物
        if "characters" in chapter_data:
            self.characters.update(chapter_data["characters"])
        
        # 更新世界观规则
        if "world_rules" in chapter_data:
            new_rules = chapter_data["world_rules"]
            if isinstance(new_rules, dict):
                self.world_rules.update(new_rules)
        
        # 更新伏笔
        if "foreshadowing" in chapter_data:
            foreshadowing = chapter_data["foreshadowing"]
            if isinstance(foreshadowing, dict):
                self.foreshadowing.extend(foreshadowing.get("new", []))
                # 标记已回收的伏笔
                for resolved in foreshadowing.get("resolved", []):
                    for fs in self.foreshadowing:
                        if fs.get("content") == resolved.get("content"):
                            fs["resolved"] = True
        
        # 保存章节摘要
        if "chapter_summary" in chapter_data:
            self.chapters_summary.append({
                "chapter_num": chapter_data.get("chapter_num"),
                "summary": chapter_data["chapter_summary"]
            })
    
    def _get_summary(self) -> str:
        """内部使用的摘要"""
        return self.get_summary()
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        json_objects = extract_all_json(text)
        return json_objects[0] if json_objects else {}
    

class NovelWritingPhases:
    """网络小说创作工作流的各个阶段"""
    
    def __init__(self, agents_manager: AgentsManager, conversation_manager: ConversationManager):
        self.agents = agents_manager
        self.conversation = conversation_manager
        self.documentation = None

    async def _intermediate_review(self, chapters: List[str], checkpoint_num: int,
                                start_chapter_num: int) -> Dict[str, Any]:
        """中期评审：评审多个章节的整体质量"""
        
        end_chapter_num = start_chapter_num + len(chapters) - 1
        
        # 合并要评审的章节
        merged_text = "\n\n".join([
            f"【第 {start_chapter_num + i} 章】\n{chapter}"
            for i, chapter in enumerate(chapters)
        ])
        
        # 用 Editor 进行整体评审
        editor = self.agents.get_agent("editor")
        
        # ← 简化！只说任务，不说格式要求
        task = f"""
    请对以下故事第 {start_chapter_num}-{end_chapter_num} 章进行中期评审。

    【故事内容】
    {merged_text[:5000]}

    【任务】
    这是一个中期评审任务，请按照你的系统提示词中的中期评审格式返回结果。
        """
        
        result = await editor.run(task=task)
        content = extract_content(result.messages)
        review_data = self._extract_json_single(content)
        
        return review_data

    
    async def phase1_research_and_planning(self, novel_concept: str) -> Dict[str, Any]:
        """第一阶段：创意研究和规划"""
        print("\n" + "="*60)
        print("📚 第一阶段：创意研究和规划")
        print("="*60)
        
        config = GROUPCHAT_CONFIGS["research_phase"]
        agent_list = self.agents.get_agents(config["agents"])
        
        print(f"\n🔧 GroupChat 配置:")
        print(f"   Agents: {[agent.name for agent in agent_list]}")
        print(f"   Max turns: {config['max_turns']}")
        
        group_chat = RoundRobinGroupChat(
            participants=agent_list,
            max_turns=config["max_turns"]
        )
        
        task_message = f"""
    你们是一个创意团队，需要为以下创意进行研究和规划：

    【创意需求】
    {novel_concept}

    【任务分配】
    1. mythologist（神话学家）：分析背景和文献，返回JSON
    2. writer（作家）：设计大纲和情节，返回JSON

    请互相参考意见，各自输出最终意见。
        """
        
        print(f"\n📤 发送初始 task...")
        print(f"   Task 长度: {len(task_message)} 字符")
        
        result = await group_chat.run(task=task_message)
        
        print(f"\n📥 GroupChat 返回结果:")
        print(f"   Messages 数量: {len(result.messages)}")
        
        # ========== 关键改进：保存完整对话 ==========
        agent_messages = []
        for i, msg in enumerate(result.messages):
            msg_source = getattr(msg, 'source', 'unknown')
            msg_content = getattr(msg, 'content', '')
            
            print(f"\n   --- Message {i} ---")
            print(f"   Source: {msg_source}")
            print(f"   Length: {len(msg_content)} 字符")
            
            # 只保存非user的消息
            if msg_source != 'user':
                agent_messages.append({
                    "turn": i,
                    "agent": msg_source,
                    "content": msg_content
                })
        
        # 拼接完整对话
        conversation_text = "\n\n".join([
            f"【{item['agent'].upper()}】(Turn {item['turn']}):\n{item['content']}"
            for item in agent_messages
        ])
        
        print(f"\n✅ 收集了 {len(agent_messages)} 条Agent消息")
        print(f"   完整对话长度: {len(conversation_text)} 字符")
        
        self.conversation.add_conversation("phase1_research", conversation_text)
        
        # 从所有消息中提取数据
        research_data = self._extract_research_from_all_messages(result.messages)
        
        print(f"   提取字段: {list(research_data.keys())}")
        
        return research_data

    
    async def _phase1_sequential(self, novel_concept: str) -> Dict[str, Any]:
        """第一阶段的备用顺序版本"""
        print("⚠️  使用顺序调用模式")
        
        # 先让神话学家分析
        mythologist = self.agents.get_agent("mythologist")
        myth_task = f"分析这个网络小说创意的世界观设定：{novel_concept}\n返回JSON格式的分析结果。"
        
        myth_result = await mythologist.run(task=myth_task)
        myth_content = extract_content(myth_result.messages)
        
        # 再让作家设计大纲
        writer = self.agents.get_agent("writer")
        writer_task = f"""
根据以下背景分析设计故事大纲：

{myth_content}

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
        
        conversation = myth_content + "\n---\n" + writer_content
        self.conversation.add_conversation("phase1_research_sequential", conversation)
        
        print(f"✅ 研究阶段完成（顺序模式）")
        
        research_data = self._extract_research_data(conversation)
        return research_data
    
    async def phase2_creation(self, research_data: Dict[str, Any]) -> str:
        """第二阶段：初稿创作（单章或多章）"""
        
        num_chapters = CREATION_CONFIG.get("num_chapters", 1)
        
        if num_chapters == 1:
            # 原有的单章模式
            return await self._phase2_single_chapter(research_data)
        else:
            # 新的分章节模式
            return await self._phase2_multiple_chapters(research_data, num_chapters)
    
    async def _phase2_single_chapter(self, research_data: Dict[str, Any]) -> str:
        """创作单章（原有逻辑）"""
        print("\n" + "="*60)
        print("✍️  第二阶段：初稿创作")
        print("="*60)
        
        writer = self.agents.get_agent("writer")
        
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
        
        self.conversation.add_story_version(1, story)
        print(f"✅ 初稿完成 ({len(story)} 字符)")
        
        return story
    
    async def _phase2_multiple_chapters(self, research_data: Dict[str, Any], num_chapters: int) -> str:
        """分章节创作（新模式）"""
        print("\n" + "="*60)
        print(f"✍️  第二阶段：分章节创作（{num_chapters} 章）")
        print("="*60)
        
        # 初始化档案员
        doc_agent = self.agents.get_agent("documentation_specialist")
        if not doc_agent:
            print("⚠️  档案员不可用，继续创作但无法维护一致性")
        
        
        if doc_agent:
            self.documentation = DocumentationManager(doc_agent)
        
        writer = self.agents.get_agent("writer")
        chapters = []
        checkpoint_interval = 3  # 每 3 章做一次中期评审
        checkpoint_num = 1
        
        target_length = CREATION_CONFIG.get("target_length_per_chapter", 2000)
        
        for chapter_num in range(1, num_chapters + 1):
            print(f"\n--- 第 {chapter_num}/{num_chapters} 章 ---")
            
            # 1. 准备创作上下文
            context = self._prepare_chapter_context(
                chapter_num=chapter_num,
                research_data=research_data,
                previous_chapters=chapters,
                target_length=target_length
            )
            
            # 2. Writer 创作
            print(f"   ✍️  创作中...")
            chapter_result = await writer.run(task=context)
            chapter = extract_content(chapter_result.messages)
            chapters.append(chapter)
            
            print(f"   ✅ 完成（{len(chapter)} 字）")
            
            # 3. 档案员提取信息
            if self.documentation:
                print(f"   📋 更新档案...")
                chapter_info = await self.documentation.extract_chapter_info(chapter, chapter_num)
                
                # 4. 档案员检查一致性
                print(f"   🔍 检查一致性...")
                consistency = await self.documentation.check_consistency(chapter, chapter_num)

                self.conversation.add_documentation(
                    chapter_num=chapter_num,
                    extraction_info=chapter_info,
                    consistency_check=consistency
                )
                
                score = consistency.get("overall_score", 100)
                
                if score < 90:
                    print(f"   ⚠️  一致性评分 {score:.0f}，修订中...")
                    
                    # 让 Writer 修改
                    fix_context = self._prepare_fix_context(
                        chapter=chapter,
                        consistency_issues=consistency.get("issues", []),
                        documentation=self.documentation.get_summary()
                    )
                    
                    fix_result = await writer.run(task=fix_context)
                    chapter = extract_content(fix_result.messages)
                    chapters[-1] = chapter
                    
                    # 重新更新档案
                    chapter_info = await self.documentation.extract_chapter_info(chapter, chapter_num)
                
                print(f"   一致性评分: {score:.0f}")
            
            if chapter_num % checkpoint_interval == 0 or chapter_num == num_chapters:
                # 需要做中期评审
                print(f"\n🔍 执行中期评审（Checkpoint {checkpoint_num}）...")
                
                start_chapter = chapter_num - checkpoint_interval + 1
                review_chapters = chapters[-checkpoint_interval:]
                
                intermediate_review = await self._intermediate_review(
                    review_chapters,
                    checkpoint_num=checkpoint_num,
                    start_chapter_num=start_chapter
                )
                
                review_score = intermediate_review.get("overall_quality_score", 0)
                print(f"   中期评审评分: {review_score}/100")
                print(f"   问题数: {len(intermediate_review.get('issues', []))}")
                
                # 保存中期评审结果
                self.conversation.add_conversation(
                    f"intermediate_review_checkpoint_{checkpoint_num}",
                    json.dumps(intermediate_review, ensure_ascii=False, indent=2)
                )
                
                # 如果评分过低，可以决定是否继续
                if review_score < 70:
                    print(f"\n⚠️  评分较低 ({review_score}/100)，建议修改策略")
                    # 可选：暂停并要求调整
                    # 或继续但记录警告
                
                checkpoint_num += 1
            
            self.conversation.add_story_version(chapter_num, chapter)
        
        # 合并所有章节
        full_story = "\n\n".join(chapters)
        
        print(f"\n{'='*60}")
        print(f"✅ 创作完成！共 {len(chapters)} 章，{len(full_story)} 字")
        
        return full_story
    
    def _prepare_chapter_context(self, chapter_num: int, research_data: Dict, 
                                previous_chapters: List[str], target_length: int) -> str:
        """准备某一章的创作上下文"""
        
        context = f"""
根据以下信息创作第 {chapter_num} 章：

【故事背景】
{json.dumps(research_data, ensure_ascii=False, indent=2)[:1000]}

【前面的故事】
"""
        
        if previous_chapters:
            # 只保留最后一章的摘要，避免 Token 过多
            context += f"（前 {len(previous_chapters)} 章已完成，最后一章摘要如下）\n"
            context += previous_chapters[-1][:1000] + "...\n"
        else:
            context += "（这是第一章，请精彩开局）\n"
        
        context += f"""
【已有档案】
"""
        
        if self.documentation:
            context += self.documentation.get_summary()
        
        context += f"""

【创作要求】
- 字数：约 {target_length} 字
- 风格：网络文学风格，引人入胜
- 要求：推进情节，与前面内容一致
- 结尾：留下悬念，吸引继续阅读
- 直接输出故事文本（不要JSON）
        """
        
        return context
    

    def _prepare_fix_context(self, chapter: str, consistency_issues: List[Dict], 
                            documentation: str) -> str:
        """准备修改时的上下文"""
        
        task = f"""
    根据以下一致性问题修改章节：

    【一致性问题】
    {json.dumps(consistency_issues, ensure_ascii=False, indent=2)}

    【当前档案】
    {documentation}

    【原章节】
    {chapter}

    请修改上述问题，直接输出修改后的完整章节文本。
        """
        
        return task

    async def phase3_review_and_refinement(self, story: str, research_data: Dict[str, Any]) -> str:
        """第三阶段：多轮评审和修订"""
        print("\n" + "="*60)
        print("🔄 第三阶段：多轮评审和修订")
        print("="*60)
        
        current_story = story
        version_num = 2
        
        for round_num in range(MAX_REVISION_ROUNDS):
            print(f"\n--- 第 {round_num + 1} 轮评审 ---")
            
            config = GROUPCHAT_CONFIGS["review_phase"]
            agent_list = self.agents.get_agents(config["agents"])
            
            if not agent_list:
                print("⚠️  没有可用的评审Agent")
                break
            
            # 使用顺序评审（因为GroupChat API可能有问题）
            feedback = await self._sequential_review(current_story)
            
            avg_score = calculate_average_score(feedback)
            
            self.conversation.add_feedback(round_num + 1, feedback)
            
            print(f"   平均评分: {avg_score:.1f}/100")
            print(f"   反馈摘要:")
            print(format_feedback_summary(feedback))
            
            # 检查是否达标
            if avg_score >= SCORE_THRESHOLD:
                print(f"\n✅ 第 {round_num + 1} 轮评审通过！")
                break
            
            # 最后一轮不再修订
            if round_num >= MAX_REVISION_ROUNDS - 1:
                print(f"\n⚠️  已达到最大修订轮数，结束修订")
                break
            
            # 执行修订
            print(f"\n🔧 进行修订（第 {version_num} 版本）...")
            
            revision_task = f"""
根据以下评审意见修改故事：

---原故事---
{current_story}
---原故事结束---

---评审意见---
{json.dumps(feedback, ensure_ascii=False, indent=2)}
---意见结束---

请直接输出修改后的完整故事，不要包含JSON或其他格式。
修改要求：
- 保留原故事的核心情节
- 根据评审意见进行针对性修改
- 保持网络文学的风格
- 长度保持在2000-3000字左右
            """
            
            writer = self.agents.get_agent("writer")
            revision_result = await writer.run(task=revision_task)
            current_story = extract_content(revision_result.messages)
            
            self.conversation.add_story_version(version_num, current_story, 
                                              {"round": round_num + 1, "avg_score": avg_score})
            
            print(f"✅ 修订完成 ({len(current_story)} 字符)")
            version_num += 1
        
        return current_story
    
    async def _sequential_review(self, story: str) -> Dict[str, Any]:
        """按顺序进行评审"""
        feedback = {}
        
        print(f"\n📋 启动评审流程...")
        print(f"   评审故事长度: {len(story)} 字符")
        
        # 事实核查
        fact_checker = self.agents.get_agent("fact_checker")
        if fact_checker:
            print(f"\n   [1/3] 事实核查员评审中...")
            fact_task = f"""
    请评审以下故事：

    【故事内容】
    {story[:1500]}
            """
            try:
                fact_result = await fact_checker.run(task=fact_task)
                fact_content = extract_content(fact_result.messages)
                feedback["fact_checker"] = self._extract_json_single(fact_content)
                if "score" not in feedback["fact_checker"]:
                    feedback["fact_checker"]["score"] = 50
                print(f"      ✅ 完成，评分: {feedback['fact_checker'].get('score', 'N/A')}")
            except Exception as e:
                print(f"      ❌ 错误: {e}")
                feedback["fact_checker"] = {"score": 50, "issues": ["评审出错"], "suggestions": []}
        
        # 对话评审
        dialogue = self.agents.get_agent("dialogue_specialist")
        if dialogue:
            print(f"\n   [2/3] 对话专家评审中...")
            dialogue_task = f"""
    请评审以下故事的对话质量：

    【故事内容】
    {story[:1500]}
            """
            try:
                dialogue_result = await dialogue.run(task=dialogue_task)
                dialogue_content = extract_content(dialogue_result.messages)
                feedback["dialogue_specialist"] = self._extract_json_single(dialogue_content)
                if "score" not in feedback["dialogue_specialist"]:
                    feedback["dialogue_specialist"]["score"] = 50
                print(f"      ✅ 完成，评分: {feedback['dialogue_specialist'].get('score', 'N/A')}")
            except Exception as e:
                print(f"      ❌ 错误: {e}")
                feedback["dialogue_specialist"] = {"score": 50, "issues": ["评审出错"], "suggestions": []}
        
        # 文学编辑评审
        editor = self.agents.get_agent("editor")
        if editor:
            print(f"\n   [3/3] 文学编辑评审中...")
            editor_task = f"""
    请评审以下故事的文学质量：

    【故事内容】
    {story[:1500]}
            """
            try:
                editor_result = await editor.run(task=editor_task)
                editor_content = extract_content(editor_result.messages)
                feedback["editor"] = self._extract_json_single(editor_content)
                if "score" not in feedback["editor"]:
                    feedback["editor"]["score"] = 50
                print(f"      ✅ 完成，评分: {feedback['editor'].get('score', 'N/A')}")
            except Exception as e:
                print(f"      ❌ 错误: {e}")
                feedback["editor"] = {"score": 50, "issues": ["评审出错"], "suggestions": []}
        
        return feedback


    
    async def phase4_final_check(self, story: str) -> Dict[str, Any]:
        """第四阶段：最终发布检查"""
        print("\n" + "="*60)
        print("🎯 第四阶段：最终发布检查")
        print("="*60)
        
        editor = self.agents.get_agent("editor")
        
        final_check_task = f"""
请对以下故事进行最后的发布前检查：

---故事---
{story}
---故事结束---

这是一个最终检查任务，请按照你的系统提示词中的格式返回结果。
"""
        
        check_result = await editor.run(task=final_check_task)
        check_content = extract_content(check_result.messages)
        
        self.conversation.add_conversation("phase4_final_check", check_content)
        
        check_data = self._extract_json_single(check_content)
        
        print(f"✅ 最终检查完成")
        if check_data:
            print(f"   发布就绪: {check_data.get('ready_for_publication', False)}")
            print(f"   最终评分: {check_data.get('final_score', 'N/A')}/100")
        
        return check_data
    
    def _extract_research_data(self, conversation: str) -> Dict[str, Any]:
        """从对话中提取研究数据"""
        json_objects = extract_all_json(conversation)
        
        combined_data = {
            "background": "基于AI对话生成的故事背景",
            "outline": "故事大纲",
            "character_profiles": [],
            "world_setting": "",
            "key_conflicts": []
        }
        
        for json_obj in json_objects:
            if isinstance(json_obj, dict):
                combined_data.update(json_obj)
        
        return combined_data
    
    def _extract_json_single(self, text: str) -> Dict[str, Any]:
        """从文本中提取单个JSON对象"""
        json_objects = extract_all_json(text)
        if json_objects:
            return json_objects[0]
        
        # 如果没有找到JSON，返回默认评分
        return {
            "score": 50,
            "issues": ["无法解析反馈"],
            "suggestions": ["请重新评审"]
        }
    

    def _extract_research_from_all_messages(self, messages) -> Dict[str, Any]:
        """从所有消息中综合提取研究数据（不只是最后一条）"""
        all_json_objects = []
        
        # 遍历所有消息而不是只取最后一条
        for msg in messages:
            content = extract_content([msg])
            json_objects = extract_all_json(content)
            all_json_objects.extend(json_objects)
        
        # 合并所有JSON对象
        combined_data = {
            "background": "基于AI对话生成的故事背景",
            "outline": "故事大纲",
            "character_profiles": [],
            "world_setting": "",
            "key_conflicts": []
        }
        
        for json_obj in all_json_objects:
            if isinstance(json_obj, dict):
                combined_data.update(json_obj)
        
        return combined_data
    
    async def run_full_pipeline(self, novel_concept: str) -> Dict[str, Any]:
        """运行完整的创作流程"""
        print("\n🚀 启动网络小说创作流程\n")
        
        try:
            # 第一阶段：研究和规划
            research_data = await self.phase1_research_and_planning(novel_concept)
            
            # 第二阶段：初稿创作
            story = await self.phase2_creation(research_data)
            
            # 第三阶段：评审和修订
            refined_story = await self.phase3_review_and_refinement(story, research_data)
            
            # 第四阶段：最终检查
            final_check = await self.phase4_final_check(refined_story)
            
            # 组织最终输出
            final_output = {
                "novel_concept": novel_concept,
                "research_data": research_data,
                "final_story": refined_story,
                "final_check": final_check,
                "summary": self.conversation.get_summary()
            }
            
            return final_output
        
        except Exception as e:
            print(f"\n❌ 流程执行出错: {e}")
            import traceback
            traceback.print_exc()
            raise
