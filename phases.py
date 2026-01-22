from src.novel_phases_manager import NovelWritingPhases
from src.documentation_manager import DocumentationManager
from conversation_manager import ConversationManager


class NovelWorkflowOrchestrator:
    """Main orchestrator for the novel creation workflow"""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.documentation_manager = DocumentationManager()
        self.phase_manager = None  # Will be set by main program when agents manager is available

    async def run_async_workflow(self, initial_idea: str, multi_chapter: bool = False,
                                total_chapters: int = 1, agents_manager=None):
        """Run the complete async workflow with proper agent coordination"""
        # Initialize the phase manager with async capabilities
        if agents_manager:
            phase_manager = NovelWritingPhases(
                conversation_manager=self.conversation_manager,
                documentation_manager=self.documentation_manager
            )
            phase_manager.agents_manager = agents_manager  # Pass agents manager for async operations

            # Step 1: Async Research and Planning
            research_data = await phase_manager.async_phase1_research_and_planning(initial_idea)

            # Step 2: Async Creation - handles both single/multi chapter modes in phase manager
            draft_story = await phase_manager.async_phase2_creation(research_data)

            # Step 3 & 4: Review, refinement, and final check
            revised_story = await phase_manager.phase3_review_refinement(draft_story)
            final_story = await phase_manager.phase4_final_check(revised_story)

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
            return await self._run_fallback_workflow(initial_idea, multi_chapter, total_chapters)

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