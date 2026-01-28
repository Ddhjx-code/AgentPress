#!/usr/bin/env python3
"""
测试中文字符计数功能
"""

import re

def count_chinese_chars(text):
    """计算中文汉字数量"""
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)

def count_chinese_chars_enhanced(text):
    """计算更广泛的中日韩统一表意文字"""
    # 这个范围更广，包括了一些扩展汉字
    chinese_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text)
    return len(chinese_chars)

def analyze_text_composition(text):
    """分析文本组成部分"""
    total_len = len(text)
    chinese_basic = count_chinese_chars(text)
    chinese_extended = count_chinese_chars_enhanced(text)
    english_letters = len(re.findall(r'[a-zA-Z]', text))
    digits = len(re.findall(r'\d', text))
    spaces = len(re.findall(r' ', text))
    punctuation = len(re.findall(r'[，。！？；：""''（）【】《》、,.!?;:]', text))
    other = total_len - chinese_basic - english_letters - digits - spaces - punctuation

    print(f"总字符数: {total_len}")
    print(f"基本汉字: {chinese_basic}")
    print(f"扩展汉字: {chinese_extended}")
    print(f"英文字母: {english_letters}")
    print(f"数字: {digits}")
    print(f"空格: {spaces}")
    print(f"标点符号: {punctuation}")
    print(f"其他字符: {other}")

# 测试示例文本（模拟研究阶段输出，但基于问题描述）
sample_text = """#类型：民间传说（唯恐）
#节奏：悬疑恐惧
#重点：民俗，穿越，或者规则类怪谈衍生故事都可以，选一个
#字数：13000字以上
#完结度：需要完结

这个是大纲示例文本，包括一些结构标记。
第一章 某某开始...
第二章 某某发展...
第三章 某某高潮...
第四章 某某结束..."""

print("文本分析:")
analyze_text_composition(sample_text)

# 检查研究阶段的逻辑
print("\n" + "="*50)
print("中文字符识别模式分析:")
print("基本汉字模式 [\\u4e00-\\u9fff]:")
basic_chinese = re.findall(r'[\u4e00-\u9fff]', sample_text)
print(f"  识别到: {''.join(basic_chinese)[:50]}...")

print("\n扩展汉字模式 [\\u4e00-\\u9fff\\u3400-\\u4dbf\\uf900-\\ufaff]:")
extended_chinese = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', sample_text)
print(f"  识别到: {''.join(extended_chinese)[:50]}...")