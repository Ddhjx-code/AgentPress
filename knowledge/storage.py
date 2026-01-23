# knowledge/storage.py
import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime
from .base import BaseKnowledgeStorage, KnowledgeEntry

class JsonFileKnowledgeStorage(BaseKnowledgeStorage):
    """Default file-based knowledge storage implementation"""

    def __init__(self, storage_path: str = "data/knowledge_repo/json_storage.json"):
        self.storage_path = Path(storage_path)
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._ensure_directory()
        self._load_existing_data()

    def _ensure_directory(self):
        """Ensure the storage directory exists"""
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True)

    def _load_existing_data(self):
        """Load existing knowledge entries from persistent storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for entry_data in data.get("entries", []):
                    # 兼容旧版本的entry_data，添加缺失的chapter_id
                    if 'chapter_id' not in entry_data or entry_data.get('chapter_id') is None:
                        entry_data['chapter_id'] = None
                    entry = KnowledgeEntry(**entry_data)
                    self.entries[entry.id] = entry
            except Exception as e:
                print(f"Error loading knowledge storage: {e}")
                # Initialize with empty structure
                self.entries = {}
        else:
            # Create new file with empty structure
            self._save_to_file()

    def _save_to_file(self):
        """Save all entries to persistent storage"""
        entries_data = []
        for entry in self.entries.values():
            entries_data.append({
                "id": entry.id,
                "title": entry.title,
                "content": entry.content,
                "tags": entry.tags,
                "source": entry.source,
                "creation_date": entry.creation_date,
                "last_modified": entry.last_modified,
                "knowledge_type": entry.knowledge_type,
                "chapter_id": entry.chapter_id
            })

        data_to_save = {
            "entries": entries_data,
            "metadata": {
                "last_updated": datetime.now().isoformat()
            }
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    async def save_entry(self, entry: KnowledgeEntry) -> bool:
        """Save a knowledge entry"""
        entry.last_modified = datetime.now().isoformat()
        self.entries[entry.id] = entry
        self._save_to_file()
        return True

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific knowledge entry"""
        return self.entries.get(entry_id)

    async def search_entries(self, query: str, tags: Optional[List[str]] = None) -> List[KnowledgeEntry]:
        """Search for entries matching query and tags"""
        results = []
        lower_query = query.lower()

        for entry in self.entries.values():
            # Check if query matches in title or content
            if lower_query in entry.title.lower() or lower_query in entry.content.lower():
                # If tags specified, check if entry has all required tags
                if tags is not None:
                    if all(tag in entry.tags for tag in tags):
                        results.append(entry)
                else:
                    results.append(entry)
            # Otherwise check if tags match (if provided)
            elif tags is not None:
                if all(tag in entry.tags for tag in tags):
                    results.append(entry)

        return results

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        """Get all knowledge entries"""
        return list(self.entries.values())

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_to_file()
            return True
        return False

    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        """Update a knowledge entry"""
        if entry.id in self.entries:
            entry.last_modified = datetime.now().isoformat()
            self.entries[entry.id] = entry
            self._save_to_file()
            return True
        return False

    async def get_entries_by_type(self, knowledge_type: str) -> List[KnowledgeEntry]:
        """Get entries of a specific knowledge type"""
        return [entry for entry in self.entries.values() if entry.knowledge_type == knowledge_type]

    async def get_entries_by_chapter(self, chapter_id: str) -> List[KnowledgeEntry]:
        """Get entries associated with a specific chapter"""
        return [entry for entry in self.entries.values()
                if entry.chapter_id and entry.chapter_id == chapter_id]

    async def get_entries_by_chapter_and_type(self, chapter_id: str, knowledge_type: str) -> List[KnowledgeEntry]:
        """Get entries of specific type for a particular chapter"""
        return [entry for entry in self.entries.values()
                if entry.chapter_id == chapter_id and
                   entry.knowledge_type == knowledge_type]

    async def associate_with_chapter(self, entry_id: str, chapter_id: str) -> bool:
        """Associate a knowledge entry with a specific chapter"""
        if entry_id in self.entries:
            self.entries[entry_id].chapter_id = chapter_id
            self.entries[entry_id].last_modified = datetime.now().isoformat()
            self._save_to_file()
            return True
        return False

    async def remove_chapter_association(self, entry_id: str) -> bool:
        """Remove chapter association for a knowledge entry"""
        if entry_id in self.entries:
            self.entries[entry_id].chapter_id = None
            self.entries[entry_id].last_modified = datetime.now().isoformat()
            self._save_to_file()
            return True
        return False

    async def get_all_chapter_ids(self) -> List[str]:
        """Get all unique chapter IDs in the knowledge storage"""
        chapter_ids = set()
        for entry in self.entries.values():
            if entry.chapter_id:
                chapter_ids.add(entry.chapter_id)
        return list(chapter_ids)