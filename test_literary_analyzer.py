"""
Unit tests for LiteraryAnalyzer functionality
"""
import pytest
from unittest.mock import AsyncMock, Mock
from knowledge.literary_analyzer import LiteraryAnalyzer
from knowledge.base import KnowledgeEntry
from core.workflow_service import WorkflowService


class TestLiteraryAnalyzer:
    """Tests for literary analysis functionality"""

    @pytest.fixture
    def mock_workflow_service(self):
        """Mock workflow service for testing"""
        workflow_service = Mock()
        workflow_service.model_client = Mock()
        # Mock the create method to return a simple response
        workflow_service.model_client.create = AsyncMock()
        workflow_service.model_client.create.return_value = Mock()
        workflow_service.model_client.create.return_value.content = "Test analysis result"
        return workflow_service

    @pytest.fixture
    def literary_analyzer(self, mock_workflow_service):
        """Create a literary analyzer instance for testing"""
        return LiteraryAnalyzer(mock_workflow_service)

    @pytest.mark.asyncio
    async def test_analyze_paragraph_basic(self, literary_analyzer):
        """Test basic paragraph analysis"""
        paragraph_data = {
            'id': 'test_id',
            'text': '这是一个测试段落，用于测试文学分析功能。',
            'original_title': 'Test Novel'
        }

        # Mock response for all AI calls
        literary_analyzer._analyze_technique = AsyncMock(return_value="技巧分析结果")
        literary_analyzer._analyze_rhythm = AsyncMock(return_value="节奏分析结果")
        literary_analyzer._identify_classic_paragraph = AsyncMock(return_value=(True, "经典段落分析"))
        literary_analyzer._analyze_character_development = AsyncMock(return_value="人物分析结果")
        literary_analyzer._analyze_dialogue = AsyncMock(return_value="对话分析结果")

        result = await literary_analyzer.analyze_paragraph(paragraph_data, 'Test Novel')

        # Should create a knowledge entry
        assert result is not None
        assert isinstance(result, KnowledgeEntry)
        assert "文学技巧分析" in result.title or "经典段落" in result.title

    @pytest.mark.asyncio
    async def test_create_technique_entry(self, literary_analyzer):
        """Test creation of technique analysis entry"""
        entry = await literary_analyzer._create_technique_entry(
            "测试文本片段",
            "分析：运用了比喻和拟人手法",
            "测试小说",
            "chunk_0001",
            {"section_title": "第1章", "current_chapter": "第1章"}
        )

        # Verify entry properties
        assert isinstance(entry, KnowledgeEntry)
        assert entry.knowledge_type == "novel-technique"
        assert "分析" in entry.content
        assert entry.tags  # Should have meaningful tags

    @pytest.mark.asyncio
    async def test_create_classic_paragraph_entry(self, literary_analyzer):
        """Test creation of classic paragraph entry"""
        entry = await literary_analyzer._create_classic_paragraph_entry(
            "测试文本片段",
            "评价：内容优美，具有文学价值",
            "测试小说",
            "chunk_0002",
            {"section_title": "第2章", "current_chapter": "第2章"}
        )

        # Verify entry properties
        assert isinstance(entry, KnowledgeEntry)
        assert entry.knowledge_type == "classic-paragraph"
        assert "评价" in entry.content

    @pytest.mark.asyncio
    async def test_batch_analyze_empty_list(self, literary_analyzer):
        """Test batch analysis with empty list"""
        result = await literary_analyzer.batch_analyze([], 'Test Novel')
        assert result == []

    @pytest.mark.asyncio
    async def test_analysis_prompt_templates(self, literary_analyzer):
        """Test that analysis prompt templates are properly loaded"""
        required_templates = [
            'technique_analysis',
            'rhythm_analysis',
            'classic_paragraph_analysis',
            'character_development_analysis',
            'dialogue_analysis'
        ]

        for template in required_templates:
            assert template in literary_analyzer.analysis_prompt_templates
            assert isinstance(literary_analyzer.analysis_prompt_templates[template], str)
            assert '{text}' in literary_analyzer.analysis_prompt_templates[template]