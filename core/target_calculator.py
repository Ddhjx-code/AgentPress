"""
目标字数计算器 - 标准化字符统计方式
"""
import re
from typing import Dict, Any


class TargetCalculator:
    """专门处理字数统计和目标计算的助手类"""

    @staticmethod
    def count_chinese_characters(text: str) -> int:
        """计算中文汉字数量"""
        return len(re.findall(r'[\u4e00-\u9fff]', text))

    @staticmethod
    def count_all_characters(text: str) -> int:
        """计算总字符数（包括标点、空格、数字等）"""
        return len(text)

    @staticmethod
    def count_words_or_characters(text: str, count_type: str = "chinese") -> int:
        """通用计数方法"""
        if count_type == "chinese":
            return TargetCalculator.count_chinese_characters(text)
        elif count_type == "all":
            return TargetCalculator.count_all_characters(text)
        else:
            # 默认使用汉字计数（对中文用户更友好）
            return TargetCalculator.count_chinese_characters(text)

    @staticmethod
    def evaluate_target_achievement(current_content: str,
                                  config: Dict[str, Any],
                                  target_type: str = "chinese") -> Dict[str, Any]:
        """
        评估目标完成情况

        Args:
            current_content: 当前内容
            config: 配置数据
            target_type: 计数类型 ("chinese" 或 "all")

        Returns:
            包含完成状态的字典
        """
        current_count = TargetCalculator.count_words_or_characters(current_content, target_type)

        if target_type == "chinese":
            target_count = config.get("min_chinese_chars", config.get("total_target_length", 5000))
        else:
            target_count = config.get("total_target_length", 5000)

        progress = min(100, int(current_count / target_count * 100)) if target_count > 0 else 0

        return {
            "current_count": current_count,
            "target_count": target_count,
            "progress": progress,
            "target_achieved": current_count >= target_count,
            "count_type": target_type
        }


# 创建全局实例
target_calculator = TargetCalculator()