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
from src.novel_phases_manager import NovelWritingPhases
from src.documentation_manager import DocumentationManager
from phases import NovelWorkflowOrchestrator
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

    async def initialize_models(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1", model_name: str = "qwen-max"):
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

        # 初始化编排器
        self.orchestrator = NovelWorkflowOrchestrator()

        return True

    async def execute_workflow(self,
                              novel_concept: str,
                              multi_chapter: bool = False,
                              total_chapters: int = 1) -> Dict[str, Any]:
        """
        执行小说生成工作流
        """
        if not self.agent_manager or not self.orchestrator:
            raise Exception("服务未初始化")

        try:
            # 执行完整工作流程 - 现在对于multi_chapter场景，将由AI动态决定章节
            final_output = await self.orchestrator.run_async_workflow(
                initial_idea=novel_concept,
                multi_chapter=True,  # 对于AI驱动动态章节，我们始终使用多章节模式
                total_chapters=total_chapters,  # 仍保留用于向后兼容
                agents_manager=self.agent_manager
            )

            return {
                "status": "success",
                "data": final_output
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_conversation_history(self):
        """获取对话历史"""
        if self.orchestrator:
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