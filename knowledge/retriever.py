# knowledge/retriever.py
import asyncio
from typing import Any, Dict, List, Optional
from .base import BaseKnowledgeRetriever, BaseKnowledgeStorage, KnowledgeEntry
from .storage import JsonFileKnowledgeStorage

class SimpleKnowledgeRetriever(BaseKnowledgeRetriever):
    """Simple knowledge retrieval based on keyword matching"""

    def __init__(self, storage: BaseKnowledgeStorage):
        self.storage = storage

    async def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """Retrieve knowledge based on query and optional category"""
        tags = [category] if category else None
        results = await self.storage.search_entries(query, tags)

        # Sort by "relevance" (simple word count match for now)
        query_lower = query.lower()
        def relevance_score(entry: KnowledgeEntry):
            content_lower = entry.content.lower()
            title_lower = entry.title.lower()
            # Score based on keyword matches
            score = content_lower.count(query_lower) + title_lower.count(query_lower)
            # Prefer exact matches in title
            if query.lower() in title_lower.lower():
                score += 10
            return score

        # Sort by relevance score descending
        results.sort(key=relevance_score, reverse=True)
        return results[:limit]

    async def semantic_search(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Simple fallback if semantic search is not available"""
        # For now, just return keyword search
        # This would be replaced with real embedding/semantic search later
        return await self.retrieve_knowledge(query, limit=limit)