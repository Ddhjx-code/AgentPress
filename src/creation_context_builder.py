import json
from typing import Dict, List, Any


class CreationContextBuilder:
    """专门构建创作上下文的工具类，从NovelWritingPhases中分离出来"""

    def __init__(self):
        pass

    def build_context_for_chapter_creation(self, chapter_num: int, research_data: Dict,
                                         previous_chapters: List[str], target_length: int,
                                         current_content: str) -> str:
        """为章节创建构建内容创作上下文"""
        context = f"""
第 {chapter_num} 部分创作要求 (动态章节)

【故事研究数据】
{json.dumps(research_data, ensure_ascii=False, indent=2)[:1000]}

【整体进展】
已创作了 {len(previous_chapters)} 个部分内容

【已有内容片段（供参考连贯性）】
"""
        if previous_chapters:
            context += f"...({len(previous_chapters)} 个较早的片段)\n{previous_chapters[-1][-500:]}\n\n"
        else:
            context += "这是开篇内容\n\n"

        # 计算中文汉字数量，提供更准确的字数信息给AI代理
        import re
        chinese_chars_count = len(re.findall(r'[\\u4e00-\\u9fff]', current_content))

        context += f"""
【当前内容长度】
当前总内容长度: {len(current_content)} 总字符 | {chinese_chars_count} 中文汉字

【本段创作要求】
建议长度: {target_length} 中文汉字
- 保持叙述连贯性
- 引入新情节点或发展现有冲突
- 为可能的后续章节创建悬念或自然终结点
- 专注高质量的叙事内容
- 直接输出内容，无需额外说明
"""
        return context

    def build_review_task_context(self, story: str, agent_type: str) -> str:
        """为不同类型的代理构建评审任务上下文"""
        if agent_type == "fact_checker":
            # 判断输入是故事内容还是设定文档，以便fact_checker选择适当的评估模式
            is_setting_text = any(keyword in story.lower() for keyword in ["世界观", "设定", "规则", "体系", "背景"])
            if is_setting_text:
                return f"""
请评估以下世界观设定的内在一致性和可扩展性：

{story[:3000]}

请使用世界观设定评审格式（包含coherence_score, anchored_rules, unanchored_risks等）返回评估结果。
"""
            else:
                return f"""
请评估以下故事片段的逻辑架构：

{story[:3000]}

请使用单段/单章评审格式（包含applied_strategies, logic_gaps, strengths等）返回评估结果。
"""
        elif agent_type == "dialogue_specialist":
            return f"""
请评估以下故事的对话质量、人物语言特色和表达效果：
{story[:3000]}

返回评分和改进建议。
"""
        elif agent_type == "write_enviroment_specialist":
            return f"""
请评估以下故事的环境描写、感官细节和氛围营造效果：
{story[:3000]}

请从以下方面进行评估：
- 环境描写的生动性和具体性
- 五感细节（视觉、听觉、嗅觉、触觉、味觉）的运用
- 场景与情绪的配合程度
- 感官细节是否服务于叙事

返回评分和改进建议。
"""
        elif agent_type == "write_rate_specialist":
            return f"""
请评估以下故事的叙事节奏、情绪曲线和信息安排：
{story[:3000]}

请从以下方面进行评估：
- 叙事节奏的控制（紧缓结合）
- 情绪曲线的设计（起伏变化）
- 信息密度的安排
- 读者注意力的引导效果

返回评分和改进建议。
"""
        else:  # editor
            return f"""
请从整体上评估以下故事的文学质量、情节推进和读者吸引力：
{story[:3000]}

返回评分和改进建议。
"""


class StoryStateHelper:
    """专门处理故事状态管理的助手类"""

    def __init__(self, chapter_decision_engine=None, continuity_manager=None, story_state_manager=None):
        self.chapter_decision_engine = chapter_decision_engine
        self.continuity_manager = continuity_manager
        self.story_state_manager = story_state_manager

    def update_story_state(self, new_content: str, chapter_info: dict, chapter_count: int, research_data: dict=None):
        """更新故事状态和连贯性"""
        # 更新章节决策引擎
        if self.chapter_decision_engine:
            decision = self.chapter_decision_engine.should_end_chapter(new_content, research_data or {})
            chapter_info["decision"] = decision

        # 更新连续性管理器
        if self.continuity_manager:
            self.continuity_manager.update_for_chapter(new_content, chapter_info)

        # 更新故事状态管理器
        if self.story_state_manager:
            self.story_state_manager.create_chapter(
                story_id=chapter_info.get("story_id", "temp_id"),
                title=chapter_info.get("title", f"第{chapter_count}章"),
                content=new_content
            )