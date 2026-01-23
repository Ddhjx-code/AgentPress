"""
动态章节决策引擎
- 让AI根据故事内容自然地决定何时章节结束
- 替代硬编码的章节数量设置
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from core.agent_manager import AgentManager


class ChapterDecisionEngine:
    """
    章节决策引擎
    - 基于故事内容自动判断章节结束时机
    - 与writer agent协作确定分章点
    - 提供动态章节规划
    """

    def __init__(self, agent_manager: Optional[AgentManager] = None):
        self.agent_manager = agent_manager
        self.current_chapter_info = []
        self.chapter_ending_signals = [
            '完成了阶段性冲突',
            '达到了关键情节节点',
            '完成了关键人物刻画',
            '故事张力得到释放',
            '达到了合适的自然停顿点',
            '本段情节已完整表述'
        ]

    async def should_end_chapter(self, current_content: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于当前内容和研究数据判断是否应该结束章节
        """
        if not self.agent_manager:
            # 如果没有AI agent，则基于字数和内容长度做简单判断
            return self._fallback_chapter_decision(current_content)

        writer = self.agent_manager.get_agent("writer")
        if not writer:
            return self._fallback_chapter_decision(current_content)

        # 分析当前内容以判断章节结束时机
        task_prompt = f"""
        作为经验丰富的作家和故事结构专家，请分析以下故事段落：

        【当前内容】
        {current_content[-2000:]}  # 只传最后2000字，避免过大输入

        【研究数据】
        {json.dumps(research_data, ensure_ascii=False, indent=2)[:500]}

        请判断现在是否是合适的章节结束时机：
        1. 当前段落是否完成了一个相对完整的情节或冲突？
        2. 情节张力是否达到了可以暂时停顿的点？
        3. 故事节奏是否适合章节分割？

        返回一个JSON格式的对象：
        {{
            "should_end": boolean,
            "confidence": float between 0-1,
            "reasoning": "详细的判断理由",
            "suggested_title": "建议的章节标题",
            "next_chapter_hint": "下一章的可能发展方向"
        }}
        """

        try:
            result = await writer.run(task=task_prompt)
            analysis = self._extract_json_content(result.messages)

            if analysis and 'should_end' in analysis:
                decision = {
                    "should_end": analysis["should_end"],
                    "confidence": analysis.get("confidence", 0.0),
                    "reasoning": analysis.get("reasoning", "AI分析结果"),
                    "suggested_title": analysis.get("suggested_title", f"第{len(self.current_chapter_info)+1}章"),
                    "next_chapter_hint": analysis.get("next_chapter_hint", ""),
                    "current_chapter_num": len(self.current_chapter_info) + 1
                }
                return decision
            else:
                # 如果AI没有返回正确格式，执行备选方案
                return self._fallback_chapter_decision(current_content)

        except Exception as e:
            print(f"章节决策AI分析出错: {e}")
            return self._fallback_chapter_decision(current_content)

    def _fallback_chapter_decision(self, current_content: str) -> Dict[str, Any]:
        """
        当AI不可用时的备选章节决策
        """
        current_length = len(current_content)

        # 大约每2000-3000字建议分章一次，但要基于内容
        # 如果超过3000字且当前内容有段落结尾迹象，建议分章
        should_end = False
        if current_length > 2500:
            # 检查是否在段落结尾
            last_100_chars = current_content[-100:] if len(current_content) >= 100 else current_content
            if last_100_chars.count("\n") >= 1:  # 有几个换行符可能表示段落结束
                should_end = True

        return {
            "should_end": should_end,
            "confidence": 0.5,  # 默认置信度
            "reasoning": f"基于字数和结构的备选决策 (长度: {current_length} 字符)",
            "suggested_title": f"第{len(self.current_chapter_info)+1}章",
            "next_chapter_hint": "根据故事发展确定",
            "current_chapter_num": len(self.current_chapter_info) + 1
        }

    async def create_chapter_outline(self, overall_idea: str) -> List[Dict[str, Any]]:
        """
        创建动态章节大纲（AI根据整体创意推断可能的章节划分）
        """
        outline = []
        if not self.agent_manager:
            # 如果缺乏AI支持，创建基础大纲
            outline.append({
                "chapter_num": 1,
                "title": "开篇",
                "content_summary": f"基于 {overall_idea} 的开篇内容",
                "length_hint": "800-1500字",
                "key_elements": []
            })
        else:
            mythologist = self.agent_manager.get_agent("mythologist")
            if mythologist:
                try:
                    outline_task = f"""
                    基于以下创意构思，动态设计一个分章计划（请不要强制指定章节数）：

                    创意构思: {overall_idea}

                    分析该故事的自然分段点，考虑：
                    - 情节的自然起承转合
                    - 冲突与解决的循环周期
                    - 每章的紧凑程度和可读性

                    请返回JSON格式的章节大纲，不要设置固定的章节数量，
                    而是基于故事内容的自然分割：
                    {{
                        "dynamic_chapters": [
                            {{
                                "title": "章节标题",
                                "summary": "章节内容摘要",
                                "key_elements": ["关键元素1", "关键元素2"],
                                "expected_tension": "章节末期的张力状态（高潮/平缓/悬念等）"
                            }}
                        ]
                    }}
                    """

                    result = await mythologist.run(task=outline_task)
                    analysis = self._extract_json_content(result.messages)

                    if analysis and 'dynamic_chapters' in analysis:
                        for i, chapter_data in enumerate(analysis['dynamic_chapters'], 1):
                            outline.append({
                                "chapter_num": i,
                                "title": chapter_data.get("title", f"第{i}章"),
                                "content_summary": chapter_data.get("summary", f"第{i}章内容"),
                                "key_elements": chapter_data.get("key_elements", []),
                                "expected_tension": chapter_data.get("expected_tension", "平衡")
                            })
                    else:
                        # AI未能返回正确格式，使用默认大纲
                        outline.append({
                            "chapter_num": 1,
                            "title": "开篇",
                            "content_summary": f"基于 {overall_idea} 的开篇内容",
                            "key_elements": [],
                            "expected_tension": "引入"
                        })
                except Exception as e:
                    print(f"AI章节大纲生成出错: {e}")
                    outline.append({
                        "chapter_num": 1,
                        "title": "开篇",
                        "content_summary": f"基于 {overall_idea} 的开篇内容",
                        "key_elements": [],
                        "expected_tension": "引入"
                    })

        return outline

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

    async def evaluate_overall_progress(self, current_chapters: List[str], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估整体创作进度和接下来的创作方向
        """
        total_chars = sum(len(chap) for chap in current_chapters)

        if not self.agent_manager:
            return {
                "story_progress_ratio": len(current_chapters) / 3,  # 默认3章比例
                "estimated_remaining_parts": max(1, 3 - len(current_chapters)),
                "is_continuing": len(current_chapters) < 5,  # 简单限制最多5章
                "summary": f"已完成{len(current_chapters)}章，共计{total_chars}字"
            }

        editor = self.agent_manager.get_agent("editor")
        if not editor:
            return {
                "story_progress_ratio": len(current_chapters) / 3,
                "estimated_remaining_parts": max(1, 3 - len(current_chapters)),
                "is_continuing": len(current_chapters) < 5,
                "summary": f"已完成{len(current_chapters)}章，共计{total_chars}字"
            }

        task_prompt = f"""
        评估以下创作项目的总体进展：

        【已完成章节数量】{len(current_chapters)}
        【总字数】{total_chars}
        【原始创意】{research_data}

        考虑以下方面进行评估：
        1. 故事情节已经发展到什么程度
        2. 是否需要继续创作更多内容来完善故事
        3. 故事当前阶段的情节完成度和节奏

        返回JSON:
        {{
            "story_progress_ratio": 0-1之间的数值,
            "estimated_remaining_parts": 预估还需多少部分,
            "is_continuing": boolean 是否应继续创作,
            "summary": 总体评估文本描述
        }}
        """

        try:
            result = await editor.run(task=task_prompt)
            analysis = self._extract_json_content(result.messages)

            if analysis:
                return analysis
            else:
                return {
                    "story_progress_ratio": len(current_chapters) / 4,
                    "estimated_remaining_parts": max(3 - len(current_chapters), 0),
                    "is_continuing": len(current_chapters) < 4,
                    "summary": f"已完成{len(current_chapters)}章，共计{total_chars}字，基于内容评估"
                }
        except Exception as e:
            print(f"整体进度评估出错: {e}")
            return {
                "story_progress_ratio": len(current_chapters) / 4,
                "estimated_remaining_parts": max(3 - len(current_chapters), 0),
                "is_continuing": len(current_chapters) < 4,
                "summary": f"已完成{len(current_chapters)}章，共计{total_chars}字"
            }