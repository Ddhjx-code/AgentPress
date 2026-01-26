"""
增强型知识库存储模块

功能:
- 使用多个专用存储分区 (分类存储：literature, techniques, examples等)
- 按需加载和卸载数据以节省内存
- 提供索引机制提高检索效率
- 支持增量更新避免整库重载
"""
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import hashlib
from .base import BaseKnowledgeStorage, KnowledgeEntry

class EnhancedKnowledgeStorage(BaseKnowledgeStorage):
    """
    增强型知识库存储系统
    将知识数据按类型分片存储，每种类型单独一个文件
    """

    def __init__(self, base_storage_path: str = "data/knowledge_repo/enhanced/"):
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)

        # 定义不同的知识存储区域
        self.storage_areas = {
            'literature': self.base_storage_path / "literature.json",
            'techniques': self.base_storage_path / "techniques.json",
            'examples': self.base_storage_path / "examples.json",
            'character_development': self.base_storage_path / "character_development.json",
            'dialogue': self.base_storage_path / "dialogue.json",
            'rhythm': self.base_storage_path / "rhythm.json",
            'general': self.base_storage_path / "general.json"
        }

        # 缓存当前加载的条目（按需加载）
        self.entries: Dict[str, KnowledgeEntry] = {}
        # 记录类型到文件的映射
        self.type_to_file = {}  # 知道每个entry属于哪个文件
        self.type_index: Dict[str, List[str]] = {}  # 类型到entry_id的索引

        # 加载现有的存储区域
        self._load_all_storage_areas()

    def _get_storage_file_for_type(self, knowledge_type: str) -> Path:
        """确定某个知识类型应存储在哪个文件"""
        if knowledge_type in self.storage_areas:
            return self.storage_areas[knowledge_type]
        # 如果类型不存在，则归类到general
        return self.storage_areas.get('general', self.base_storage_path / "general.json")

    def _load_all_storage_areas(self):
        """加载所有存储区域"""
        for area_type, file_path in self.storage_areas.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    for entry_data in data.get("entries", []):
                        # 兼容旧版本数据格式，添加缺失的chapter_id
                        if 'chapter_id' not in entry_data or entry_data.get('chapter_id') is None:
                            entry_data['chapter_id'] = None
                        entry = KnowledgeEntry(**entry_data)

                        self.entries[entry.id] = entry
                        self.type_to_file[entry.id] = str(file_path)

                        # 索引该类型
                        if area_type not in self.type_index:
                            self.type_index[area_type] = []
                        self.type_index[area_type].append(entry.id)

                        # 同时索引真实类型
                        if entry.knowledge_type not in self.type_index:
                            self.type_index[entry.knowledge_type] = []
                        self.type_index[entry.knowledge_type].append(entry.id)

                except Exception as e:
                    print(f"加载 {file_path} 时出错: {e}")

    async def save_entry(self, entry: KnowledgeEntry) -> bool:
        """保存知识条目到相应的分区"""
        try:
            # 确定保存的文件
            storage_file = self._get_storage_file_for_type(entry.knowledge_type)

            # 读取当前文件数据
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"entries": [], "metadata": {}}

            # 检查是否已存在
            exists = False
            for i, existing_entry in enumerate(data["entries"]):
                if existing_entry["id"] == entry.id:
                    # 更新现有条目
                    existing_entry.update({
                        "title": entry.title,
                        "content": entry.content,
                        "tags": entry.tags,
                        "source": entry.source,
                        "knowledge_type": entry.knowledge_type,
                        "last_modified": entry.last_modified,
                        "chapter_id": entry.chapter_id
                    })
                    exists = True
                    break

            if not exists:
                # 新增条目
                data["entries"].append({
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

            # 保存到文件
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 更新内部缓存和索引
            entry.last_modified = datetime.now().isoformat()
            self.entries[entry.id] = entry
            self.type_to_file[entry.id] = str(storage_file)

            if entry.knowledge_type not in self.type_index:
                self.type_index[entry.knowledge_type] = []
            if entry.id not in self.type_index[entry.knowledge_type]:
                self.type_index[entry.knowledge_type].append(entry.id)

            return True
        except Exception as e:
            print(f"保存知识条目失败: {e}")
            return False

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """获取特定知识条目"""
        if entry_id in self.entries:
            return self.entries[entry_id]
        return None

    async def search_entries(self, query: str, tags: Optional[List[str]] = None) -> List[KnowledgeEntry]:
        """在所有存储区域中搜索条目"""
        results = []
        query_lower = query.lower()

        for entry in self.entries.values():
            # 检查查询匹配
            matches_query = (
                query_lower in entry.title.lower() or
                query_lower in entry.content.lower()
            )

            # 检查标签匹配
            if tags is not None:
                matches_tags = all(tag in entry.tags for tag in tags)
                if tags and (not matches_tags or not matches_query):
                    continue
            elif not matches_query and tags is not None:
                continue

            results.append(entry)

        return results

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        """获取所有知识条目"""
        return list(self.entries.values())

    async def delete_entry(self, entry_id: str) -> bool:
        """删除知识条目"""
        if entry_id not in self.entries:
            return False

        try:
            # 从对应的存储文件中删除
            storage_file_path = self.type_to_file.get(entry_id)
            if storage_file_path:
                storage_file = Path(storage_file_path)
                if storage_file.exists():
                    with open(storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 移除对应条目
                    data["entries"] = [
                        entry for entry in data["entries"]
                        if entry["id"] != entry_id
                    ]

                    # 保存回去
                    with open(storage_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

            # 从内部缓存和索引中移除
            entry_to_delete = self.entries.pop(entry_id, None)
            if entry_to_delete:
                self.type_to_file.pop(entry_id, None)
                if entry_to_delete.knowledge_type in self.type_index:
                    if entry_id in self.type_index[entry_to_delete.knowledge_type]:
                        self.type_index[entry_to_delete.knowledge_type].remove(entry_id)

            return True
        except Exception as e:
            print(f"删除条目时出错: {e}")
            return False

    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        """更新知识条目"""
        if entry.id in self.entries:
            # 先删除旧版本
            await self.delete_entry(entry.id)

            # 再保存新版本
            return await self.save_entry(entry)
        else:
            return False

    async def get_entries_by_type(self, knowledge_type: str) -> List[KnowledgeEntry]:
        """按类型获取知识条目 (高效方法)"""
        entry_ids = self.type_index.get(knowledge_type, [])
        return [self.entries[entry_id] for entry_id in entry_ids if entry_id in self.entries]

    async def get_entries_by_types(self, knowledge_types: List[str]) -> List[KnowledgeEntry]:
        """获取多种类型的条目"""
        results = []
        for k_type in knowledge_types:
            results.extend(await self.get_entries_by_type(k_type))
        return results