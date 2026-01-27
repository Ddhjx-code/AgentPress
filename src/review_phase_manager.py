import asyncio
from typing import Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.agent_activity_manager import AgentActivityManager
from src.creation_context_builder import CreationContextBuilder
from config import CREATION_CONFIG, MAX_REVISION_ROUNDS, SCORE_THRESHOLD
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary


class ReviewPhaseManager:
    """专门处理评审和修订阶段的类，从NovelWritingPhases中分离出来"""

    def __init__(self, conversation_manager: ConversationManager,
                 agent_activity_manager: AgentActivityManager,
                 agent_manager: AgentManager):
        self.conversation_manager = conversation_manager
        self.agent_activity_manager = agent_activity_manager
        self.agent_manager = agent_manager
        self.context_builder = CreationContextBuilder()

    async def execute_review_phase(self, story: str) -> str:
        """执行评审和修订阶段的完整流程"""
        if not self.agent_manager:
            print("⚠️  无代理可用，跳过审查阶段")
            return story

        print("\n" + "="*60)
        print("🔄 第三阶段：多轮评审和修订")
        print("="*60)

        # 通知进度回调开始评审阶段
        if hasattr(self, 'progress_callback') and self.progress_callback:
            await self.progress_callback("质量检查", "总体进度", "开始多代理并行评审流程...")

        current_story = story
        version_num = 2

        # 限制评审轮数以控制token消耗，只进行一轮评审
        max_review_rounds = min(MAX_REVISION_ROUNDS, 1)
        for round_num in range(max_review_rounds):
            print(f"\n--- 第 {round_num + 1} 轮评审 ---")

            if hasattr(self, 'progress_callback') and self.progress_callback:
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
            if hasattr(self, 'progress_callback') and self.progress_callback:
                await self.progress_callback(
                    "质量检查",
                    f"轮次 {round_num + 1} 完成",
                    f"获得反馈并计算平均分: {avg_score:.1f}/100",
                    (round_num + 0.5) / max_review_rounds if max_review_rounds > 0 else 1.0
                )

            # Check if story passes quality threshold
            if avg_score >= SCORE_THRESHOLD:
                print(f"\n✅ 第 {round_num + 1} 轮评审通过！")
                if hasattr(self, 'progress_callback') and self.progress_callback:
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
            if hasattr(self, 'progress_callback') and self.progress_callback:
                await self.progress_callback(
                    "质量检查",
                    "评审完成",
                    f"跳过修订阶段以控制长度和成本",
                    1.0
                )
            break  # 即使只有1轮，也要确保不会进行完整修订

        # 创建会议纪要信息
        review_participants = [agent[0] for agent in agents_to_review if self.agent_manager.get_agent(agent[0])]
        review_summary = f"完成第{len(range(max_review_rounds))}轮评审，参与代理: {', '.join([agent[0] for agent in agents_to_review if self.agent_manager.get_agent(agent[0])])}，平均得分: {avg_score:.1f}/100"

        # 检查并添加会议纪要
        if hasattr(self.conversation_manager, 'add_meeting_minutes'):
            self.conversation_manager.add_meeting_minutes(
                stage="review_phase",
                participants=review_participants,
                summary=review_summary,
                decisions=[
                    f"平均得分: {avg_score:.1f}/100" if avg_score > 0 else "评分失败",
                    f"代理参与: {len(review_participants)} 个代理完成评审",
                    f"总轮次: {len(range(max_review_rounds))} 轮审查",
                    f"总体评价: {'通过' if avg_score >= SCORE_THRESHOLD else '未通过阈值'}"
                ],
                turn_count=len(agents_to_review) * len(range(max_review_rounds)),
            )

            # 实时保存阶段性报告
            if hasattr(self.conversation_manager, 'save_interim_report'):
                self.conversation_manager.save_interim_report("review_phase")

        # 保存代理工作日志
        try:
            log_file, summary_file, web_file = self.agent_activity_manager.save_agent_work_log()
            print(f"📁 代理工作日志已保存: {log_file}")
            print(f"📋 代理工作摘要已保存: {summary_file}")
            print(f"🌐 Web可视化数据已保存: {web_file}")
        except Exception as e:
            print(f"⚠️  保存代理工作日志时出错: {e}")

        return current_story

    async def _get_multifaceted_feedback_parallel(self, story: str) -> Dict[str, Any]:
        """使用并行处理获得多个专业代理的反馈（使用asyncio.gather）"""
        if not self.agent_manager:
            return {"default": {"score": 75, "comments": "No agents available", "suggestions": ["Improve character development"]}}

        agents_to_review = [
            ("fact_checker", "事实与逻辑检查"),
            ("dialogue_specialist", "对话质量评估"),
            ("editor", "整体质量把控"),
            ("write_enviroment_specialist", "环境描写优化"),
            ("write_rate_specialist", "叙事节奏调整")
        ]

        print(f"   🤖 开始并行评审流程 (共 {len(agents_to_review)} 个专业代理)...")

        # Create async tasks for all the agents to run them in parallel
        tasks = []
        agent_instances = []

        for agent_name, description in agents_to_review:
            agent = self.agent_manager.get_agent(agent_name)
            if agent:
                agent_instances.append((agent, agent_name, description))
                task = self._run_single_review(agent, agent_name, story)
                tasks.append(task)

        # Execute all review tasks in parallel
        print(f"   ⏳ 并行处理评审任务中...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        feedback = {}
        for i, (agent, agent_name, description) in enumerate(agent_instances):
            try:
                # Check if result had an exception
                if i < len(results) and isinstance(results[i], Exception):
                    print(f"   ❌ {description}({agent_name}) 评审出错: {results[i]}")
                    feedback[agent_name] = {"score": 60, "error": str(results[i])}
                else:
                    result = results[i]
                    review_data = self._extract_json(result)
                    feedback[agent_name] = result or {
                        "score": 75,
                        "comments": f"Default {agent_name} review",
                        "suggestions": ["General improvement"]
                    }
                    print(f"   ✅ {description}完成")
            except Exception as e:
                print(f"   ❌ {description}({agent_name}) 评审出错: {e}")
                feedback[agent_name] = {"score": 60, "error": str(e)}

        print(f"   📋 所有评审任务完成！")
        return feedback

    async def _run_single_review(self, agent, agent_name: str, story: str):
        """运行单个评审任务"""
        task = self.context_builder.build_review_task_context(story, agent_name)
        review_result = await agent.run(task=task)
        review_content = extract_content(review_result.messages)

        # 记录评审代理的活动
        self.agent_activity_manager.log_agent_activity(
            phase="review_phase",
            agent_name=agent_name,
            task=task,
            result=review_content,
            metadata={
                "character_count": len(story),
                "agent_type": agent_name
            }
        )

        return review_content

    async def _get_multifaceted_feedback(self, story: str) -> Dict[str, Any]:
        """获得多个专业代理的反馈 - 单独运行版本"""
        if not self.agent_manager:
            return {"default": {"score": 75, "comments": "No agents available", "suggestions": ["Improve character development"]}}

        feedback = {}

        agents_to_review = [
            ("fact_checker", "事实与逻辑检查"),
            ("dialogue_specialist", "对话质量评估"),
            ("editor", "整体质量把控"),
            ("write_enviroment_specialist", "环境描写优化"),
            ("write_rate_specialist", "叙事节奏调整")
        ]

        for agent_name, description in agents_to_review:
            agent = self.agent_manager.get_agent(agent_name)
            if agent:
                print(f"   📝 {description}中...")
                try:
                    review_task = self.context_builder.build_review_task_context(story, agent_name)
                    review_result = await agent.run(task=review_task)
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

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """提取文本中的JSON并处理错误"""
        json_objects = extract_all_json(text)
        return json_objects[0] if json_objects else []