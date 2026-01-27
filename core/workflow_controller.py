"""
工作流控制器 - 提供暂停、介入和控制功能
"""
import asyncio
import time
from typing import Dict, Any, Callable, Optional, List
import re
from .conversation_manager import ConversationManager


class WorkflowController:
    """控制工作流的执行过程，提供暂停、介入和监控功能"""

    def __init__(self, conversation_manager: ConversationManager = None):
        self.conversation_manager = conversation_manager
        self.interruption_handler = None
        self.paused = False
        self.interrupted = False
        self.user_inputs = {}
        self.phase_results = {}  # 存储各阶段的结果

    def set_interruption_handler(self, handler: Callable):
        """设置中断处理器"""
        self.interruption_handler = handler

    async def request_user_input(self, prompt: str, default_value: str = "") -> str:
        """请求用户输入（异步实现，实际在同步环境中的模拟）"""
        print(f"\n❓ 用户输入请求: {prompt}")
        user_value = input(f"   (默认: '{default_value}') > ") or default_value
        return user_value

    async def pause_point(self, stage: str, message: str, show_progress: bool = True,
                         allow_controls: bool = True) -> Dict[str, Any]:
        """
        暂停点 - 在关键节点提供用户介入

        Args:
            stage: 当前阶段
            message: 暂停说明
            show_progress: 是否显示进度
            allow_controls: 是否允许用户控制

        Returns:
            Dict[str, Any]: 控制指令，包含用户选择和状态
        """
        print(f"\n⏸️  {message}")
        print(f"📊 阶段: {stage}")

        # 显示会议纪要摘要（如果可用）
        if self.conversation_manager and hasattr(self.conversation_manager, 'get_meeting_minutes_summary'):
            meeting_minutes = self.conversation_manager.get_meeting_minutes_summary()
            if meeting_minutes:
                print(f"\n📋 代理讨论摘要 (共 {len(meeting_minutes)} 个要点):")
                for i, meeting in enumerate(meeting_minutes[-3:]):  # 显示最近3个要点
                    print(f"   • {meeting['stage']}: {meeting['summary'][:100]}...")
                    if len(meeting['participants']) > 0:
                        print(f"     参与: {', '.join(meeting['participants'][:3])}{'...' if len(meeting['participants']) > 3 else ''}")

        if not allow_controls:
            # 如果不允许控制，稍作停顿后继续
            print("⏳ 自动继续...")
            await asyncio.sleep(0.5)
            return {"action": "continue", "modified_result": None}

        # 提供用户控制选项
        print("\n🔧 可用操作:")
        print("   1. 继续 (continue)")
        print("   2. 修改设定 (modify_config)")
        print("   3. 重新生成当前内容 (regenerate)")
        print("   4. 查看详细讨论过程 (review)")
        print("   5. 退出 (exit)")

        while True:
            choice = input("\n请选择操作 [1-5]: ").strip()

            if choice == "1":
                return {"action": "continue", "modified_result": None}
            elif choice == "2":
                print("🔧 当前不支持在线修改配置")
                return {"action": "continue", "modified_result": None}
            elif choice == "3":
                print("🔄 请求重新生成")
                return {"action": "regenerate", "modified_result": None}
            elif choice == "4":
                # 显示详细会议纪要
                if self.conversation_manager:
                    all_meetings = self.conversation_manager.get_meeting_minutes_summary()
                    if all_meetings:
                        print(f"\n📋 详细讨论过程 (共 {len(all_meetings)} 个要点):")
                        for meeting in reversed(all_meetings[-10:]):  # 显示最近10个要点
                            print(f"   - {meeting['stage']} ({meeting['timestamp']})")
                            print(f"     参与: {', '.join(meeting['participants'])}")
                            print(f"     摘要: {meeting['summary'][:150]}...")
                            if meeting['decisions']:
                                print(f"     决策: {', '.join(meeting['decisions'][:2])}")
                        input("\n按回车键继续... ")
                    else:
                        print("   暂无详细讨论记录")
                continue  # 返回操作选择
            elif choice == "5":
                print("🛑 用户请求退出生成过程")
                return {"action": "exit", "modified_result": None}
            else:
                print("无效选择，请重新输入")

    def check_interruption(self) -> bool:
        """检查是否需要中断"""
        return self.interrupted

    def set_interrupted(self, interrupted: bool):
        """设置中断状态"""
        self.interrupted = interrupted

    def get_progress_report(self) -> Dict[str, Any]:
        """获取当前进度报告"""
        if not self.conversation_manager:
            return {"error": "No conversation manager available"}

        history = self.conversation_manager.get_summary()
        return {
            "total_conversations": history.get("total_conversations", 0),
            "total_versions": history.get("total_versions", 0),
            "total_feedback_rounds": history.get("total_feedback_rounds", 0),
            "total_meeting_minutes": history.get("total_meeting_minutes", 0),
            "meeting_participants": history.get("meeting_participants", []),
            "paused": self.paused,
            "stage_results": self.phase_results
        }

    def set_result(self, stage: str, result: Any):
        """存储阶段结果"""
        self.phase_results[stage] = result

    def get_result(self, stage: str) -> Any:
        """获取阶段结果"""
        return self.phase_results.get(stage)

    def get_phase_summary(self) -> Dict[str, Any]:
        """获取阶段摘要"""
        if not self.conversation_manager or not hasattr(self.conversation_manager, 'get_phase_summaries'):
            return {"error": "No phase summaries available"}

        return {
            "phase_summaries": self.conversation_manager.get_phase_summaries(),
            "total_summaries": len(self.conversation_manager.get_phase_summaries())
        }

    async def wrap_async_generation(self,
                                  generator_func,
                                  stage: str,
                                  stage_name: str,
                                  pause_interval: int = 3,  # 每生成3章暂停一次
                                  pause_on_completion: bool = True) -> Any:
        """
        包装生成函数，添加暂停和控制功能

        Args:
            generator_func: 生成器函数
            stage: 阶段标识
            stage_name: 阶段名称
            pause_interval: 暂停间隔（多少章/步骤后暂停一次）
            pause_on_completion: 完成后是否暂停
        """
        print(f"🚀 开始执行 {stage_name} 阶段...")

        # 在阶段开始时暂停
        pause_result = await self.pause_point(
            stage=stage,
            message=f"{stage_name} 阶段开始",
            show_progress=True,
            allow_controls=True
        )

        if pause_result.get("action") == "exit":
            print(f"🛑 用户在 {stage_name} 开始时选择退出")
            return None

        # 执行生成
        try:
            result = await generator_func()

            # 在阶段完成时暂停
            if pause_on_completion:
                stage_summary = f"{stage_name} 完成，结果类型: {type(result).__name__}"
                if isinstance(result, str):
                    stage_summary += f", 长度: {len(result)} 字符"
                elif isinstance(result, dict):
                    stage_summary += f", 字段数: {len(result)}"

                pause_result = await self.pause_point(
                    stage=f"{stage}_completed",
                    message=stage_summary,
                    show_progress=True,
                    allow_controls=True
                )

                if pause_result.get("action") == "exit":
                    print(f"🛑 用户在 {stage_name} 完成后选择退出")
                    return result

            return result
        except Exception as e:
            print(f"❌ {stage_name} 执行出错: {e}")
            raise