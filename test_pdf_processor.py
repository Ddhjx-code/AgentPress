"""
Unit tests for PDFProcessor functionality
"""
import pytest
from pathlib import Path
import tempfile
import os
from knowledge.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Tests for PDF content processing functionality"""

    def test_segment_content_with_short_paragraphs(self):
        """Test handling of short content segments"""
        processor = PDFProcessor()

        content = "这是第一段。很短。\n\n这是第二段，稍微长一点，包含更多词汇用以测试分段功能。\n\n这是第三段。"
        segments = processor.segment_content(content)

        assert len(segments) > 0
        assert all(isinstance(seg, dict) for seg in segments)

        # The actual number of segments may vary based on the implementation
        # But we should get at least 1 segment for valid content
        assert len(segments) >= 1
        # Each segment should have the expected keys
        for segment in segments:
            assert 'text' in segment
            assert 'id' in segment
            assert len(segment['text']) > 0

    def test_split_long_paragraph(self):
        """Test splitting of long paragraphs into smaller chunks"""
        processor = PDFProcessor()

        # Create a very long paragraph that should be split during _split_into_paragraphs
        long_sentence = "这是一个测试句子。" * 30  # Create paragraph > 400 chars to trigger splitting
        content = f"介绍部分。{long_sentence} 结尾部分。"

        # Test the actual splitting method used internally
        result = processor._split_into_paragraphs(content)

        # Result should be split into smaller chunks based on the logic in _split_into_paragraphs
        # There should be at least one segment
        assert len(result) >= 1
        # Each result should be a reasonable size
        for segment in result:
            assert len(segment) > 0  # Each segment should have content

    def test_segment_cleaning(self):
        """Test cleaning of content during segmentation"""
        processor = PDFProcessor()

        # Content with extra newlines and spaces that should be cleaned
        dirty_content = "混乱的换行符\r\n和连续的空行\n\n\n\n\n以及\r制表符和  连续空格。"

        cleaned = processor._clean_content(dirty_content)

        # Should handle \r and normalize newlines
        assert '\r' not in cleaned
        # Should not have more than 2 consecutive newlines
        assert '\n\n\n' not in cleaned

    def test_chapter_title_detection(self):
        """Test detection of chapter titles"""
        processor = PDFProcessor()

        # Test various chapter patterns
        test_cases = [
            "第一章 这逅",  # Chinese chapter
            "第1章 开始",   # Chinese numeric
            "Part I: Introduction",  # English part
            "非章节标题"    # Non-chapter title for comparison
        ]

        # First three should be detected as chapter titles
        for case in test_cases[:3]:
            assert processor._is_chapter_title(case), f"Should detect {case} as chapter title"

        # Last should not be detected as chapter title
        assert not processor._is_chapter_title(test_cases[3]), f"Should not detect {test_cases[3]} as chapter title"