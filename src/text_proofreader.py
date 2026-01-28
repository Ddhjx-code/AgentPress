"""
文本校对器 - 优化生成小说的排版和格式
"""

import re
from typing import Dict, Any, List


class TextProofreader:
    """
    文本校对器，专门优化生成小说的格式、标点和排版
    """

    def __init__(self):
        # 定义校对规则
        self.correction_rules = [
            # 修复标点符号问题
            (r'\s+([，。！？；：])', r'\1'),  # 修正标点前的多余空格
            (r'([，。！？；：])\s*\n', r'\1\n'),  # 修正回车前的标点
            (r'([。！？])\s*([\"\'])', r'\1\2'),  # 修正句末标点后的引号
            (r'([\"\'])\s+([^\s])', r'\1\2'),  # 修正引号后的多余空格

            # 优化段落格式
            (r'\n{3,}', r'\n\n'),  # 限制连续空行为2个
            (r'\n\s+\n', r'\n\n'),  # 修正空行中的空格

            # 优化中文字符间的间距
            (r'([，。！？；：])\s+([一-龯])', r'\1\2'),  # 中文标点后不应该有空格
            (r'([一-龯])([，。！？；：])', r'\1\2'),  # 中文字符和标点之间无空格

            # 修正数字与单位间的问题
            (r'(\d)\s+([%年月日时分秒])', r'\1\2'),  # 修正数字与单位间的空格
        ]

        self.chinese_punctuation = ['，', '。', '！', '？', '；', '：', '"', '"', ''', ''']
        self.english_punctuation = [',', '.', '!', '?', ';', ':', '"', '"', "'", "'"]

    def proofread_text(self, text: str) -> str:
        """
        执行文本校对

        Args:
            text: 需要校对的文本

        Returns:
            校对后的文本
        """
        if not text or len(text.strip()) == 0:
            return text

        corrected_text = text

        # 应用基础规则
        for pattern, replacement in self.correction_rules:
            corrected_text = re.sub(pattern, replacement, corrected_text)

        # 执行高级校对
        corrected_text = self._apply_advanced_proofreading(corrected_text)

        # 修正段落格式
        corrected_text = self._format_paragraphs(corrected_text)

        # 修正章节标题格式
        corrected_text = self._format_chapter_titles(corrected_text)

        return corrected_text.strip()

    def _apply_advanced_proofreading(self, text: str) -> str:
        """
        应用高级校对规则
        """
        result = []
        i = 0
        while i < len(text):
            char = text[i]
            result.append(char)

            # 处理中文标点符号的特殊规则
            if char in self.chinese_punctuation:
                # 检查下一个非空白字符
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1

                # 如果下一个字符是中文字符，移除空格
                if j < len(text) and '\u4e00' <= text[j] <= '\u9fff':
                    # 不添加空格，保持紧凑
                    pass
                elif j < len(text) and text[j] in self.chinese_punctuation:
                    # 中文标点后不加空格
                    pass
                elif j < len(text) and char in ['。', '！', '？'] and text[j] not in ['"', '']:
                    # 句号、感叹号、问号后可以添加一个空格（如果是句子开头）
                    pass
            elif char in ['"', '']:
                # 处理引号
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1
                # 如果引号后面是中文，不加空格
                if j < len(text) and '\u4e00' <= text[j] <= '\u9fff':
                    # 移除到下一个非空字符之间的空格
                    pass

            i += 1

        final_text = ''.join(result)

        # 再次执行正则表达式规则
        for pattern, replacement in self.correction_rules:
            final_text = re.sub(pattern, replacement, final_text)

        return final_text

    def _format_paragraphs(self, text: str) -> str:
        """
        格式化段落，确保正确的段落间距
        """
        # 分割成段落
        paragraphs = text.split('\n')
        formatted_paragraphs = []

        for paragraph in paragraphs:
            if paragraph.strip():  # 非空行
                paragraph = paragraph.strip()  # 去除段落首尾空格/空行
                # 段落首行不需要缩进，因为这是小说格式
                formatted_paragraphs.append(paragraph)
            else:  # 空行
                formatted_paragraphs.append('')

        # 合并段落，确保段落间只有一行空行
        final = []
        for i, para in enumerate(formatted_paragraphs):
            if para:
                final.append(para)
            elif i > 0 and i < len(formatted_paragraphs) - 1:
                # 中间的空行可以保留，但连续多个只保留一个
                if not (final and final[-1] == ''):  # 如果前一行不是空行
                    final.append('')

        return '\n'.join(final)

    def _format_chapter_titles(self, text: str) -> str:
        """
        格式化章节标题
        """
        # 查找章节标题格式如：第X章、第X节、chapter等
        patterns = [
            r'(第[一二三四五六七八九十零\d]+[章回节幕集卷])',  # 第X章格式
            r'(第[零一二三四五六七八九十\d]+[回节幕集卷])',  # 第X回等格式
            r'(\[第[一二三四五六七八九十零\d]+[章回节幕集卷]\])',  # [第X章]格式
            r'(CHAPTER\s+[\dIVXLCDM]+)',  # CHAPTER X 格式
        ]

        for pattern in patterns:
            # 为章节标题前后添加换行
            text = re.sub(pattern, r'\n\n\1\n\n', text, flags=re.IGNORECASE)

        # 清理多余空行
        text = re.sub(r'\n{4,}', r'\n\n\n', text)

        return text

    def generate_proofreading_report(self, original: str, corrected: str) -> Dict[str, Any]:
        """
        生成校对报告

        Args:
            original: 原始文本
            corrected: 校对后的文本

        Returns:
            校对报告
        """
        report = {
            'original_length': len(original),
            'corrected_length': len(corrected),
            'length_difference': len(corrected) - len(original),
            'improvements': [],
        }

        # 统计文本特征
        def count_punctuation(text):
            punct_count = {}
            for char in text:
                if char in self.chinese_punctuation:
                    punct_count[char] = punct_count.get(char, 0) + 1
            return punct_count

        original_punct = count_punctuation(original)
        corrected_punct = count_punctuation(corrected)

        report['improvements'].append({
            'type': 'punctuation',
            'description': '中文标点符号优化',
            'original': f"标点总数: {sum(original_punct.values())}",
            'corrected': f"标点总数: {sum(corrected_punct.values())}",
        })

        # 统计段落数
        original_paragraphs = len([p for p in original.split('\n') if p.strip()])
        corrected_paragraphs = len([p for p in corrected.split('\n') if p.strip()])

        report['improvements'].append({
            'type': 'formatting',
            'description': '段落格式优化',
            'original': f"段落数: {original_paragraphs}",
            'corrected': f"段落数: {corrected_paragraphs}",
        })

        return report


# 使用示例和测试函数
def test_proofreader():
    """
    测试文本校对器
    """
    proofreader = TextProofreader()
    sample_text = """这个故事讲述了 一个冒险家。   他的名字是李明，
    他热爱探险。   "我们必须找到宝藏，" 李明说。
    这个任务非常 困难！我们能完成吗 ？ """

    corrected = proofreader.proofread_text(sample_text)
    print("原始文本:")
    print(repr(sample_text))
    print("\n校对后文本:")
    print(repr(corrected))

    report = proofreader.generate_proofreading_report(sample_text, corrected)
    print("\n校对报告:")
    print(f"原始长度: {report['original_length']}, 校对后长度: {report['corrected_length']}")
    print(f"长度变化: {report['length_difference']}")
    for improvement in report['improvements']:
        print(f"- {improvement['description']}: {improvement['original']} -> {improvement['corrected']}")

    return corrected


if __name__ == "__main__":
    test_proofreader()