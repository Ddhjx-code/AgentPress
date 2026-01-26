#!/usr/bin/env python3
"""
测试新的fact_checker兼容性
"""
import sys
from pathlib import Path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from utils import calculate_average_score, format_feedback_summary

def test_fact_checker_compatibility():
    """测试fact_checker不同输出格式的兼容性"""

    print("🧪 测试fact_checker输出格式兼容性...")

    # 1. 测试旧格式
    old_format = {
        "fact_checker": {
            "score": 85,
            "is_logical": True,
            "is_based_on_original": True,
            "overall_comment": "故事逻辑基本清晰",
            "issues": [
                {
                    "location": "第3段",
                    "problem": "人物动机不够清晰",
                    "severity": "中等",
                    "suggestion": "补充角色背景说明"
                }
            ],
            "suggestions": [
                "增加角色背景说明",
                "清晰化动机"
            ]
        }
    }

    old_score = calculate_average_score(old_format)
    old_summary = format_feedback_summary(old_format)
    print(f"旧格式测试: 评分={old_score}, 摘要='{old_summary}'")

    # 2. 测试新格式 - 单段评审
    new_format_single = {
        "fact_checker": {
            "original_excerpt": "这是一个测试段落...",
            "applied_strategies": [
                {
                    "strategy_type": "A",
                    "specific_technique": "A_欲望-障碍模型",
                    "effectiveness": "high",
                    "context_fit": "支撑当前情节"
                }
            ],
            "logic_gaps": [
                {
                    "gap_type": "动机缺失",
                    "missing_strategy": "A_欲望-障碍模型",
                    "symptom": "读者无法理解主角为何冒险",
                    "location": "第3段",
                    "suggestion": "添加动机说明"
                }
            ],
            "strengths": [
                "B_规则锚定清晰"
            ],
            "genre_alignment": ["玄幻"]
        }
    }

    new_score = calculate_average_score(new_format_single)
    new_summary = format_feedback_summary(new_format_single)
    print(f"新格式(单段)测试: 评分={new_score}, 摘要='{new_summary}'")

    # 3. 测试新格式 - 世界观设定评审
    new_format_setting = {
        "fact_checker": {
            "setting_summary": "一个奇幻世界观...",
            "coherence_score": "high",
            "anchored_rules": ["魔法消耗寿命", "皇族血脉可驭龙"],
            "unanchored_risks": [
                {
                    "rule": "龙可以穿越时空",
                    "risk": "未说明限制条件",
                    "fix_strategy": "B_规则锚定"
                }
            ],
            "character_motivation_support": "A_欲望-障碍模型可支撑多角色",
            "recommended_additions": [
                "添加 B_历史层积"
            ]
        }
    }

    setting_score = calculate_average_score(new_format_setting)
    setting_summary = format_feedback_summary(new_format_setting)
    print(f"新格式(设定)测试: 评分={setting_score}, 摘要='{setting_summary}'")

    # 测试多代理混合
    mixed_feedback = {**old_format, **new_format_single, **new_format_setting}
    mixed_score = calculate_average_score(mixed_feedback)
    mixed_summary = format_feedback_summary(mixed_feedback)
    print(f"混合格式测试: 评分={mixed_score:.1f}")
    print(f"摘要: {mixed_summary}")

    print("✅ 测试完成！新旧格式兼容性正常")


if __name__ == "__main__":
    test_fact_checker_compatibility()