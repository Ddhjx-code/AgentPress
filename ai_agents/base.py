from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAIAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, name: str, system_message: str, model_config: Dict[str, Any]):
        self.name = name
        self.system_message = system_message
        self.model_config = model_config

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process the input and return result"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of the agent"""
        pass

    async def run(self, prompt: str) -> Any:
        """Run the agent with the given prompt"""
        # This is a placeholder implementation
        # In a real implementation, this would call the LLM
        return {
            "response": f"Agent {self.name} processed: {prompt}",
            "metadata": {
                "agent_type": self.__class__.__name__,
                "model_config": self.model_config
            }
        }