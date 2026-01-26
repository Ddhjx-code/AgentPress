# knowledge/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class KnowledgeEntry:
    """Represents a single knowledge entry"""
    id: str
    title: str
    content: str
    tags: List[str]
    source: str
    creation_date: str
    last_modified: str
    knowledge_type: str  # "example", "technique", "background", "template"
    chapter_id: Optional[str] = None  # 关联的章节ID，可选字段

class BaseKnowledgeStorage(ABC):
    """Abstract base class for knowledge storage implementations"""

    @abstractmethod
    async def save_entry(self, entry: KnowledgeEntry) -> bool:
        pass

    @abstractmethod
    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        pass

    @abstractmethod
    async def search_entries(self, query: str, tags: Optional[List[str]] = None) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def get_all_entries(self) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        pass

    @abstractmethod
    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        pass

class BaseKnowledgeRetriever(ABC):
    """Abstract base class for knowledge retrieval implementations"""

    @abstractmethod
    async def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def semantic_search(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        pass