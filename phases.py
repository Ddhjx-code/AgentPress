# phases.py
import json
import asyncio
from typing import Dict, Any, List
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary
from agents_manager import AgentsManager
from conversation_manager import ConversationManager
from config import GROUPCHAT_CONFIGS, SCORE_THRESHOLD, MAX_REVISION_ROUNDS

class NovelWritingPhases:
    """网络小说创作工作流的各个阶段"""
    
    def __init__(self, agents_manager: AgentsManager, conversation_manager: ConversationManager):
        self.agents = agents_manager
        self.conversation = conversation_manager
    
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
        """第二阶段：初稿创作"""
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

检查以下方面（JSON格式输出）：
1. 是否有明显的语法或拼写错误
2. 故事逻辑是否完整
3. 是否适合网络文学平台发布
4. 整体评分

返回格式：
{{
  "ready_for_publication": true/false,
  "final_score": 0-100,
  "grammar_issues": [],
  "logic_issues": [],
  "overall_comments": "总体评价",
  "reader_appeal": "预期吸引力1-10"
}}
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
