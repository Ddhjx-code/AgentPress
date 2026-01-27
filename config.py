# config.py
from pathlib import Path
from typing import Dict

# 基础配置
PROMPTS_DIR = Path("prompts")
OUTPUT_DIR = Path("output")

# Agent 配置
AGENT_CONFIGS = {
    "mythologist": {
        "display_name": "📜 跨文化符号策略师",
        "description": "从全球神话、传说、象征中提取可操作的创作方向"
    },
    "writer": {
        "display_name": "✍️  原创作家",
        "description": "创作高质量的故事内容"
    },
    "dialogue_specialist": {
        "display_name": "💬 对话策略专家",
        "description": "优化对话的生动性和角色辨识度"
    },
    "fact_checker": {
        "display_name": "🏗️ 故事架构师",
        "description": "确保逻辑自洽和设定一致，应用构建策略库"
    },
    "editor": {
        "display_name": "🧐 整体审阅师",
        "description": "提供综合质量评价和发布建议"
    },
    "documentation_specialist": {
        "display_name": "📚 复杂度控制员",
        "description": "维护故事连贯性，管理设定档案和人物发展"
    },
    "write_enviroment_specialist": {
        "display_name": "🌆 感官呈现专家",
        "description": "优化环境描写与氛围营造策略"
    },
    "write_rate_specialist": {
        "display_name": "⏱️ 情绪节拍师",
        "description": "设计叙事节奏和情绪起伏曲线"
    }
}

# GroupChat 配置
GROUPCHAT_CONFIGS = {
    "research_phase": {
        "agents": ["mythologist", "writer"],
        "max_turns": 4,
        "description": "创意符号挖掘与大纲规划"
    },
    "review_phase": {
        "agents": ["fact_checker", "dialogue_specialist", "editor"],
        "max_turns": 5,
        "description": "架构审查与质量把控"
    },
    "style_optimization": {
        "agents": ["write_enviroment_specialist", "write_rate_specialist", "dialogue_specialist"],
        "max_turns": 4,
        "description": "感官体验与节奏优化"
    },
    "consistency_phase": {
        "agents": ["documentation_specialist", "fact_checker", "mythologist"],
        "max_turns": 3,
        "description": "连续性核查与符号一致性管理"
    }
}

# 创作配置
CREATION_CONFIG = {
    "num_chapters": 1,         # 总章数（会动态增加直到达到目标字数）
    "target_length_per_chapter": 3000,  # 每章基础字数目标
    "total_target_length": 5000,  # 总目标字数（默认5000字，可调整）
    "min_chinese_chars": 5000,  # 最少中文汉字数要求
    "enable_dynamic_chapters": True,  # 是否启用动态多章节生成
    "chapter_target_chars": 1800    # 每章目标汉字数
}

# 评分阈值
SCORE_THRESHOLD = 80
MAX_REVISION_ROUNDS = 3

# 模型配置
MODEL_CONFIG = {
    "model": "qwen3-max",
    "base_url": "https://apis.iflow.cn/v1",
    "vision": False,
    "function_calling": True,
    "json_output": True
}
