from src.novel_phases_manager import NovelWritingPhases
from src.documentation_manager import DocumentationManager
from core.conversation_manager import ConversationManager
from core.workflow_controller import WorkflowController


class NovelWorkflowOrchestrator:
    """Main orchestrator for the novel creation workflow with control features"""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.documentation_manager = DocumentationManager()
        self.workflow_controller = WorkflowController(self.conversation_manager)
        self.phase_manager = None  # Will be set by main program when agents manager is available

    def get_workflow_controller(self):
        """获取工作流控制器以进行交互操作"""
        return self.workflow_controller

    async def run_async_workflow(self, initial_idea: str, multi_chapter: bool = False,
                                total_chapters: int = 1, agents_manager=None, progress_callback=None,
                                enable_manual_control: bool = False):
        """Run the complete async workflow with proper agent coordination"""
        # Initialize the phase manager with async capabilities
        if agents_manager:
            phase_manager = NovelWritingPhases(
                conversation_manager=self.conversation_manager,
                documentation_manager=self.documentation_manager
            )
            phase_manager.agents_manager = agents_manager  # Pass agents manager for async operations
            phase_manager.progress_callback = progress_callback  # Add progress callback

            # Notify about workflow start
            if progress_callback:
                await progress_callback("整体流程", "开始", "初始化研究和规划阶段...")

            # Step 1: Async Research and Planning
            if enable_manual_control:
                research_data = await self.workflow_controller.wrap_async_generation(
                    lambda: phase_manager.async_phase1_research_and_planning(initial_idea),
                    "research", "研究和规划", pause_on_completion=True
                )
            else:
                research_data = await phase_manager.async_phase1_research_and_planning(initial_idea)

            self.workflow_controller.set_result("research_data", research_data)

            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("研究和规划", "完成", "已完成故事研究和规划")

            # Step 2: Async Creation - handles both single/multi chapter modes in phase manager
            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("创作阶段", "开始", "开始故事创作...")

            if enable_manual_control:
                draft_story = await self.workflow_controller.wrap_async_generation(
                    lambda: phase_manager.async_phase2_creation(research_data),
                    "creation", "故事创作", pause_on_completion=True
                )
            else:
                draft_story = await phase_manager.async_phase2_creation(research_data)

            self.workflow_controller.set_result("draft_story", draft_story)

            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("创作阶段", "完成", "故事创作完成")

            # Step 3: Review, refinement
            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("质量检查", "开始", "正在进行多轮评审和修订...")

            if enable_manual_control:
                revised_story = await self.workflow_controller.wrap_async_generation(
                    lambda: phase_manager.phase3_review_refinement(draft_story),
                    "review", "质量检查", pause_on_completion=True
                )
            else:
                revised_story = await phase_manager.phase3_review_refinement(draft_story)

            self.workflow_controller.set_result("revised_story", revised_story)

            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("质量检查", "完成", "评审和修订完成")

            # Step 4: Final check
            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("最终检查", "开始", "正在进行最终质量检查...")

            if enable_manual_control:
                final_story = await self.workflow_controller.wrap_async_generation(
                    lambda: phase_manager.phase4_final_check(revised_story),
                    "final_check", "最终检查", pause_on_completion=True
                )
            else:
                final_story = await phase_manager.phase4_final_check(revised_story)

            self.workflow_controller.set_result("final_story", final_story)

            if progress_callback and not (enable_manual_control and
                                        await self._should_stop_from_controller()):
                await progress_callback("最终检查", "完成", "最终检查完成，流程结束")

            # 会议纪要可视化：输出到控制台和保存到文件
            if hasattr(self.conversation_manager, 'print_meeting_minutes_summary'):
                print("\n" + "="*70)
                print("📋 最终AI代理协作过程总结")
                print("="*70)
                self.conversation_manager.print_meeting_minutes_summary()

                # 自动保存会议纪要到文件
                self.conversation_manager.save_meeting_minutes_to_file()

                # 同时使用ProcessVisualizer进行高级可视化分析
                try:
                    from src.process_visualizer import ProcessVisualizer
                    visualizer = ProcessVisualizer()
                    visualizer.visualize_meeting_minutes(self.conversation_manager, "file")
                    visualizer.visualize_detailed_participants(self.conversation_manager, "file")
                    visualizer.save_complete_process_log(self.conversation_manager)
                except Exception as e:
                    print(f"⚠️  扩展可视化失败: {e}")

            # Return complete results
            results = {
                "initial_idea": initial_idea,
                "research_data": research_data,
                "draft_story": draft_story,
                "revised_story": revised_story,
                "final_story": final_story,
                "conversation_history": self.conversation_manager.get_all_history(),
                "documentation": self.documentation_manager.get_documentation()
            }

            return results
        else:
            # Fallback: simplified workflow if no agents manager provided
            if progress_callback:
                await progress_callback("错误处理", "警告", "没有代理管理器，使用备用流程")
            return await self._run_fallback_workflow(initial_idea, multi_chapter, total_chapters)

    async def _should_stop_from_controller(self) -> bool:
        """检查是否应从控制器停止工作流"""
        return self.workflow_controller.check_interruption()

    async def _run_fallback_workflow(self, initial_idea: str, multi_chapter: bool = False, total_chapters: int = 1):
        """Fallback workflow when no agents manager is provided"""
        # Step 1: Research and Planning
        plan = f"基于 '{initial_idea}' 的研究和规划方案"
        # Step 2: Creation
        draft_story = f"以 {plan} 为指导创作的初稿"
        # Step 3: Review and Refinement
        revised_story = f"经过审查修改的版本：{draft_story}"
        # Step 4: Final Check
        final_story = f"{revised_story} [已完成最终检查]"

        # Return complete results
        results = {
            "initial_idea": initial_idea,
            "research_plan": plan,
            "draft_story": draft_story,
            "revised_story": revised_story,
            "final_story": final_story,
            "conversation_history": self.conversation_manager.get_all_history(),
            "documentation": self.documentation_manager.get_documentation()
        }

        return results

    def get_conversation_manager(self):
        """Get conversation manager for external access"""
        return self.conversation_manager

    def get_documentation_manager(self):
        """Get documentation manager for external access"""
        return self.documentation_manager

    def get_workflow_status(self):
        """获取工作流状态报告"""
        return self.workflow_controller.get_progress_report()