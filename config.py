# config.py
from pathlib import Path
from typing import Dict

# 基础配置
PROMPTS_DIR = Path("prompts")
OUTPUT_DIR = Path("output")

# Agent 配置
AGENT_CONFIGS = {
    "mythologist": {
        "display_name": "🧙 神话学家",
        "description": "分析故事背景和设定"
    },
    "writer": {
        "display_name": "✍️  作家",
        "description": "创作故事内容"
    },
    "dialogue_specialist": {
        "display_name": "💬 对话专家",
        "description": "优化对话质量"
    },
    "fact_checker": {
        "display_name": "🔍 事实核查员",
        "description": "检查逻辑和事实"
    },
    "editor": {
        "display_name": "📝 文学编辑",
        "description": "评价整体质量"
    }
}

# GroupChat 配置
GROUPCHAT_CONFIGS = {
    "research_phase": {
        "agents": ["mythologist", "writer"],
        "max_turns": 4,
        "description": "创意研究和规划"
    },
    "review_phase": {
        "agents": ["fact_checker", "dialogue_specialist", "editor"],
        "max_turns": 5,
        "description": "评审和修订"
    }
}

# 评分阈值
SCORE_THRESHOLD = 80
MAX_REVISION_ROUNDS = 3

# 模型配置
MODEL_CONFIG = {
    "model": "qwen3-max",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "vision": False,
    "function_calling": True,
    "json_output": True
}
