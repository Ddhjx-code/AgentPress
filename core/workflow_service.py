"""
统一核心工作流服务
- 同时支持命令行和Web UI调用
- 集成模型配置管理
- 统一小说生成流程
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily

from .agent_manager import AgentManager
from .conversation_manager import ConversationManager
from utils import load_all_prompts


class WorkflowService:
    """
    统一核心工作流服务
    - 同时支持命令行和Web UI调用
    - 集成模型配置管理
    - 统一小说生成流程
    """

    def __init__(self):
        self.model_client = None
        self.agent_manager = None
        self.orchestrator = None
        self.conversation_manager = None
        self.prompts = {}
        self.novel_phases_manager = None  # 添加对NovelWritingPhases的引用

    async def initialize_models(self, api_key: str, base_url: str = "https://apis.iflow.cn/v1", model_name: str = "qwen3-max"):
        """初始化模型"""
        # 创建AI模型客户端
        self.model_client = OpenAIChatCompletionClient(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            model_info=ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                structured_output=False,
                family=ModelFamily.GPT_5
            )
        )

        # 初始化 Agent Manager
        self.agent_manager = AgentManager(model_client=self.model_client)

        # 加载提示词
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts = load_all_prompts(prompts_dir)

        # 初始化代理
        agent_init_success = await self.agent_manager.initialize(self.prompts)
        if not agent_init_success:
            raise Exception("代理初始化失败")

        # 初始化编排器和小说阶段管理器（使用局部导入避免循环依赖）
        from phases import NovelWorkflowOrchestrator
        from src.novel_phases_manager import NovelWritingPhases
        from src.conversation_manager import ConversationManager
        from src.documentation_manager import DocumentationManager

        self.orchestrator = NovelWorkflowOrchestrator()
        self.conversation_manager = ConversationManager() if not self.conversation_manager else self.conversation_manager
        documentation_manager = DocumentationManager()

        # 初始化小说阶段管理器
        self.novel_phases_manager = NovelWritingPhases(
            conversation_manager=self.conversation_manager,
            documentation_manager=documentation_manager
        )
        self.novel_phases_manager.agents_manager = self.agent_manager

        return True

    async def execute_workflow(self,
                              novel_concept: str,
                              multi_chapter: bool = False,
                              total_chapters: int = 1) -> Dict[str, Any]:
        """
        执行小说生成工作流
        """
        if not self.agent_manager or not self.novel_phases_manager:
            raise Exception("服务未初始化")

        try:
            # 设置进度回调以便实时更新
            self.novel_phases_manager.progress_callback = self._on_progress_update

            # 使用小说阶段管理器执行完整工作流程
            # 第一阶段：研究和规划
            self._on_progress_update("创作流程", "phase1", "开始创意研究和规划")
            research_data = await self.novel_phases_manager.async_phase1_research_and_planning(novel_concept)

            # 第二阶段：创作
            self._on_progress_update("创作流程", "phase2", "开始动态章节创作")
            story = await self.novel_phases_manager.async_phase2_creation(research_data)

            # 第三阶段：评审和修订（可选，基于配置）
            self._on_progress_update("创作流程", "phase3", "开始评审和修订")
            refined_story = await self.novel_phases_manager.phase3_review_refinement(story)

            # 第四阶段：最终检查
            self._on_progress_update("创作流程", "phase4", "执行最终检查")
            final_story = await self.novel_phases_manager.phase4_final_check(refined_story)

            self._on_progress_update("创作流程", "complete", "创作完成")

            result = {
                "status": "success",
                "initial_idea": novel_concept,
                "research_data": research_data,
                "final_story": final_story,
                "story_length": len(final_story)
            }

            # 添加代理工作日志（如果存在）
            if hasattr(self.novel_phases_manager, 'get_agent_work_summary'):
                result["agent_work_log"] = self.novel_phases_manager.get_agent_work_summary()

            # 添加对话历史
            result["conversation_history"] = self.get_conversation_history()

            return result
        except Exception as e:
            import traceback
            # 发生错误时也要通知前端
            self._on_progress_update("创作流程", "error", f"生成过程中出现错误: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }

    async def _on_progress_update(self, phase: str, step: str, message: str, progress: float = None):
        """
        进度更新回调函数
        """
        # 可以用于实时反馈或记录进度
        print(f"[PROGRESS] {phase} - {step}: {message}")
        if progress:
            print(f"[PROGRESS] 进度: {progress*100:.1f}%")

        # 如果Web UI端有WebSocket连接管理器，应将进度信息发送出去
        # 这里我们保存当前进度状态
        if not hasattr(self, 'current_progress_status'):
            self.current_progress_status = {}

        # 更新当前进度状态
        self.current_progress_status = {
            "phase": phase,
            "step": step,
            "message": message,
            "progress": progress,
            "timestamp": datetime.now().timestamp()
        }

        # 如果有进度回调函数，调用它
        if hasattr(self, '_progress_callback') and self._progress_callback:
            try:
                await self._progress_callback(phase, step, message, progress)
            except Exception as e:
                print(f"[PROGRESS] 进度回调错误: {e}")

    def get_conversation_history(self):
        """获取对话历史"""
        if self.conversation_manager:
            return {
                "conversations": getattr(self.conversation_manager, 'conversation_history', []),
                "versions": getattr(self.conversation_manager, 'story_versions', {}),
                "feedbacks": getattr(self.conversation_manager, 'feedback_records', {}),
                "documentation": getattr(self.conversation_manager, 'documentation_records', {}),
                "all_history": self.conversation_manager.get_all_history() if hasattr(self.conversation_manager, 'get_all_history') else {}
            }
        elif self.orchestrator:
            cm = self.orchestrator.get_conversation_manager()
            if cm:
                return {
                    "conversations": getattr(cm, 'conversation_history', []),
                    "versions": getattr(cm, 'story_versions', {}),
                    "feedbacks": getattr(cm, 'feedback_records', {}),
                    "documentation": getattr(cm, 'documentation_records', {}),
                    "all_history": cm.get_all_history() if hasattr(cm, 'get_all_history') else {}
                }
        return {}