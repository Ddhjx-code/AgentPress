"""
跨章节连续性管理器
- 确保故事在不同章节间保持一致性
- 跟踪角色、事件、设定等元素的连续性
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from core.agent_manager import AgentManager


class ContinuityManager:
    """
    连续性管理器
    - 跟踪故事内各种元素的一致性
    - 与AI代理合作检测不一致之处
    """

    def __init__(self, agent_manager: Optional[AgentManager] = None):
        self.agent_manager = agent_manager
        self.story_elements = {
            "characters": {},
            "locations": {},
            "events": {},
            "rules": {},
            "timeline": []
        }
        self.chapter_snapshots = {}  # 每章的快照
        self.inconsistencies = []    # 记录发现的不一致
        self.summary = ""            # 当前的故事摘要

    async def update_for_chapter(self, chapter_content: str, chapter_info: Dict[str, Any]):
        """
        更新连续性跟踪器以包括新章节
        """
        chapter_num = chapter_info.get("chapter_num", len(self.chapter_snapshots) + 1)

        # 保存章节快照
        self.chapter_snapshots[chapter_num] = {
            "content": chapter_content,
            "timestamp": chapter_info.get("timestamp"),
            "elements": {},
            "title": chapter_info.get("title", f"第{chapter_num}章")
        }

        # 提取当前章节的关键元素
        if self.agent_manager:
            await self._extract_with_ai(chapter_content, chapter_num)
        else:
            self._extract_locally(chapter_content, chapter_num)

    def _extract_locally(self, chapter_content: str, chapter_num: int):
        """
        本地提取关键元素（当AI不可用时）
        """
        # 简单的关键字提取实现
        content_lower = chapter_content.lower()

        # 简单的角色提取（通常名字会出现多次）
        potential_names = self._extract_potential_names(chapter_content)
        for name in potential_names:
            if name not in self.story_elements["characters"]:
                self.story_elements["characters"][name] = {
                    "first_mentioned": chapter_num,
                    "last_mentioned": chapter_num,
                    "description": f"角色: {name} (在第{chapter_num}章中首次提及)"
                }
            else:
                self.story_elements["characters"][name]["last_mentioned"] = chapter_num

        # 事件提取（基于特定动词模式）
        events = self._extract_events(chapter_content)
        for event in events:
            event_id = f"{chapter_num}_{event.replace(' ', '_')}"
            if event_id not in self.story_elements["events"]:
                self.story_elements["events"][event_id] = {
                    "event": event,
                    "chapter": chapter_num,
                    "description": event
                }

    async def _extract_with_ai(self, chapter_content: str, chapter_num: int):
        """
        使用AI提取关键元素
        """
        doc_agent = self.agent_manager.get_agent("documentation_specialist")
        if not doc_agent:
            self._extract_locally(chapter_content, chapter_num)
            return

        # 分析章节内容的各个部分
        ai_tasks = [
            self._ai_extract_characters(chapter_content, doc_agent),
            self._ai_extract_locations(chapter_content, doc_agent),
            self._ai_extract_events(chapter_content, doc_agent),
            self._ai_extract_rules_and_settings(chapter_content, doc_agent)
        ]

        try:
            results = await asyncio.gather(*ai_tasks, return_exceptions=True)

            if not isinstance(results[0], Exception) and results[0]:
                self._update_characters(results[0], chapter_num)

            if not isinstance(results[1], Exception) and results[1]:
                self._update_locations(results[1], chapter_num)

            if not isinstance(results[2], Exception) and results[2]:
                self._update_events(results[2], chapter_num)

            if not isinstance(results[3], Exception) and results[3]:
                self._update_rules(results[3], chapter_num)

        except Exception as e:
            print(f"AI分析出错，使用本地分析: {e}")
            self._extract_locally(chapter_content, chapter_num)

    async def _ai_extract_characters(self, content: str, agent) -> Optional[Dict[str, Any]]:
        """
        使用AI提取角色信息
        """
        task = f"""
        从以下章节内容中提取角色信息:

        {content[:2000]}

        请返回JSON，包含角色姓名、描述和关键特征:
        {{
            "characters": [
                {{
                    "name": "",
                    "description": "",
                    "traits": [],
                    "role": ""
                }}
            ]
        }}
        """

        try:
            result = await agent.run(task=task)
            content_text = self._extract_json_content(result.messages)
            if content_text and 'characters' in content_text and content_text['characters']:
                return {"characters": content_text['characters']}
        except Exception as e:
            print(f"角色提取出错: {e}")

        return None

    async def _ai_extract_locations(self, content: str, agent) -> Optional[Dict[str, Any]]:
        """
        使用AI提取地点信息
        """
        task = f"""
        从以下章节内容中提取地点信息:

        {content[:2000]}

        请返回JSON，包含地点名称和描述:
        {{
            "locations": [
                {{
                    "name": "",
                    "description": "",
                    "features": []
                }}
            ]
        }}
        """

        try:
            result = await agent.run(task=task)
            content_text = self._extract_json_content(result.messages)
            if content_text and 'locations' in content_text and content_text['locations']:
                return {"locations": content_text['locations']}
        except Exception as e:
            print(f"地点提取出错: {e}")

        return None

    async def _ai_extract_events(self, content: str, agent) -> Optional[Dict[str, Any]]:
        """
        使用AI提取事件信息
        """
        task = f"""
        从以下章节内容中提取重要事件:

        {content[:2000]}

        请返回JSON，包含事件标题和描述:
        {{
            "events": [
                {{
                    "title": "",
                    "description": "",
                    "significance": "low|medium|high"
                }}
            ]
        }}
        """

        try:
            result = await agent.run(task=task)
            content_text = self._extract_json_content(result.messages)
            if content_text and 'events' in content_text and content_text['events']:
                return {"events": content_text['events']}
        except Exception as e:
            print(f"事件提取出错: {e}")

        return None

    async def _ai_extract_rules_and_settings(self, content: str, agent) -> Optional[Dict[str, Any]]:
        """
        使用AI提取规则和设定信息
        """
        task = f"""
        从以下章节内容中提取世界观规则和设定:

        {content[:2000]}

        请返回JSON，包含世界规则、能力体系、特殊设定等:
        {{
            "rules": [
                {{
                    "name": "",
                    "description": "",
                    "type": "magic|ability|world-rule|custom"
                }}
            ]
        }}
        """

        try:
            result = await agent.run(task=task)
            content_text = self._extract_json_content(result.messages)
            if content_text and 'rules' in content_text and content_text['rules']:
                return {"rules": content_text['rules']}
        except Exception as e:
            print(f"规则提取出错: {e}")

        return None

    def _update_characters(self, extracted_data: Dict[str, Any], chapter_num: int):
        """
        更新角色信息
        """
        for char_data in extracted_data.get("characters", []):
            name = char_data.get("name", "")
            if name:
                if name not in self.story_elements["characters"]:
                    self.story_elements["characters"][name] = {
                        "first_mentioned": chapter_num,
                        "last_mentioned": chapter_num,
                        "description": char_data.get("description", ""),
                        "traits": char_data.get("traits", []),
                        "role": char_data.get("role", ""),
                        "history": [f"第{chapter_num}章: {char_data.get('description', '')}"]
                    }
                else:
                    # 更新角色信息
                    existing_char = self.story_elements["characters"][name]
                    existing_char["last_mentioned"] = chapter_num
                    if char_data.get("description") != existing_char["description"]:
                        existing_char["history"].append(f"第{chapter_num}章: 角色描述更新 - {char_data.get('description', '')}")
                        existing_char["description"] = char_data.get("description", "")
                    for trait in char_data.get("traits", []):
                        if trait not in existing_char["traits"]:
                            existing_char["traits"].append(trait)

    def _update_locations(self, extracted_data: Dict[str, Any], chapter_num: int):
        """
        更新地点信息
        """
        for location_data in extracted_data.get("locations", []):
            name = location_data.get("name", "")
            if name:
                if name not in self.story_elements["locations"]:
                    self.story_elements["locations"][name] = {
                        "first_mentioned": chapter_num,
                        "last_mentioned": chapter_num,
                        "description": location_data.get("description", ""),
                        "features": location_data.get("features", []),
                        "history": [f"第{chapter_num}章: {location_data.get('description', '')}"]
                    }
                else:
                    existing_location = self.story_elements["locations"][name]
                    existing_location["last_mentioned"] = chapter_num
                    # 在这个简单的实现中，我们不会自动更新地点描述
                    # 更复杂的实现可能会合并新的信息

    def _update_events(self, extracted_data: Dict[str, Any], chapter_num: int):
        """
        更新事件信息
        """
        for event_data in extracted_data.get("events", []):
            title = event_data.get("title", "")
            if title:
                event_key = f"{title.lower().replace(' ', '_')}"
                if event_key not in self.story_elements["events"]:
                    self.story_elements["events"][event_key] = {
                        "title": title,
                        "chapter": chapter_num,
                        "description": event_data.get("description", ""),
                        "significance": event_data.get("significance", "medium")
                    }

    def _update_rules(self, extracted_data: Dict[str, Any], chapter_num: int):
        """
        更新规则信息
        """
        for rule_data in extracted_data.get("rules", []):
            name = rule_data.get("name", "")
            if name:
                if name not in self.story_elements["rules"]:
                    self.story_elements["rules"][name] = {
                        "first_mentioned": chapter_num,
                        "description": rule_data.get("description", ""),
                        "type": rule_data.get("type", "world-rule"),
                        "history": [f"第{chapter_num}章: {rule_data.get('description', '')}"]
                    }

    def _extract_potential_names(self, text: str) -> List[str]:
        """
        本地提取潜在角色名称
        """
        # 简单实现：查找出现多次的中文名词
        import re
        # 这是一个非常简单的实现，真实实现会更复杂
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        from collections import Counter
        word_counts = Counter(words)
        return [word for word, count in word_counts.items() if count > 1]

    def _extract_events(self, text: str) -> List[str]:
        """
        本地提取潜在事件
        """
        # 简单提取包含特定动词短语的句子
        import re
        sentences = re.split(r'[。！？\n]', text)
        key_actions = ["出现", "发生", "导致", "引起", "发生", "改变", "决定"]
        events = []

        for sent in sentences:
            if any(action in sent for action in key_actions):
                events.append(sent.strip())

        return events

    def _extract_json_content(self, messages: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        从AI消息中提取JSON内容
        """
        for message in reversed(messages):
            if isinstance(message, dict):
                if 'content' in message:
                    content = message['content']
                    # 尝试提取JSON
                    start_idx = content.find('{')
                    if start_idx != -1:
                        end_idx = content.rfind('}') + 1
                        if end_idx > start_idx:
                            try:
                                json_str = content[start_idx:end_idx]
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                # 如果解析失败，尝试解析更宽泛的JSON内容
                                lines = content.split('\n')
                                for line in lines:
                                    line_clean = line.strip().rstrip('`')
                                    if line_clean.startswith('{') and '}' in line_clean:
                                        try:
                                            return json.loads(line_clean)
                                        except json.JSONDecodeError:
                                            continue

        return None

    async def check_continuity(self, chapter_content: str, chapter_num: int) -> Dict[str, Any]:
        """
        检查新章节内容与之前章节的连续性
        """
        inconsistencies = []
        warnings = []

        if self.agent_manager:
            doc_agent = self.agent_manager.get_agent("documentation_specialist")
            if doc_agent:
                inconsistencies, warnings = await self._ai_check_continuity(
                    chapter_content, chapter_num, doc_agent
                )

        # 如果没有AI或者AI检查失败，则使用简单的模式匹配检查
        if not inconsistencies:
            local_inconsistencies = self._simple_continuity_check(chapter_content, chapter_num)
            inconsistencies.extend(local_inconsistencies)

        self.inconsistencies.extend(inconsistencies)

        return {
            "inconsistencies": inconsistencies,
            "warnings": warnings,
            "continuity_score": len(inconsistencies),  # 得分越低越好
            "summary": f"第{chapter_num}章连续性检查：发现{len(inconsistencies)}个不一致，{len(warnings)}个警告"
        }

    async def _ai_check_continuity(self, content: str, chapter_num: int, agent) -> tuple:
        """
        使用AI检查连续性
        """
        all_content = ""
        previous_chapters = [ch for num, ch in self.chapter_snapshots.items() if num < chapter_num]

        if previous_chapters:
            all_content = "\n\n".join([f"第{ch_num}章: {ch['content'][:500]}"
                                     for ch_num, ch in sorted(self.chapter_snapshots.items())
                                     if ch_num < chapter_num])

        task = f"""
        请检查新章节内容与之前故事内容的连续性:

        【已有故事概要】
        {all_content}

        【当前章节内容】
        {content[:2000]}

        请识别任何可能的不一致之处或矛盾，并返回JSON:
        {{
            "inconsistencies": [
                {{
                    "type": "character|location|event|timeline|rule",
                    "element": "",
                    "issue": "具体问题描述",
                    "severity": "low|medium|high",
                    "suggestion": "修正建议"
                }}
            ],
            "warnings": [
                {{
                    "type": "potential_new_element|timeline_gap|etc",
                    "description": "潜在问题描述"
                }}
            ]
        }}
        """

        try:
            result = await agent.run(task=task)
            analysis = self._extract_json_content(result.messages)

            if analysis:
                return (analysis.get("inconsistencies", []),
                       analysis.get("warnings", []))
        except Exception as e:
            print(f"AI连续性检查出错: {e}")

        return ([], [])

    def _simple_continuity_check(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """
        简单的连续性检查，基于已知元素
        """
        inconsistencies = []
        content_lower = content.lower()

        # 检查角色前后不一致
        for char_name, char_info in self.story_elements["characters"].items():
            if char_info["last_mentioned"] < chapter_num - 1:  # 隔章出现
                if char_name.lower() in content_lower and char_info.get("needs_background", False):
                    inconsistencies.append({
                        "type": "character",
                        "element": char_name,
                        "issue": f"角色 {char_name} 隔了多章后出现，但没有背景介绍",
                        "severity": "medium",
                        "suggestion": f"考虑在重新引入角色 {char_name} 时加上简单的背景说明"
                    })

        # 更多简单检查可在这里添加

        return inconsistencies

    def get_continuity_report(self) -> Dict[str, Any]:
        """
        生成连续性报告
        """
        total_chapters = len(self.chapter_snapshots)
        inconsistent_chapters = set()
        for issue in self.inconsistencies:
            inconsistent_chapters.add(issue.get("chapter", 0))

        return {
            "total_chapters": total_chapters,
            "inconsistent_chapters_count": len(inconsistent_chapters),
            "total_issues_count": len(self.inconsistencies),
            "inconsistency_rate": len(self.inconsistencies) / max(total_chapters, 1),
            "issues_by_type": self._categorize_issues(self.inconsistencies),
            "story_elements": self.story_elements,
            "element_counts": {k: len(v) if isinstance(v, dict) else len(v) for k, v in self.story_elements.items()}
        }

    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        按类型对问题进行分类计数
        """
        categories = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            categories[issue_type] = categories.get(issue_type, 0) + 1
        return categories