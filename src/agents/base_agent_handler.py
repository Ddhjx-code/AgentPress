"""
Agent处理器基础类
定义所有专门化agent处理器的共同接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from autogen_agentchat.agents import AssistantAgent


class BaseAgentHandler(ABC):
    """
    Agent处理器基础类
    所有专门化代理处理器都应该继承此类
    """

    def __init__(self, agent: AssistantAgent):
        """
        初始化处理器

        Args:
            agent: Autogen代理对象
        """
        self.agent = agent
        self.name = agent.name if hasattr(agent, 'name') else 'unknown_agent'

    @abstractmethod
    async def process(self, task: str, **kwargs) -> Any:
        """
        处理任务的抽象方法，子类必须实现

        Args:
            task: 要处理的任务内容
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        pass

    async def run_task(self, task: str, **kwargs) -> Any:
        """
        执行任务的标准方法

        Args:
            task: 任务描述
            **kwargs: 额外参数

        Returns:
            任务执行结果
        """
        return await self.process(task, **kwargs)

    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取代理信息

        Returns:
            代理相关信息的字典
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
        }