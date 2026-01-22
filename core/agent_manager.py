# core/agent_manager.py
from typing import Dict, List, Optional, Any, Union
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config import AGENT_CONFIGS
import asyncio


class ModelConfig:
    """Configuration for different AI models per agent type"""

    def __init__(self):
        self.model_configs = {
            "writer": self._get_writer_config(),
            "editor": self._get_editor_config(),
            "fact_checker": self._get_fact_checker_config(),
            "dialogue_specialist": self._get_dialogue_specialist_config(),
            "mythologist": self._get_researcher_config(),
            "documentation_specialist": self._get_documentation_config()
        }

    def _get_writer_config(self):
        # Strong generative model
        return {
            "model": os.getenv("WRITER_MODEL", "gpt-4"),
            "description": "Primary story content creation",
            "capabilities": ["creative_generation", "narrative_control"]
        }

    def _get_editor_config(self):
        # Assessment model
        return {
            "model": os.getenv("EDITOR_MODEL", "gpt-4"),
            "description": "Overall story evaluation",
            "capabilities": ["quality_assessment", "holistic_review"]
        }

    def _get_fact_checker_config(self):
        # Logic reasoning model
        return {
            "model": os.getenv("FACT_CHECKER_MODEL", "gpt-4"),
            "description": "Logic and consistency verification",
            "capabilities": ["logical_inference", "consistency_check"]
        }

    def _get_dialogue_specialist_config(self):
        # Language understanding focused model
        return {
            "model": os.getenv("DIALOGUE_MODEL", "gpt-4"),
            "description": "Dialogue evaluation and optimization",
            "capabilities": ["dialogue_analysis", "character_voice"]
        }

    def _get_researcher_config(self):
        # Knowledge retrieval model (can be generic)
        return {
            "model": os.getenv("RESEARCHER_MODEL", "gpt-4"),
            "description": "Background research and setting development",
            "capabilities": ["research_synthesis", "background_development"]
        }

    def _get_documentation_config(self):
        # Memory tracking model (long context)
        return {
            "model": os.getenv("DOCUMENTATION_MODEL", "gpt-4"),
            "description": "Maintain consistency across long-form content",
            "capabilities": ["memory_retention", "consistency_tracking"]
        }


class AgentManager:
    """Updated Agent Manager with model-specific allocation"""

    def __init__(self, model_configs: Optional[ModelConfig] = None):
        self.model_configs = model_configs or ModelConfig()
        self.agents = {}

    async def initialize(self, prompts: Dict[str, str]) -> bool:
        """Initialize all agents with error handling and comprehensive setup"""
        print("🔧 初始化智能代理团队...")

        try:
            for agent_key, config in AGENT_CONFIGS.items():
                if agent_key in prompts and prompts[agent_key]:
                    # Use valid identifier for agent name
                    agent_name = self._convert_to_valid_identifier(agent_key)

                    self.agents[agent_key] = AssistantAgent(
                        name=agent_name,
                        model_client=self.model_client,
                        system_message=prompts[agent_key]
                    )
                    print(f"  ✅ {config['display_name']} ({agent_key}) 已就绪")

            self._initialized = True
            print(f"\\n✅ 智能代理团队初始化完成 ({len(self.agents)} 个代理)")
            return len(self.agents) > 0

        except Exception as e:
            print(f"❌ 代理初始化失败: {e}")
            return False

    def get_agent(self, agent_key: str) -> Optional[AssistantAgent]:
        """Get specific agent by key"""
        return self.agents.get(agent_key)

    def get_agents(self, agent_keys: List[str]) -> List[AssistantAgent]:
        """Get multiple agents by keys"""
        return [self.agents[key] for key in agent_keys if key in self.agents]

    def list_agents(self) -> Dict[str, str]:
        """List all available agents"""
        return {key: config["display_name"] for key, config in AGENT_CONFIGS.items()
                if key in self.agents}

    def is_initialized(self) -> bool:
        """Check if agent manager is properly initialized"""
        return self._initialized

    def update_agent_system_message(self, agent_key: str, new_system_message: str) -> bool:
        """Update system message for a specific agent (dynamic adaptation)"""
        if agent_key in self.agents:
            # This would require a different approach since AssistantAgent is immutable
            # In practice, you'd need to replace the agent or use a different agent type
            print(f"⚠️ 暂不支持动态更新 {agent_key} 的系统消息")
            return False
        return False

    @staticmethod
    def _convert_to_valid_identifier(name: str) -> str:
        """
        Convert string to valid Python identifier
        """
        # Replace invalid characters
        valid_name = name.replace("-", "_").replace(" ", "_")
        # Ensure starts with letter or underscore
        if valid_name and not (valid_name[0].isalpha() or valid_name[0] == "_"):
            valid_name = "_" + valid_name
        return valid_name


class GroupChatCoordinator:
    """Coordination manager for multi-agent group conversations"""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager

    async def run_group_discussion(self,
                                 agent_keys: List[str],
                                 task: str,
                                 max_rounds: int = 5,
                                 enable_logging: bool = True) -> Dict[str, Any]:
        """Run structured group discussion among selected agents"""
        if not self.agent_manager.is_initialized():
            return {"error": "Agent manager not initialized", "result": task}

        agents = self.agent_manager.get_agents(agent_keys)
        if not agents:
            return {"error": "No valid agents found", "result": task}

        if enable_logging:
            print(f"\\n👥 组讨论开始，参与代理: {[agent.name for agent in agents]}")

        # Simple round-robin discussion simulation
        # In a real implementation, this would use proper group chat framework
        current_result = task
        discussion_history = []

        for round_num in range(max_rounds):
            for agent in agents:
                try:
                    result = await agent.run(task=f"基于以下信息发表意见：\\n{current_result[:2000]}")
                    content = self._extract_content(result.messages)

                    if enable_logging:
                        print(f"  🗣️  {agent.name} (轮次 {round_num + 1}): {len(content)} 字")

                    discussion_history.append({
                        "agent": agent.name,
                        "round": round_num + 1,
                        "content": content,
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    # Update the current result with the latest input
                    current_result = f"{current_result}\\n\\n{content[:1000]}"

                except Exception as e:
                    print(f"  ⚠️  {agent.name} 轮次 {round_num + 1} 出错: {e}")
                    continue

        return {
            "result": current_result,
            "discussion_history": discussion_history,
            "participating_agents": [agent.name for agent in agents],
            "total_rounds": max_rounds
        }

    def _extract_content(self, messages: List) -> str:
        """Simple content extraction from messages"""
        # This is a simplified version - in real implementation,
        # you'd use the actual utils function
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                return str(last_message.content) if last_message.content else ""
            else:
                return str(last_message) if last_message else ""
        return ""


class DynamicModelAgentManager(AgentManager):
    """Agent manager with dynamic model selection capability"""

    def __init__(self, model_client: OpenAIChatCompletionClient, model_registry: Dict[str, Any] = None):
        super().__init__(model_client)
        self.model_registry = model_registry or {}
        self.current_model_config = "default"

    def switch_model(self, model_config_name: str) -> bool:
        """Switch to different model configuration"""
        if model_config_name in self.model_registry:
            self.current_model_config = model_config_name
            print(f"🔄 已切换到模型配置: {model_config_name}")
            return True
        else:
            print(f"❌ 未找到模型配置: {model_config_name}")
            return False

    def register_model_config(self, name: str, config: Dict[str, Any]):
        """Register a new model configuration"""
        self.model_registry[name] = config
        print(f"✅ 模型配置已注册: {name}")

    def get_model_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get registered model configuration"""
        return self.model_registry.get(name)