# agents_manager.py
from typing import Dict, List
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config import AGENT_CONFIGS

class AgentsManager:
    """管理所有编辑Agent"""
    
    def __init__(self, model_client: OpenAIChatCompletionClient):
        self.model_client = model_client
        self.agents: Dict[str, AssistantAgent] = {}
    
    async def initialize(self, prompts: Dict[str, str]) -> bool:
        """初始化所有Agent"""
        print("🔧 初始化编辑团队Agent...\n")
        
        for agent_key, config in AGENT_CONFIGS.items():
            if agent_key in prompts and prompts[agent_key]:
                # 使用简单的英文名称作为Agent name（必须是有效的Python标识符）
                agent_name = self._convert_to_valid_identifier(agent_key)
                
                self.agents[agent_key] = AssistantAgent(
                    name=agent_name,  # 使用转换后的名称
                    model_client=self.model_client,
                    system_message=prompts[agent_key]
                )
                print(f"  ✅ {config['display_name']} (内部名称: {agent_name}) 已就绪")
        
        print(f"\n✅ 编辑团队初始化完成 ({len(self.agents)} 位编辑)\n")
        return len(self.agents) > 0
    
    def get_agent(self, agent_key: str) -> AssistantAgent:
        """获取指定Agent"""
        return self.agents.get(agent_key)
    
    def get_agents(self, agent_keys: List[str]) -> List[AssistantAgent]:
        """获取多个Agent"""
        return [self.agents[key] for key in agent_keys if key in self.agents]
    
    def list_agents(self) -> Dict[str, str]:
        """列出所有可用Agent"""
        return {key: config["display_name"] for key, config in AGENT_CONFIGS.items() 
                if key in self.agents}
    
    @staticmethod
    def _convert_to_valid_identifier(name: str) -> str:
        """
        将字符串转换为有效的Python标识符
        例如: "dialogue_specialist" -> "dialogue_specialist"
             "fact_checker" -> "fact_checker"
        """
        # 替换不允许的字符
        valid_name = name.replace("-", "_").replace(" ", "_")
        # 确保开头是字母或下划线
        if valid_name and not (valid_name[0].isalpha() or valid_name[0] == "_"):
            valid_name = "_" + valid_name
        return valid_name
