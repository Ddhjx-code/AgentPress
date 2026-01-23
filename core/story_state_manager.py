"""
故事状态管理器
- 管理多章节故事的复杂状态
- 提供章节级别的操作接口
- 维护故事整体状态与章节状态的关系
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ChapterState:
    """章节状态"""
    chapter_id: str
    title: str
    content: str
    word_count: int
    created_at: str
    updated_at: str
    status: str  # 'draft', 'reviewing', 'approved', 'revising', 'final'
    metadata: Dict[str, Any]


@dataclass
class StoryState:
    """故事整体状态"""
    story_id: str
    title: str
    overall_status: str  # 'init', 'writing', 'revising', 'completed', 'published'
    created_at: str
    updated_at: str
    total_chapters: int
    current_chapter: int
    word_count: int
    metadata: Dict[str, Any]


class StoryStateManager:
    """
    故事状态管理器
    - 管理故事的整个生命周期
    - 追踪每个章节的状态
    - 提供高效的查询和更新操作
    """

    def __init__(self):
        self.stories: Dict[str, StoryState] = {}
        self.chapters: Dict[str, ChapterState] = {}
        self.story_chapter_map: Dict[str, List[str]] = {}  # story_id -> [chapter_id, ...]

    def create_story(self, story_id: str, title: str, initial_metadata: Optional[Dict] = None) -> StoryState:
        """
        创建新故事
        """
        if story_id in self.stories:
            raise ValueError(f"故事ID {story_id} 已存在")

        now = datetime.now().isoformat()

        story = StoryState(
            story_id=story_id,
            title=title,
            overall_status="init",
            created_at=now,
            updated_at=now,
            total_chapters=0,
            current_chapter=0,
            word_count=0,
            metadata=initial_metadata or {}
        )

        self.stories[story_id] = story
        self.story_chapter_map[story_id] = []

        # 立即广播状态变化（如果有监听机制）
        self._on_story_state_change(story_id)

        return story

    def create_chapter(self, story_id: str, title: str, content: str = "") -> ChapterState:
        """
        为故事创建新章节
        """
        if story_id not in self.stories:
            raise ValueError(f"故事ID {story_id} 不存在")

        # 生成章节ID (使用故事ID+序号)
        chapter_index = len(self.story_chapter_map[story_id]) + 1
        chapter_id = f"{story_id}_chapter_{chapter_index}"

        now = datetime.now().isoformat()

        chapter = ChapterState(
            chapter_id=chapter_id,
            title=title,
            content=content,
            word_count=len(content),
            created_at=now,
            updated_at=now,
            status="draft",
            metadata={}
        )

        self.chapters[chapter_id] = chapter
        self.story_chapter_map[story_id].append(chapter_id)

        # 更新故事状态
        story = self.stories[story_id]
        story.total_chapters = len(self.story_chapter_map[story_id])
        story.current_chapter = story.total_chapters
        story.word_count += chapter.word_count
        story.updated_at = now
        story.overall_status = "writing"

        self._on_story_state_change(story_id)
        self._on_chapter_state_change(chapter_id)

        return chapter

    def update_chapter_content(self, chapter_id: str, new_content: str) -> ChapterState:
        """
        更新章节内容
        """
        if chapter_id not in self.chapters:
            raise ValueError(f"章节ID {chapter_id} 不存在")

        chapter = self.chapters[chapter_id]
        old_word_count = chapter.word_count

        now = datetime.now().isoformat()

        chapter.content = new_content
        chapter.word_count = len(new_content)
        chapter.updated_at = now

        # 更新相关故事的统计信息
        story_id = self._get_story_id_from_chapter(chapter_id)
        if story_id in self.stories:
            story = self.stories[story_id]
            story.word_count = story.word_count - old_word_count + chapter.word_count
            story.updated_at = now

        self._on_chapter_state_change(chapter_id)
        self._on_story_state_change(story_id)

        return chapter

    def update_chapter_status(self, chapter_id: str, status: str) -> ChapterState:
        """
        更新章节状态
        """
        if chapter_id not in self.chapters:
            raise ValueError(f"章节ID {chapter_id} 不存在")

        chapter = self.chapters[chapter_id]
        old_status = chapter.status
        chapter.status = status
        chapter.updated_at = datetime.now().isoformat()

        self._on_chapter_state_change(chapter_id)

        # 可能需要更新故事的全局状态
        story_id = self._get_story_id_from_chapter(chapter_id)
        if story_id:
            # 根据所有章节的状态更新故事状态
            self._update_story_overall_status_sync(story_id)

        return chapter

    def get_story_state(self, story_id: str) -> Optional[StoryState]:
        """
        获取故事整体状态
        """
        return self.stories.get(story_id)

    def get_chapter_state(self, chapter_id: str) -> Optional[ChapterState]:
        """
        获取章节状态
        """
        return self.chapters.get(chapter_id)

    def get_story_chapters(self, story_id: str) -> List[ChapterState]:
        """
        获取故事的所有章节（按顺序）
        """
        if story_id not in self.story_chapter_map:
            return []

        return [self.chapters[chapter_id] for chapter_id in self.story_chapter_map[story_id]
                if chapter_id in self.chapters]

    def _update_story_overall_status_sync(self, story_id: str):
        """
        根据所有章节状态自动更新故事的整体状态（同步版本）
        """
        story = self.stories.get(story_id)
        if not story:
            return

        chapters = self.get_story_chapters(story_id)

        if not chapters:
            # 如果没有章节，则状态取决于是否初始化
            return

        all_approved = all(chapter.status in ["approved", "final"] for chapter in chapters)
        any_draft = any(chapter.status == "draft" for chapter in chapters)
        any_revising = any(chapter.status == "revising" for chapter in chapters)

        if all_approved:
            story.overall_status = "completed"
        elif any_revising:
            story.overall_status = "revising"
        elif any_draft:
            story.overall_status = "writing"

        story.updated_at = datetime.now().isoformat()
        self._on_story_state_change(story_id)

    def _get_story_id_from_chapter(self, chapter_id: str) -> Optional[str]:
        """
        从章节ID推导出故事ID
        假设章节ID格式为 'story_id_chapter_n'
        """
        parts = chapter_id.split('_chapter_')
        if len(parts) >= 2:
            story_id = f"{parts[0]}_chapter_{parts[1][0]}" if len(parts[1]) > 0 else parts[0]
            # 更准确地分割，取前缀部分
            for story_id_candidate in self.story_chapter_map.keys():
                if chapter_id.startswith(f"{story_id_candidate}_chapter_"):
                    return story_id_candidate
        return None

    def get_story_by_chapter_id(self, chapter_id: str) -> Optional[StoryState]:
        """
        根据章节ID获取对应的故事状态
        """
        story_id = self._get_story_id_from_chapter(chapter_id)
        return self.stories.get(story_id) if story_id else None

    def export_story_as_text(self, story_id: str) -> str:
        """
        将整个故事导出为纯文本格式
        """
        chapters = self.get_story_chapters(story_id)
        if not chapters:
            return ""

        text_result = []
        for chapter in chapters:
            text_result.append(f"# {chapter.title}")
            text_result.append(chapter.content)
            text_result.append("")  # 空行分隔

        return "\n\n".join(text_result).strip()

    def export_story_as_dict(self, story_id: str) -> Dict[str, Any]:
        """
        将整个故事导出为字典格式
        """
        story = self.get_story_state(story_id)
        if not story:
            return {}

        return {
            "story": asdict(story),
            "chapters": [asdict(chapter) for chapter in self.get_story_chapters(story_id)]
        }

    def _on_chapter_state_change(self, chapter_id: str):
        """
        章节状态变更时的回调方法（可扩展用于实时通知）
        """
        # 这里可以触发WebSocket消息或其他通知机制
        pass

    def _on_story_state_change(self, story_id: str):
        """
        故事状态变更时的回调方法（可扩展用于实时通知）
        """
        # 这里可以触发WebSocket消息或其他通知机制
        pass

    def delete_chapter(self, chapter_id: str) -> bool:
        """
        删除章节（谨慎使用）
        """
        if chapter_id not in self.chapters:
            return False

        chapter = self.chapters[chapter_id]

        # 从故事映射中移除
        story_id = self._get_story_id_from_chapter(chapter_id)
        if story_id and story_id in self.story_chapter_map:
            if chapter_id in self.story_chapter_map[story_id]:
                self.story_chapter_map[story_id].remove(chapter_id)

        # 从存储中删除
        del self.chapters[chapter_id]

        # 更新故事统计
        if story_id in self.stories:
            story = self.stories[story_id]
            story.total_chapters = len(self.story_chapter_map[story_id])
            story.word_count -= chapter.word_count
            story.updated_at = datetime.now().isoformat()

        self._on_story_state_change(story_id)
        return True

    def reorder_chapters(self, story_id: str, new_order: List[str]) -> bool:
        """
        重新排序章节
        """
        if story_id not in self.story_chapter_map:
            return False

        # 验证所有章节ID都存在于故事中
        existing_chapters = set(self.story_chapter_map[story_id])
        new_chapters = set(new_order)
        if not new_chapters.issubset(existing_chapters):
            return False

        # 检查是否遗漏了现有章节
        if not existing_chapters.issubset(new_chapters):
            return False

        # 重新排序
        self.story_chapter_map[story_id] = new_order
        self.stories[story_id].updated_at = datetime.now().isoformat()

        self._on_story_state_change(story_id)
        return True

    def bulk_update_chapters(self, updates: List[Dict[str, Any]]) -> List[ChapterState]:
        """
        批量更新多个章节
        """
        updated_chapters = []
        for update_data in updates:
            chapter_id = update_data.get("chapter_id")
            if chapter_id and chapter_id in self.chapters:
                chapter = self.chapters[chapter_id]

                # 更新允许的字段
                for field in ["title", "content", "status", "metadata"]:
                    if field in update_data:
                        setattr(chapter, field, update_data[field])

                chapter.updated_at = datetime.now().isoformat()
                updated_chapters.append(chapter)

        return updated_chapters