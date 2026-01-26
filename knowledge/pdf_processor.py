"""
PDF小说处理模块

功能:
- PDF文件读取和预处理
- 内容分块提取（按段落、章节）
- 提取小说元信息
- 提供标准化的文档结构用于后续分析
"""
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF - 更好的PDF处理库
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF处理器 - 专门用于处理小说PDF文件"""

    def __init__(self):
        # 常见的小说章节标识
        self.chapter_patterns = [
            r'^第\s*([一二三四五六七八九十百千万\d]+)\s*(回|章|节)',  # 第N章/回/节
            r'^CHAPTER\s+([IVXLCDM\d]+)',  # CHAPTER N
            r'^Chapter\s+([IVXLCDM\d]+)',  # Chapter N
            r'^[一二三四五六七八九十百千万\d]+\s*[、.]\s*',  # 汉字序号+、或.
            r'^\d+\s*[、.]\s*[^\d]',      # 阿拉伯数字+、或. 开头文本
            r'Part\s+[IVXLCDM\d]+',       # Part N
            r'^[A-Z][a-z]+\s+\d+',        # 英文单词+数字
        ]

    def extract_pdf_content(self, pdf_path: str) -> Dict:
        """
        提取PDF内容并返回结构化数据

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含PDF基本信息和内容的字典
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)

            # 提取元信息
            try:
                metadata = doc.metadata
                title = metadata.get('title', '') or Path(pdf_path).stem
                author = metadata.get('author', '')
            except:
                # 如果无法获取元信息，使用文件名
                title = Path(pdf_path).stem
                author = 'Unknown'

            # 提取文本内容
            content_parts = []
            current_page_num = 0

            for page_num in range(doc.page_count):
                current_page_num = page_num
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text("text")

                    # 确保文档仍然打开
                    if doc.is_closed:
                        logger.error(f"PDF文档意外关闭: {pdf_path}")
                        break

                    if text.strip():  # 忽略空页
                        content_parts.append(text)
                except Exception as e:
                    logger.warning(f"读取页面 {page_num} 时出错: {str(e)}, 跳过该页面")
                    continue

            content = "\n".join(content_parts)

            # 生成信息
            result = {
                'title': title,
                'author': author,
                'content': content,
                'total_pages': doc.page_count,
                'file_path': pdf_path
            }

            doc.close()
            return result

        except Exception as e:
            logger.error(f"处理PDF文件时出错: {pdf_path}, 错误: {str(e)}")
            if doc and not doc.is_closed:
                try:
                    doc.close()
                except:
                    pass
            raise

    def segment_content(self, content: str) -> List[Dict]:
        """
        将PDF内容按段落和章节分段

        Args:
            content: PDF的原始文本内容

        Returns:
            分段列表，每个元素包含段落内容、位置等信息
        """
        # 清理文本 - 移除多余的换行符和空格
        print("🧹 正在清理文本内容...")
        cleaned_content = self._clean_content(content)

        # 按照段落进行分割
        print("✂️  正在按段落分割内容...")
        paragraphs = self._split_into_paragraphs(cleaned_content)
        total_paragraphs = len(paragraphs)
        print(f"✅ 段落分割完成，共 {total_paragraphs} 个段落")

        # 识别章节划分
        print("챕 正在识别章节划分...")
        segmented_paragraphs = self._identify_chapters(paragraphs)

        # 为每个段落创建结构化信息
        result = []
        for i, (text, chapter_info) in enumerate(segmented_paragraphs):
            paragraph_info = {
                'id': f'pdf_para_{i:04d}',
                'text': text,
                'original_pos': i,
                'chapter_info': chapter_info,
                'word_count': len(text.strip()),
                'is_chapter_header': chapter_info.get('is_header', False),
                'section_title': chapter_info.get('section_title', '')
            }
            result.append(paragraph_info)

            # 每处理100个段落显示一次进度
            if (i + 1) % 100 == 0:
                progress = (i + 1) / total_paragraphs * 100
                print(f"📝 已处理 {i+1}/{total_paragraphs} 个段落 ({progress:.1f}%)")

        logger.info(f"内容已分割为 {len(result)} 个段落段")
        print(f"✅ 内容已分割为 {len(result)} 个分段条目")
        return result

    def _clean_content(self, content: str) -> str:
        """清理PDF内容文本"""
        # 替换连续的空白字符为单个空格，保留重要的段落分割符
        content = re.sub(r'\r', '\n', content)  # 统一换行符

        # 保留段落级的分割（两个或多个换行）
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 压缩单个换行和连字符（如换行处断开的单词）
        lines = content.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # 检查当前行是否很短（可能导致连词分割错误）
                if len(line) > 10:
                    processed_lines.append(line)
                # 如果行末以连字符结束，并且不是章节标题，则可能是一个被拆开的词
                elif line.endswith('-') and len(line) > 1 and not self._is_chapter_title(line):
                    if i < len(lines) - 1:
                        # 与下一行合并
                        if processed_lines:  # 如果之前有行被处理
                            processed_lines[-1] = processed_lines[-1][:-1] + lines[i+1].lstrip()
                        continue  # 跳过当前行
                else:
                    processed_lines.append(line)

        # 重新组合段落
        final_content = '\n'.join(processed_lines)

        # 再次合并过多的空行
        final_content = re.sub(r'\n{3,}', '\n\n', final_content)

        return final_content

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """按段落分割内容，对于长段落进行分割"""
        # 按双换行分割段落
        paragraphs = content.split('\n\n')

        # 过滤掉空的或太短的内容
        paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]

        # 智能分割过长段落
        final_paragraphs = []
        for para in paragraphs:
            if len(para) > 500 and not self._is_chapter_title(para):  # 太长的段落进行分割
                # 按句子结束符进行子分割
                sentences = re.split(r'([。！？!?]+)', para)
                sub_paragraphs = []

                current_para = ""
                for sentence in sentences:
                    if len(current_para + sentence) < 400:
                        current_para += sentence
                    else:
                        if current_para.strip():
                            sub_paragraphs.append(current_para.strip())
                        current_para = sentence

                if current_para.strip():
                    sub_paragraphs.append(current_para.strip())

                # 分割太长的部分，避免AI处理超限
                for sub_para in sub_paragraphs:
                    if len(sub_para) > 500:
                        # 按固定长度切分
                        for i in range(0, len(sub_para), 400):
                            chunk = sub_para[i:i+400]
                            final_paragraphs.append(chunk)
                    else:
                        final_paragraphs.append(sub_para)
            else:
                if len(para) < 50 and final_paragraphs:  # 过短的内容合并
                    # 检查是否可能是章节标题
                    prev_para = final_paragraphs[-1]
                    if self._is_chapter_title(para) or len(para) < 20:  # 章节标题单独保留
                        final_paragraphs.append(para)
                    else:  # 合并到前一段落
                        final_paragraphs[-1] = prev_para + " " + para
                else:
                    final_paragraphs.append(para)

        return final_paragraphs

    def _identify_chapters(self, paragraphs: List[str]) -> List[Tuple[str, Dict]]:
        """识别文本中的章节划分"""
        result = []

        for para in paragraphs:
            chapter_info = {'is_header': False, 'section_title': ''}

            if self._is_chapter_title(para):
                chapter_info['is_header'] = True
                chapter_info['section_title'] = para.strip()

            result.append((para, chapter_info))

        # 更新所有段落的章节归属信息
        final_result = []
        current_chapter = "开头部分"

        for para, info in result:
            if info['is_header']:
                current_chapter = info['section_title']
                final_result.append((para, info))
            else:
                info['current_chapter'] = current_chapter
                final_result.append((para, info))

        return final_result

    def _is_chapter_title(self, text: str) -> bool:
        """判断文本是否是章节标题"""
        text = text.strip()
        for pattern in self.chapter_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        return False

    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        完整的PDF处理流程

        Args:
            pdf_path: PDF文件路径

        Returns:
            经过分段的PDF内容列表
        """
        print(f"📖 开始处理PDF文件: {Path(pdf_path).name}")
        logger.info(f"开始处理PDF: {pdf_path}")

        # 提取完整内容
        print("🔍 正在提取PDF内容...")
        pdf_data = self.extract_pdf_content(pdf_path)
        title = pdf_data['title']
        content = pdf_data['content']
        total_pages = pdf_data['total_pages']

        print(f"✅ PDF内容提取完成 ({total_pages} 页)")

        # 分段处理
        print("✂️  正在对内容进行分段...")
        segmented_content = self.segment_content(content)

        # 添加小说标题到每段
        for segment in segmented_content:
            segment['original_title'] = title

        print(f"✅ PDF内容分段完成，共分割出 {len(segmented_content)} 个段落")
        logger.info(f"PDF处理完成，共分割出 {len(segmented_content)} 个段落段")
        return segmented_content


# 使用示例（可选测试方法）
if __name__ == "__main__":
    processor = PDFProcessor()
    # 示例用法：
    # processed_data = processor.process_pdf("example_novel.pdf")
    # print(f"已提取: {len(processed_data)} 个段落")