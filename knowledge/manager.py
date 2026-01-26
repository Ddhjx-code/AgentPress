# knowledge/manager.py
import asyncio
from typing import Any, Dict, List, Optional
from .base import KnowledgeEntry
from .storage import JsonFileKnowledgeStorage
from .enhanced_storage import EnhancedKnowledgeStorage  # 新增增强存储
from .retriever import SimpleKnowledgeRetriever

class KnowledgeManager:
    """Main manager for knowledge base functionality"""

    def __init__(self, storage_path: str = "data/knowledge_repo/json_storage.json", use_enhanced_storage: bool = False):
        if use_enhanced_storage:
            # 使用增强存储系统（按类型分片存储）
            self.storage = EnhancedKnowledgeStorage(storage_path)
        else:
            # 使用传统存储系统（单文件存储）
            from pathlib import Path
            if "enhanced" in storage_path or storage_path.endswith("enhanced"):
                self.storage = EnhancedKnowledgeStorage(storage_path)
            else:
                self.storage = JsonFileKnowledgeStorage(storage_path)
        self.retriever = SimpleKnowledgeRetriever(self.storage)

    async def add_entry(
        self,
        title: str,
        content: str,
        tags: List[str],
        knowledge_type: str,
        source: str = "manual"
    ) -> bool:
        """Add a new knowledge entry"""
        # Generate ID from hash of content
        import hashlib
        content_hash = hashlib.md5((title + content).encode()).hexdigest()

        entry = KnowledgeEntry(
            id=content_hash,
            title=title,
            content=content,
            tags=tags,
            source=source,
            creation_date=str(__import__('datetime').datetime.now().isoformat()),
            last_modified=str(__import__('datetime').datetime.now().isoformat()),
            knowledge_type=knowledge_type
        )

        return await self.storage.save_entry(entry)

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific knowledge entry"""
        return await self.storage.get_entry(entry_id)

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """Search knowledge based on query and category"""
        return await self.retriever.retrieve_knowledge(query, category, limit)

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        """Get all knowledge entries"""
        return await self.storage.get_all_entries()

    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        """Update an existing knowledge entry"""
        return await self.storage.update_entry(entry)

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        return await self.storage.delete_entry(entry_id)

    async def get_examples_by_type(self, example_type: str) -> List[KnowledgeEntry]:
        """Get examples of a specific type from knowledge base"""
        all_entries = await self.get_all_entries()
        return [
            entry for entry in all_entries
            if entry.knowledge_type == "example" and example_type.lower() in entry.tags
        ]

    async def get_techniques_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get writing techniques in a specific category"""
        all_entries = await self.get_all_entries()
        return [
            entry for entry in all_entries
            if entry.knowledge_type == "technique" and category.lower() in entry.tags
        ]