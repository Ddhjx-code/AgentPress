from typing import Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from src.agent_activity_manager import AgentActivityManager
from src.research_phase_manager import ResearchPhaseManager
from src.creation_phase_manager import CreationPhaseManager
from src.review_phase_manager import ReviewPhaseManager
from src.final_check_manager import FinalCheckManager
from core.config_manager import ConfigManager


# Import utility functions that are still needed
from utils import extract_content, extract_all_json, calculate_average_score, format_feedback_summary
from config import CREATION_CONFIG, MAX_REVISION_ROUNDS, SCORE_THRESHOLD, GROUPCHAT_CONFIGS


class NovelWritingPhases:
    """Simplified main controller for the multi-phase novel writing process that orchestrates specialized managers"""

    def __init__(self, conversation_manager: ConversationManager,
                 documentation_manager: DocumentationManager):
        self.conversation_manager = conversation_manager
        self.documentation_manager = documentation_manager
        self.agents_manager = None  # Will be set by caller
        self.progress_callback = None  # For progress notifications

        # Initialize specialized managers
        self.agent_activity_manager = AgentActivityManager()
        self.research_manager = ResearchPhaseManager(conversation_manager, self.agents_manager)
        self.creation_manager = CreationPhaseManager(conversation_manager, documentation_manager, self.agents_manager)
        self.review_manager = ReviewPhaseManager(conversation_manager, self.agent_activity_manager, self.agents_manager)
        self.final_check_manager = FinalCheckManager(conversation_manager, self.agent_activity_manager, self.agents_manager)

        # Initialize config manager
        try:
            self.config_manager = ConfigManager()
        except ImportError:
            self.config_manager = None

    async def async_phase1_research_and_planning(self, novel_concept: str) -> Dict[str, Any]:
        """Async version of phase 1 with delegated implementation to specialized manager"""
        # Set agent manager reference in specialized manager
        self.research_manager.agent_manager = self.agents_manager

        # Set agent activity manager reference in specialized manager if needed
        self.creation_manager.agent_activity_manager = self.agent_activity_manager
        self.review_manager.agent_activity_manager = self.agent_activity_manager
        self.final_check_manager.agent_activity_manager = self.agent_activity_manager

        # Add progress callback to managers if available
        if hasattr(self, 'progress_callback'):
            self.creation_manager.progress_callback = self.progress_callback
            self.review_manager.progress_callback = self.progress_callback
            self.final_check_manager.progress_callback = self.progress_callback

        # Delegate to specialized manager
        return await self.research_manager.execute_research_phase(novel_concept)

    async def async_phase2_creation(self, research_data: Dict[str, Any]) -> str:
        """Async phase 2: Creation with delegated implementation to specialized manager"""
        # Set agent manager reference in specialized manager
        self.creation_manager.agent_manager = self.agents_manager

        # Add progress callback to manager
        if hasattr(self, 'progress_callback'):
            self.creation_manager.progress_callback = self.progress_callback

        # Initialize managers in the creation manager
        from core.chapter_decision_engine import ChapterDecisionEngine
        from core.continuity_manager import ContinuityManager
        from core.story_state_manager import StoryStateManager
        from config import CREATION_CONFIG

        # Delegate to specialized manager
        return await self.creation_manager.execute_creation_phase(research_data)


    async def phase3_review_refinement(self, story: str) -> str:
        """Complete phase 3 implementation with delegated implementation to specialized manager"""
        # Set agent manager reference in specialized manager
        self.review_manager.agent_manager = self.agents_manager

        # Add progress callback to manager
        if hasattr(self, 'progress_callback'):
            self.review_manager.progress_callback = self.progress_callback

        # Delegate to specialized manager
        return await self.review_manager.execute_review_phase(story)


    async def phase4_final_check(self, story: str) -> str:
        """Complete phase 4 implementation with delegated implementation to specialized manager"""
        # Set agent manager reference in specialized manager
        self.final_check_manager.agent_manager = self.agents_manager

        # Delegate to specialized manager
        return await self.final_check_manager.execute_final_check(story)

