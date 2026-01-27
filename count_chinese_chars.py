#!/usr/bin/env python3
import re

def count_chinese_characters(text):
    """只统计中文汉字数量"""
    # 使用正则表达式匹配中文汉字
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)

def count_chinese_words(text):
    """统计中文汉字和词语"""
    # 去掉标点、空格等非字符内容
    clean_text = re.sub(r'[^\u4e00-\u9fff]', '', text)
    return len(clean_text)

def count_with_standard_words(text):
    """统计标准字数（中文汉字+英文字母+数字，按1:1比例）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    digits = len(re.findall(r'[0-9]', text))
    return chinese_chars + english_chars + digits

# 读取生成的故事
with open('output/long_story_6000_chars.txt', 'r', encoding='utf-8') as f:
    content = f.read()

chinese_char_count = count_chinese_characters(content)
chinese_word_count = count_chinese_words(content)
standard_char_count = count_with_standard_words(content)

print(f"总字符数(含空白): {len(content)}")
print(f"中文汉字数: {chinese_char_count}")
print(f"纯中文字符数(不含标点空格): {chinese_word_count}")
print(f"标准字数(中文+英文+数字): {standard_char_count}")
print(f"AI代理报告字数: 3878 (可能是包含标点和空格的字符数)")