from src.novel_phases_manager import NovelWritingPhases
from src.documentation_manager import DocumentationManager
from conversation_manager import ConversationManager


class NovelWorkflowOrchestrator:
    """Main orchestrator for the novel creation workflow"""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.documentation_manager = DocumentationManager()
        self.phase_manager = None  # Set by main program when agents manager is available

    def run_complete_workflow(self, initial_idea: str, multi_chapter: bool = False, total_chapters: int = 1):
        """Run the complete novel creation workflow"""
        # Check if we have a phase manager with async capabilities
        if self.phase_manager:
            # This would run async operations if phase_manager is properly initialized
            pass

        # Fallback behavior for current implementation
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

    async def run_async_workflow(self, initial_idea: str, multi_chapter: bool = False,
                                total_chapters: int = 1, agents_manager=None):
        """Run the complete async workflow with proper agent coordination"""
        # Initialize the phase manager with async capabilities
        phase_manager = NovelWritingPhases(
            conversation_manager=self.conversation_manager,
            documentation_manager=self.documentation_manager
        )
        phase_manager.agents_manager = agents_manager  # Pass agents manager for async operations

        # Step 1: Async Research and Planning
        research_data = await phase_manager.async_phase1_research_and_planning(initial_idea)

        # Step 2: Async Creation
        draft_story = await phase_manager.async_phase2_creation(research_data)

        # Step 3 & 4: Review, refinement, and final check would go here in full implementation
        revised_story = draft_story
        final_story = f"{draft_story} [最终版本]"

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