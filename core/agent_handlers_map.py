"""
Agent处理器映射服务
管理agent_key到专门处理器的映射关系
"""
from typing import Dict, Any, Optional
from autogen_agentchat.agents import AssistantAgent


class AgentHandlersMap:
    """Agent处理器映射容器"""

    def __init__(self):
        self._handlers: Dict[str, Any] = {}
        self._agents: Dict[str, AssistantAgent] = {}

    def register_handler(self, agent_key: str, handler: Any):
        """注册agent处理器"""
        self._handlers[agent_key] = handler

    def get_handler(self, agent_key: str) -> Optional[Any]:
        """获取指定agent的处理器"""
        return self._handlers.get(agent_key)

    def register_agent(self, agent_key: str, agent: AssistantAgent):
        """注册原始agent对象"""
        self._agents[agent_key] = agent

    def get_agent(self, agent_key: str) -> Optional[AssistantAgent]:
        """获取原始agent对象"""
        return self._agents.get(agent_key)

    def list_handlers(self):
        """列出所有已注册的处理器"""
        return list(self._handlers.keys())