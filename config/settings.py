"""
增强的配置管理系统，支持多层次覆盖机制
默认值 -> 配置文件 -> 环境变量 -> 命令行参数
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import copy
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import copy
import importlib.util
import sys

# 使用动态导入来避免模块名冲突
config_path = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("original_config", config_path)
original_config = importlib.util.module_from_spec(spec)
sys.modules["original_config"] = original_config
spec.loader.exec_module(original_config)

# 从原始配置中获取设置
CREATION_CONFIG = original_config.CREATION_CONFIG
AGENT_CONFIGS = original_config.AGENT_CONFIGS
GROUPCHAT_CONFIGS = original_config.GROUPCHAT_CONFIGS
MODEL_CONFIG = original_config.MODEL_CONFIG

# 默认配置
DEFAULT_SETTINGS = {
    "creation": copy.deepcopy(CREATION_CONFIG),
    "agents": copy.deepcopy(AGENT_CONFIGS),
    "groupchat": copy.deepcopy(GROUPCHAT_CONFIGS),
    "model": copy.deepcopy(MODEL_CONFIG)
}

class HierarchicalConfigManager:
    """多层次配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.config = copy.deepcopy(DEFAULT_SETTINGS)

        # 按优先级加载配置
        self._load_from_defaults()
        self._load_from_file()
        self._load_from_env()

    def _load_from_defaults(self):
        """从默认设置加载"""
        self.config = copy.deepcopy(DEFAULT_SETTINGS)

    def _load_from_file(self):
        """从配置文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
                print(f"📊 从配置文件 {self.config_file} 加载配置")
            except Exception as e:
                print(f"⚠️  从配置文件加载失败: {e}")

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 加载创建配置相关的环境变量
        creation_keys = {
            'total_target_length': int,
            'min_chinese_chars': int,
            'num_chapters': int,
            'target_length_per_chapter': int,
            'chapter_target_chars': int,
            'enable_dynamic_chapters': lambda x: x.lower() == 'true'
        }

        for key, converter in creation_keys.items():
            env_key = f"CREATION_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    converted_value = converter(env_value)
                    self.config['creation'][key] = converted_value
                    print(f"📊 环境变量 {env_key} -> creation.{key} = {converted_value}")
                except Exception as e:
                    print(f"⚠️  环境变量 {env_key} 转换失败: {e}")

        # 加载模型相关信息（如API Key等敏感信息）
        model_api_key = os.getenv("MODEL_API_KEY")
        if model_api_key:
            # 将API密钥存储在单独的字典中以避免配置导出时泄露
            if not hasattr(self, 'secrets'):
                self.secrets = {}
            self.secrets['api_key'] = model_api_key

        model_base_url = os.getenv("MODEL_BASE_URL")
        if model_base_url:
            self.config['model']['base_url'] = model_base_url
            print(f"📊 从环境变量设置模型URL: {model_base_url}")

    def load_from_cli_args(self, cli_args: Dict[str, Any]):
        """从CLI参数加载配置 - 最高优先级"""
        # 创建配置键的映射，CLI参数名->实际配置路径
        cli_config_mapping = {
            'total_target_length': ('creation', 'total_target_length'),
            'min_chinese_chars': ('creation', 'min_chinese_chars'),
            'target_length_per_chapter': ('creation', 'target_length_per_chapter'),
            'chapter_target_chars': ('creation', 'chapter_target_chars'),
            'enable_dynamic_chapters': ('creation', 'enable_dynamic_chapters'),
            'num_chapters': ('creation', 'num_chapters')
        }

        for cli_key, (section, config_key) in cli_config_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                self.config[section][config_key] = cli_args[cli_key]
                print(f"📊 CLI参数 -> {section}.{config_key} = {cli_args[cli_key]}")

        # 处理特殊参数
        if 'model_api_key' in cli_args and cli_args['model_api_key']:
            if not hasattr(self, 'secrets'):
                self.secrets = {}
            self.secrets['api_key'] = cli_args['model_api_key']

        if 'model_base_url' in cli_args and cli_args['model_base_url']:
            self.config['model']['base_url'] = cli_args['model_base_url']

    def get_creation_config(self) -> Dict[str, Any]:
        """获取创作配置"""
        return self.config['creation']

    def get_agent_configs(self) -> Dict[str, Any]:
        """获取代理配置"""
        return self.config['agents']

    def get_groupchat_configs(self) -> Dict[str, Any]:
        """获取组聊配置"""
        return self.config['groupchat']

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config['model']

    def get_api_key(self) -> Optional[str]:
        """获取API密钥（从环境变量或CLI参数）"""
        if hasattr(self, 'secrets'):
            return self.secrets.get('api_key')
        return os.getenv('MODEL_API_KEY')

    def write_to_file(self, config_path: str = None):
        """将当前配置写入文件（不包含敏感信息）"""
        config_path = config_path or self.config_file
        config_to_save = copy.deepcopy(self.config)

        # 清理敏感数据
        if hasattr(self, 'secrets'):
            print(f"🔒 保存配置到 {config_path}（已移除敏感信息）")
        else:
            print(f"💾 保存配置到 {config_path}")

        with open(config_path, 'w', encoding='utf-8') as f:
            # 只保存配置，不包含API密钥等敏感信息
            json.dump(config_to_save, f, ensure_ascii=False, indent=2)

    def get_ui_config(self) -> Dict[str, Any]:
        """获取适合UI显示的配置"""
        creation_config = self.get_creation_config()
        agent_configs = self.get_agent_configs()
        groupchat_configs = self.get_groupchat_configs()

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
                        "default": DEFAULT_SETTINGS['creation']['total_target_length'],
                        "description": "目标总字数",
                        "current_value": creation_config.get("total_target_length", 5000)
                    },
                    {
                        "name": "min_chinese_chars",
                        "display_name": "最小汉字数",
                        "type": "int",
                        "min_value": 1000,
                        "max_value": 20000,
                        "default": DEFAULT_SETTINGS['creation']['min_chinese_chars'],
                        "description": "确保生成的最小汉字数",
                        "current_value": creation_config.get("min_chinese_chars", 5000)
                    },
                    {
                        "name": "num_chapters",
                        "display_name": "章节数量",
                        "type": "int",
                        "min_value": 1,
                        "max_value": 100,
                        "default": DEFAULT_SETTINGS['creation']['num_chapters'],
                        "description": "目标章节数量（实际会动态调整）",
                        "current_value": creation_config.get("num_chapters", 1)
                    },
                    {
                        "name": "target_length_per_chapter",
                        "display_name": "每章目标字数",
                        "type": "int",
                        "min_value": 500,
                        "max_value": 5000,
                        "default": DEFAULT_SETTINGS['creation']['target_length_per_chapter'],
                        "description": "每章的目标字数",
                        "current_value": creation_config.get("target_length_per_chapter", 3000)
                    },
                    {
                        "name": "chapter_target_chars",
                        "display_name": "每章目标汉字数",
                        "type": "int",
                        "min_value": 500,
                        "max_value": 3000,
                        "default": DEFAULT_SETTINGS['creation']['chapter_target_chars'],
                        "description": "每章的目标汉字数",
                        "current_value": creation_config.get("chapter_target_chars", 1800)
                    },
                    {
                        "name": "enable_dynamic_chapters",
                        "display_name": "启用动态多章节",
                        "type": "bool",
                        "default": DEFAULT_SETTINGS['creation']['enable_dynamic_chapters'],
                        "description": "是否启用自适应章节生成",
                        "current_value": creation_config.get("enable_dynamic_chapters", True)
                    }
                ]
            },
            "agents": {
                "title": "AI角色设置",
                "description": "配置各AI角色的显示名称和职责",
                "parameters": self._get_agent_config_params(agent_configs)
            },
            "groupchat": {
                "title": "协作流程",
                "description": "定义各阶段AI协作的方式",
                "parameters": self._get_groupchat_config_params(groupchat_configs)
            }
        }

    def _get_agent_config_params(self, agent_configs) -> list:
        """获取代理配置参数"""
        params = []
        for agent_key, config in agent_configs.items():
            params.append({
                "name": agent_key,
                "display_name": config.get("display_name", agent_key),
                "description": config.get("description", ""),
                "editable": True
            })
        return params

    def _get_groupchat_config_params(self, groupchat_configs) -> list:
        """获取组聊配置参数"""
        params = []
        for phase_key, config in groupchat_configs.items():
            params.append({
                "name": phase_key,
                "description": config.get("description", ""),
                "agents": config.get("agents", []),
                "max_turns": config.get("max_turns", 4),
                "editable": True
            })
        return params

    def _merge_config(self, base_config: Dict, override_config: Dict):
        """合并配置：base_config <- override_config"""
        for section, section_config in override_config.items():
            if section in base_config:
                base_config[section].update(section_config)
            else:
                base_config[section] = section_config


# 创建全局配置管理器实例
config_manager = HierarchicalConfigManager()

class BackwardCompatibleConfigManager:
    """向后兼容的配置管理器包装 - 与core/config_manager.py兼容"""

    def __init__(self):
        self._manager = config_manager
        self._creation_config = {}  # 将用于CLI参数覆盖

    def get_creation_config(self) -> Dict[str, Any]:
        base_creation_config = self._manager.get_creation_config()
        # CLI参数可以覆盖的创建配置
        merged = copy.deepcopy(base_creation_config)
        merged.update(self._creation_config)
        return merged

    def update_creation_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """接受外部配置更新(如通过程序调用)"""
        self._creation_config.update(config_updates)
        return self.get_creation_config()

    def get_agent_configs(self) -> Dict[str, Any]:
        return self._manager.get_agent_configs()

    def get_groupchat_configs(self) -> Dict[str, Any]:
        return self._manager.get_groupchat_configs()

    def get_model_config(self) -> Dict[str, Any]:
        return self._manager.get_model_config()

        """获取UI配置"""
    def get_ui_config(self) -> Dict[str, Any]:
        # 使用更新后的创建配置版本返回UI配置
        base_ui_config = copy.deepcopy(self._manager.get_ui_config())

        if self._creation_config:
            for param in base_ui_config["creation"]["parameters"]:
                if param["name"] in self._creation_config:
                    param["current_value"] = self._creation_config[param["name"]]

        return base_ui_config

    def set_config(self, config_type: str, key: str, value: Any):
        """设置配置"""
        if config_type == "creation":
            self._creation_config[key] = value
        # 注意：这里不支持其他配置类型，因为它们由外部配置管理器管理

    def reset_to_defaults(self):
        """重置到默认配置"""
        self._creation_config.clear()

# 为向后兼容创建实例
HierarchicalConfigManager.instance = config_manager