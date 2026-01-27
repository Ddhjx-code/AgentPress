"""
配置管理器 - 支持灵活的配置和UI界面对应
"""
from typing import Dict, Any
import json
from pathlib import Path
import copy
from config import CREATION_CONFIG, AGENT_CONFIGS, GROUPCHAT_CONFIGS, MODEL_CONFIG


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.default_creation_config = copy.deepcopy(CREATION_CONFIG)
        self.default_agent_configs = copy.deepcopy(AGENT_CONFIGS)
        self.default_groupchat_configs = copy.deepcopy(GROUPCHAT_CONFIGS)
        self.default_model_config = copy.deepcopy(MODEL_CONFIG)

        self.current_creation_config = copy.deepcopy(CREATION_CONFIG)
        self.current_agent_configs = copy.deepcopy(AGENT_CONFIGS)
        self.current_groupchat_configs = copy.deepcopy(GROUPCHAT_CONFIGS)
        self.current_model_config = copy.deepcopy(MODEL_CONFIG)

    def get_creation_config(self) -> Dict[str, Any]:
        """获取创作配置"""
        return self.current_creation_config

    def update_creation_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新创作配置"""
        for key, value in config_updates.items():
            if key in self.current_creation_config:
                self.current_creation_config[key] = value
        return self.current_creation_config

    def get_agent_configs(self) -> Dict[str, Any]:
        """获取代理配置"""
        return self.current_agent_configs

    def get_groupchat_configs(self) -> Dict[str, Any]:
        """获取组聊配置"""
        return self.current_groupchat_configs

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.current_model_config

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI可用的完整配置"""
        return {
            "creation": {
                "title": "创作设置",
                "description": "控制小说创作的基本参数",
                "parameters": [
                    {
                        "name": "total_target_length",
                        "display_name": "目标总字数",
                        "type": "int",
                        "min_value": 1000,
                        "max_value": 20000,
                        "default": 5000,
                        "description": "目标总字数",
                        "current_value": self.current_creation_config.get("total_target_length", 5000)
                    },
                    {
                        "name": "min_chinese_chars",
                        "display_name": "最小汉字数",
                        "type": "int",
                        "min_value": 1000,
                        "max_value": 20000,
                        "default": 5000,
                        "description": "确保生成的最小汉字数",
                        "current_value": self.current_creation_config.get("min_chinese_chars", 5000)
                    },
                    {
                        "name": "num_chapters",
                        "display_name": "章节数量",
                        "type": "int",
                        "min_value": 1,
                        "max_value": 100,
                        "default": 1,
                        "description": "目标章节数量（实际会动态调整）",
                        "current_value": self.current_creation_config.get("num_chapters", 1)
                    },
                    {
                        "name": "target_length_per_chapter",
                        "display_name": "每章目标字数",
                        "type": "int",
                        "min_value": 500,
                        "max_value": 5000,
                        "default": 3000,
                        "description": "每章的目标字数",
                        "current_value": self.current_creation_config.get("target_length_per_chapter", 3000)
                    },
                    {
                        "name": "chapter_target_chars",
                        "display_name": "每章目标汉字数",
                        "type": "int",
                        "min_value": 500,
                        "max_value": 3000,
                        "default": 1800,
                        "description": "每章的目标汉字数",
                        "current_value": self.current_creation_config.get("chapter_target_chars", 1800)
                    },
                    {
                        "name": "enable_dynamic_chapters",
                        "display_name": "启用动态多章节",
                        "type": "bool",
                        "default": True,
                        "description": "是否启用自适应章节生成",
                        "current_value": self.current_creation_config.get("enable_dynamic_chapters", True)
                    }
                ]
            },
            "agents": {
                "title": "AI角色设置",
                "description": "配置各AI角色的显示名称和职责",
                "parameters": self._get_agent_config_params()
            },
            "groupchat": {
                "title": "协作流程",
                "description": "定义各阶段AI协作的方式",
                "parameters": self._get_groupchat_config_params()
            }
        }

    def _get_agent_config_params(self) -> list:
        """获取代理配置参数"""
        params = []
        for agent_key, config in self.current_agent_configs.items():
            params.append({
                "name": agent_key,
                "display_name": config.get("display_name", agent_key),
                "description": config.get("description", ""),
                "editable": True
            })
        return params

    def _get_groupchat_config_params(self) -> list:
        """获取组聊配置参数"""
        params = []
        for phase_key, config in self.current_groupchat_configs.items():
            params.append({
                "name": phase_key,
                "description": config.get("description", ""),
                "agents": config.get("agents", []),
                "max_turns": config.get("max_turns", 4),
                "editable": True
            })
        return params

    def set_config(self, config_type: str, key: str, value: Any):
        """设置特定配置"""
        if config_type == "creation":
            self.current_creation_config[key] = value
        elif config_type == "agent":
            if key in self.current_agent_configs:
                self.current_agent_configs[key] = value

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.current_creation_config = copy.deepcopy(self.default_creation_config)
        self.current_agent_configs = copy.deepcopy(self.default_agent_configs)
        self.current_groupchat_configs = copy.deepcopy(self.default_groupchat_configs)
        self.current_model_config = copy.deepcopy(self.default_model_config)