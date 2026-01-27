from typing import Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.agent_activity_manager import AgentActivityManager
from utils import extract_content, extract_all_json


class FinalCheckManager:
    """专门处理最终检查阶段的类，从NovelWritingPhases中分离出来"""

    def __init__(self, conversation_manager: ConversationManager,
                 agent_activity_manager: AgentActivityManager,
                 agent_manager: AgentManager):
        self.conversation_manager = conversation_manager
        self.agent_activity_manager = agent_activity_manager
        self.agent_manager = agent_manager

    async def execute_final_check(self, story: str) -> str:
        """执行最终检查阶段的完整工作流"""
        if not self.agent_manager:
            print("⚠️  无代理可用，添加最终标记")
            return f"{story} [已完成最终检查]"

        print("\n" + "="*60)
        print("🎯 第四阶段：最终检查")
        print("="*60)

        editor = self.agent_manager.get_agent("editor")
        if not editor:
            return f"{story} [未找到编辑，无修改]"

        final_check_task = """
对以下故事进行最终质量检查：

{story_content}

请从发布角度进行全面评估，重点关注：
1. 整体质量与完成度
2. 是否适合网络文学平台
3. 读者阅读体验
4. 出版/发布准备度

返回JSON格式的最终评估报告。
""".replace("{story_content}", story[:5000])

        check_result = await editor.run(task=final_check_task)
        check_content = extract_content(check_result.messages)

        self.conversation_manager.add_conversation("phase4_final_check", check_content)

        # Extract check results
        check_results = self._extract_json(check_content)
        overall_score = check_results.get("final_score", "N/A") if check_results else "N/A"

        print(f"✅ 最终检查完成，评分: {overall_score}")

        # 记录编辑代理的最终检查活动
        self.agent_activity_manager.log_agent_activity(
            phase="final_check_phase",
            agent_name="editor",
            task=final_check_task,
            result=check_content,
            metadata={"final_score": overall_score}
        )

        # 添加会议纪要功能
        if hasattr(self.conversation_manager, 'add_meeting_minutes'):
            self.conversation_manager.add_meeting_minutes(
                stage="final_check",
                participants=["editor"],
                summary=f"editor完成最终质量检查，评分为{overall_score}",
                decisions=[
                    f"最终评分: {overall_score}",
                    f"完成状态: 故事已通过最终检查",
                    f"准备度: 适合发布",
                    f"质量评估: 已达到发布标准"
                ],
                turn_count=1  # editor代理的检查次数
            )

            # 实时保存阶段性报告
            if hasattr(self.conversation_manager, 'save_interim_report'):
                self.conversation_manager.save_interim_report("final_check")

        # 保存最终的代理工作日志
        try:
            log_file, summary_file, web_file = self.agent_activity_manager.save_agent_work_log()
            print(f"📁 最终代理工作日志已保存: {log_file}")
            print(f"📋 最终代理工作摘要已保存: {summary_file}")
            print(f"🌐 Web可视化数据已保存: {web_file}")
        except Exception as e:
            print(f"⚠️  保存最终代理工作日志时出错: {e}")

        return f"{story} [最终版，评分: {overall_score}]"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """提取文本中的JSON并处理错误"""
        json_objects = extract_all_json(text)
        return json_objects[0] if json_objects else []