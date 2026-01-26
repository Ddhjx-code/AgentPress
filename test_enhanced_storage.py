"""
Unit tests for EnhancedKnowledgeStorage functionality
"""
import pytest
import tempfile
import os
from pathlib import Path
from knowledge.enhanced_storage import EnhancedKnowledgeStorage
from knowledge.base import KnowledgeEntry


class TestEnhancedKnowledgeStorage:
    """Tests for enhanced storage functionality"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage during testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a temporary enhanced storage instance"""
        # Patch the initialization to use our temp dir
        storage = EnhancedKnowledgeStorage(str(temp_storage_dir / "enhanced/"))
        return storage

    def test_storage_creation(self, storage):
        """Test that enhanced storage creates proper directory structure"""
        # Storage should initialize with default areas
        expected_areas = {
            'literature', 'techniques', 'examples',
            'character_development', 'dialogue', 'rhythm', 'general'
        }

        assert set(storage.storage_areas.keys()) == expected_areas
        assert all(isinstance(path, Path) for path in storage.storage_areas.values())

    def test_get_storage_file_for_type(self, storage):
        """Test mapping of knowledge type to storage file"""
        # Should return correct file for known types
        assert "literature" in str(storage._get_storage_file_for_type('literature'))
        assert "techniques" in str(storage._get_storage_file_for_type('techniques'))
        assert "character_development" in str(storage._get_storage_file_for_type('character_development'))

        # Unknown type should map to general
        unknown_file = storage._get_storage_file_for_type('unknown_type')
        assert "general" in str(unknown_file)

    @pytest.mark.asyncio
    async def test_save_and_retrieve_entry(self, storage):
        """Test basic save and retrieval of entries"""
        test_entry = KnowledgeEntry(
            id="test_id_123",
            title="Test Title",
            content="This is a test content",
            tags=["test", "tag"],
            source="test",
            creation_date="2023-01-01T00:00:00",
            last_modified="2023-01-01T00:00:00",
            knowledge_type="techniques"
        )

        # Save the entry
        save_result = await storage.save_entry(test_entry)

        # Verify save was successful
        assert save_result is True

        # Try to retrieve the same entry
        retrieved_entry = await storage.get_entry("test_id_123")

        # Verify the entry was retrieved correctly
        assert retrieved_entry is not None
        assert retrieved_entry.title == "Test Title"
        assert retrieved_entry.content == "This is a test content"
        assert retrieved_entry.id == "test_id_123"
        assert set(retrieved_entry.tags) == {"test", "tag"}

    @pytest.mark.asyncio
    async def test_entries_by_type(self, storage):
        """Test retrieving entries by type"""
        # Create and save entries of different types
        techniques_entry = KnowledgeEntry(
            id="tech_001",
            title="Technique Sample",
            content="Some technique",
            tags=["technique", "sample"],
            source="test",
            creation_date="2023-01-01T00:00:00",
            last_modified="2023-01-01T00:00:00",
            knowledge_type="techniques"
        )

        lit_entry = KnowledgeEntry(
            id="lit_001",
            title="Literature Sample",
            content="Some literature",
            tags=["literature", "sample"],
            source="test",
            creation_date="2023-01-01T00:00:00",
            last_modified="2023-01-01T00:00:00",
            knowledge_type="literature"
        )

        # Save both entries
        assert await storage.save_entry(techniques_entry)
        assert await storage.save_entry(lit_entry)

        # Test retrieval by type
        tech_entries = await storage.get_entries_by_type("techniques")
        lit_entries = await storage.get_entries_by_type("literature")

        # Should only return entries of the requested type
        assert len(tech_entries) == 1
        assert tech_entries[0].id == "tech_001"

        assert len(lit_entries) == 1
        assert lit_entries[0].id == "lit_001"

    @pytest.mark.asyncio
    async def test_search_entries(self, storage):
        """Test search functionality"""
        # Save a test entry
        test_entry = KnowledgeEntry(
            id="search_test_01",
            title="Searchable Title with Keywords",
            content="This content contains searchable keywords for testing",
            tags=["search", "test", "keywords"],
            source="test",
            creation_date="2023-01-01T00:00:00",
            last_modified="2023-01-01T00:00:00",
            knowledge_type="techniques"
        )
        await storage.save_entry(test_entry)

        # Test searching in content
        results = await storage.search_entries("searchable")
        assert len(results) == 1
        assert results[0].id == "search_test_01"

        # Test searching in title
        results = await storage.search_entries("Keywords")
        assert len(results) == 1
        assert results[0].id == "search_test_01"

        # Test searching with tags filter
        results = await storage.search_entries("", ["search"])
        assert len(results) == 1
        assert results[0].id == "search_test_01"