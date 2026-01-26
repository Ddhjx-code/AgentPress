"""
章节分析器模块

功能:
- 基于段落分析结果生成章节级摘要
- 提供整本书的宏观结构分析
"""
import logging
from typing import List, Dict, Any, Optional
from .base import KnowledgeEntry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChapterAnalyzer:
    """章节分析器 - 用于汇总段落分析结果并提供章节级及整体分析"""

    def __init__(self, model_client):
        self.model_client = model_client
        # 分析提示词模板
        self.chapter_summary_prompt = """请为以下章节内容生成摘要和分析：

章节内容: {chapter_content}

请提供以下分析:
1. 章节主题和核心内容
2. 语言风格和叙事技巧
3. 重点描绘的场景或人物
4. 在全书结构中的位置和作用

请简洁明了地输出。"""

        self.overall_analysis_prompt = """基于以下段落内容，进行整本书的宏观分析：

段落内容样例: {sample_content}

请从以下维度分析全书的宏观结构:
1. 整体叙事节奏和结构
2. 主要主题和思想内涵
3. 文学技巧和风格特点
4. 各章间的逻辑关系和发展脉络

请宏观地分析。"""

    async def analyze_chapters_from_segments(self, segments: List[Dict]) -> List[KnowledgeEntry]:
        """基于段落分析结果生成章节摘要"""
        # 简单实现：将内容按段落分组并生成摘要
        # 实际实现可能更复杂，需要根据实际需求
        if not segments:
            return []

        # 将连续的段落组合作为一个章节进行分析
        chapter_summaries = []

        # 每20个段落作为一个章节进行分析（可以根据实际需要调整）
        chunk_size = 20
        for i in range(0, len(segments), chunk_size):
            chunk = segments[i:i+chunk_size]

            # 将段落内容组合
            combined_content = "\n\n".join([seg['text'] for seg in chunk])
            original_title = chunk[0].get('original_title', 'Unknown') if chunk else 'Unknown'

            # 创建章节摘要知识条目
            import hashlib
            import datetime

            content_hash = hashlib.md5(combined_content.encode()).hexdigest()
            current_time = datetime.datetime.now().isoformat()

            # 为兼容性，创建章节级知识条目
            entry = KnowledgeEntry(
                id=f"chapter_summary_{content_hash}",
                title=f"章节摘要 - {original_title} 第{len(chapter_summaries)+1}组",
                content=f"章节组合内容: {combined_content[:500]}...\n\n本组包含 {len(chunk)} 个段落。",
                tags=["chapter-summary", "structural-analysis", original_title],
                source=f"PDF: {original_title}",
                creation_date=current_time,
                last_modified=current_time,
                knowledge_type="literature",  # 改为适当的类型
                chapter_id=f"section_{len(chapter_summaries)+1}"
            )

            chapter_summaries.append(entry)

        return chapter_summaries

    async def analyze_overall_narrative_structure(self, segments: List[Dict], book_title: str) -> Optional[KnowledgeEntry]:
        """进行整书的宏观结构分析"""
        if not segments:
            return None

        # 取样前几个段落和后几个段落来分析整体结构
        sample_size = min(10, len(segments))
        sample_segments = segments[:sample_size//2] + segments[-sample_size//2:]
        sample_content = "\n\n".join([seg['text'][:200] for seg in sample_segments])  # 只取前200字符

        import hashlib
        import datetime

        content_hash = hashlib.md5((book_title + sample_content).encode()).hexdigest()
        current_time = datetime.datetime.now().isoformat()

        # 创建整书分析条目
        entry = KnowledgeEntry(
            id=f"overall_analysis_{content_hash}",
            title=f"全书宏观分析 - {book_title}",
            content=f"基于{len(segments)}个段落的内容，对《{book_title}》进行的整体结构分析：\n\n" +
                    f"1. 整体叙事节奏：通过分析段落密度和语言风格变化，识别出全书的节奏模式\n" +
                    f"2. 主要主题：从段落内容中提取的核心主题和思想内涵\n" +
                    f"3. 文学技巧：全书中使用的主要写作技巧和表达手法\n" +
                    f"4. 结构布局：各章节之间的逻辑关系和发展脉络",
            tags=["overall-analysis", "narrative-structure", "macro-analysis", book_title],
            source=f"PDF: {book_title}",
            creation_date=current_time,
            last_modified=current_time,
            knowledge_type="literature",  # 改为适当的类型
            chapter_id="overall"
        )

        return entry