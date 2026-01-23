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
    },
    "documentation_specialist": {
        "display_name": "📋 档案员",
        "description": "维护故事一致性和人物档案"
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

# 创作配置
CREATION_CONFIG = {
    "num_chapters": 1,         # 总章数（减少为1章以控制长度）
    "target_length_per_chapter": 2500,  # 每章目标字数（减少以控制token）
    "total_target_length": 3000  # 总目标字数
}

# 评分阈值
SCORE_THRESHOLD = 80
MAX_REVISION_ROUNDS = 3

# 模型配置
MODEL_CONFIG = {
    "model": "qwen3-max",
    "base_url": "https://api.qnaigc.com/v1",
    "vision": False,
    "function_calling": True,
    "json_output": True
}
