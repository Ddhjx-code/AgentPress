"""
章节分析器模块

功能:
- 聚合同一章节下所有段落的分析结果
- 生成章节级摘要（节奏、主题、情绪、技巧集中度）
- 为全书结构分析提供中间层数据
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .base import KnowledgeEntry
from .literary_analyzer import LiteraryAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChapterSummary:
    """章节摘要数据结构"""
    chapter_title: str
    paragraphs_count: int
    main_themes: List[str]  # 主要主题
    emotional_arc: List[Dict[str, Any]]  # 情绪弧线（段落位置->情绪值）
    rhythm_pattern: List[Dict[str, Any]]  # 节奏模式（紧张度、速度变化）
    literary_techniques: List[str]  # 使用的技巧
    character_development_notes: List[str]  # 角色发展
    section_transitions: List[str]  # 段落间过渡特色
    total_analysis: str  # 章节级分析总评


class ChapterAnalyzer:
    """章节分析器 - 聚合段落分析，生成章节摘要"""

    def __init__(self, literary_analyzer: LiteraryAnalyzer):
        self.literary_analyzer = literary_analyzer

    async def generate_chapter_summary(
        self,
        chapter_title: str,
        paragraph_entries: List[KnowledgeEntry]
    ) -> ChapterSummary:
        """
        生成章节摘要

        Args:
            chapter_title: 章节标题
            paragraph_entries: 该章节所有段落分析结果

        Returns:
            章节摘要对象
        """
        logger.info(f"为章节 '{chapter_title}' 生成摘要，共 {len(paragraph_entries)} 个段落")

        # 1. 提取并聚合主题
        themes = await self._aggregate_themes(paragraph_entries)

        # 2. 分析情绪弧线
        emotional_arc = await self._analyze_emotional_arc(paragraph_entries)

        # 3. 分析节奏模式
        rhythm_pattern = await self._analyze_rhythm_pattern(paragraph_entries)

        # 4. 汇总文学技巧
        techniques = await self._aggregate_techniques(paragraph_entries)

        # 5. 分析角色发展
        character_notes = await self._analyze_character_development(paragraph_entries)

        # 6. 分析段落间过渡
        transitions = await self._analyze_transitions(paragraph_entries)

        # 7. 生成章节级综合分析
        total_analysis = await self._generate_chapter_analysis(
            chapter_title, paragraph_entries, themes, emotional_arc, rhythm_pattern
        )

        return ChapterSummary(
            chapter_title=chapter_title,
            paragraphs_count=len(paragraph_entries),
            main_themes=themes,
            emotional_arc=emotional_arc,
            rhythm_pattern=rhythm_pattern,
            literary_techniques=techniques,
            character_development_notes=character_notes,
            section_transitions=transitions,
            total_analysis=total_analysis
        )

    async def _aggregate_themes(self, paragraph_entries: List[KnowledgeEntry]) -> List[str]:
        """聚合段落中的主要主题"""
        all_themes = set()

        for entry in paragraph_entries:
            # 尝试从分析结果中提取主题关键词
            content = entry.content.lower()
            # 这里可以根据分析文本中的关键词来推断主题
            if '人物' in content or '角色' in content:
                all_themes.add('人物刻画')
            if '对话' in content:
                all_themes.add('对话技巧')
            if '情感' in content or '情绪' in content:
                all_themes.add('情感表达')
            if '节奏' in content or '推进' in content:
                all_themes.add('叙事节奏')
            if '冲突' in content or '矛盾' in content:
                all_themes.add('冲突发展')
            if '悬念' in content or '神秘' in content:
                all_themes.add('悬念设置')

        # 使用AI分析来获取更多隐藏主题
        if paragraph_entries:
            sample_content = " ".join([entry.content[:200] for entry in paragraph_entries[:5]])
            try:
                theme_analysis = await self.literary_analyzer._get_ai_response(
                    f"基于以下文本片段，总结最主要的3个主题或中心内容：\n\n{sample_content[:1000]}"
                )
                for word in ['主题', '主题是', '核心是']:
                    if word in theme_analysis:
                        # 简单提取主要主题词
                        lines = theme_analysis.split('\n')
                        for line in lines:
                            if any(t in line for t in ['人物', '故事', '情节', '环境', '心理', '成长']):
                                cleaned_topic = line.replace(':', '').strip()
                                if cleaned_topic and len(cleaned_topic) < 15:
                                    all_themes.add(cleaned_topic)
            except:
                pass

        return list(all_themes)

    async def _analyze_emotional_arc(self, paragraph_entries: List[KnowledgeEntry]) -> List[Dict[str, Any]]:
        """分析章节内的情绪弧线"""
        emotional_arc = []

        for i, entry in enumerate(paragraph_entries):
            # 基于内容判断情绪强度和类型
            content = entry.content.lower()

            # 简单的情绪判断（可基于AI分析结果优化）
            stress_level = 0  # 0-10的紧张度
            emotion_type = "neutral"

            # 检查一些情绪相关关键词
            if any(w in content for w in ['紧张', '冲突', '战斗', '争斗', '战斗', '危险', '恐惧']):
                stress_level = 8
                emotion_type = 'high_tension'
            elif any(w in content for w in ['平静', '安稳', '安宁', '宁静', '和谐']):
                stress_level = 3
                emotion_type = 'calm'
            elif any(w in content for w in ['悲伤', '忧郁', '哀伤', '失望', '沮丧']):
                stress_level = 5
                emotion_type = 'sad_emo'
            elif any(w in content for w in ['兴奋', '激动', '欢乐', '愉快', '快乐']):
                stress_level = 7
                emotion_type = 'excitement'
            elif any(w in content for w in ['神秘', '悬疑', '未知', '谜团', '探索']):
                stress_level = 6
                emotion_type = 'intrigue'
            else:
                stress_level = 5
                emotion_type = 'steady'

            emotional_arc.append({
                'paragraph_index': i,
                'stress_level': stress_level,
                'emotion_type': emotion_type,
                'content_summary': entry.title[:20] if len(entry.title) < 20 else entry.title[:20] + "..."
            })

        return emotional_arc

    async def _analyze_rhythm_pattern(self, paragraph_entries: List[KnowledgeEntry]) -> List[Dict[str, Any]]:
        """分析章节内的节奏模式"""
        rhythm_pattern = []

        for i, entry in enumerate(paragraph_entries):
            content = entry.content.lower()

            # 简单节奏分析（可优化为基于AI分析结果）
            pace = "medium"  # fast/medium/slow
            tension_change = "stable"  # increase/decrease/stable

            # 确定节奏特征
            if any(word in content for word in ['迅速', '立即', '马上', '快速', '疾速', '飞快']):
                pace = "fast"
            elif any(word in content for word in ['缓慢', '慢慢', '徐徐', '渐渐', '悠然']):
                pace = "slow"
            else:
                pace = "medium"

            # 确定紧张度变化
            if any(word in content for word in ['紧张', '冲突', '加剧', '升级', '升级']):
                tension_change = "increase"
            elif any(word in content for word in ['缓和', '平静', '缓解', '消失', '降低']):
                tension_change = "decrease"
            else:
                tension_change = "stable"

            rhythm_pattern.append({
                'index': i,
                'pace': pace,
                'tension_change': tension_change,
                'technical_notes': f"段落{i+1}节拍: {pace}, 张力{tension_change}"
            })

        return rhythm_pattern

    async def _aggregate_techniques(self, paragraph_entries: List[KnowledgeEntry]) -> List[str]:
        """汇总章节使用的文学技巧"""
        techniques = set()

        for entry in paragraph_entries:
            content = entry.content.lower()

            # 从标签和内容中提取技巧
            for tag in entry.tags:
                if 'technique' in tag or len(tag) < 20:  # 合理的技巧标签
                    techniques.add(tag.replace('-', ' '))

            # 从内容中识别技巧关键字
            if '比喻' in content:
                techniques.add('比喻/类比')
            if '对比' in content:
                techniques.add('对比/对照')
            if '象征' in content:
                techniques.add('象征/比喻')
            if '悬念' in content:
                techniques.add('悬念设置')
            if '伏笔' in content:
                techniques.add('伏笔铺垫')
            if '重复' in content:
                techniques.add('重复强调')
            if '反问' in content:
                techniques.add('反问修辞')
            if '设问' in content:
                techniques.add('设问技巧')
            if '对话' in content:
                techniques.add('对话推进')

        # 如果段落数量较多，可调用AI进行技巧总结
        if len(paragraph_entries) > 5:
            sample_content = " ".join([entry.content[:100] for entry in paragraph_entries[:3]]) + \
                           " [...更多内容...]"
            try:
                tech_summary = await self.literary_analyzer._get_ai_response(
                    f"基于以下文本内容，总结这章节主要采用的文学技巧：\n\n{sample_content}"
                )

                # 提取技巧关键词
                tech_keywords = ['比喻', '拟人', '排比', '对比', '象征', '伏笔', '悬念', '对偶',
                               '设问', '反问', '夸张', '反复', '借代', '通感', '移情']
                for keyword in tech_keywords:
                    if keyword in tech_summary:
                        techniques.add(keyword.replace('设问', '设问/反问'))

            except Exception:
                pass  # 忽略AI分析错误，使用基础提取方法

        return list(techniques)

    async def _analyze_character_development(self, paragraph_entries: List[KnowledgeEntry]) -> List[str]:
        """分析章节角色发展情况"""
        character_notes = []

        # 搜集所有角色相关分析
        for entry in paragraph_entries:
            if any(tag in ['character-development', 'character-portrayal'] for tag in entry.tags):
                content = entry.content
                if len(content) > 20:  # 添加有意义的内容
                    summary = f"角色：{content[:80]}..." if len(content) > 80 else content
                    character_notes.append(summary)

        # 如果没有专门的角色条目，从内容中提取角色相关主题
        if not character_notes and len(paragraph_entries) > 2:
            char_analysis = " ".join([entry.content for entry in paragraph_entries])
            try:
                response = await self.literary_analyzer._get_ai_response(
                    f"分析以下章节内容中的角色塑造情况，包括性格表现、心理变化等：\n\n{char_analysis[:1500]}"
                )
                if response and '角色' in response or '人物' in response:
                    character_notes.append(response)
            except:
                pass

        return character_notes

    async def _analyze_transitions(self, paragraph_entries: List[KnowledgeEntry]) -> List[str]:
        """分析段落间的转换模式"""
        transitions = []

        if len(paragraph_entries) > 1:
            sample_comparison = f"前段：{paragraph_entries[0].content[:100]}\n后段：{paragraph_entries[-1].content[:100]}"

            try:
                transition_analysis = await self.literary_analyzer._get_ai_response(
                    f"分析以下两个段落之间的过渡方式和逻辑衔接：\n\n{sample_comparison}\n\n重点关注转换手法、连接技巧以及情节发展连续性。"
                )

                if transition_analysis:
                    transitions.append(transition_analysis)
            except:
                pass

        if not transitions and len(paragraph_entries) > 3:
            # 添加一个通用过渡描述
            all_content = " ".join([e.content for e in paragraph_entries])
            has_transition = any(word in all_content for word in ['接着', '然后', '突然', '于是', '之后', '此时'])
            if has_transition:
                transitions.append("章节内部结构连贯，转换自然")

        return transitions

    async def _generate_chapter_analysis(
        self,
        chapter_title: str,
        paragraph_entries: List[KnowledgeEntry],
        themes: List[str],
        emotional_arc: List[Dict],
        rhythm_pattern: List[Dict]
    ) -> str:
        """生成章节级综合分析"""
        try:
            sample_for_analysis = " ".join([e.content for e in paragraph_entries if e.content][:3])
            response = await self.literary_analyzer._get_ai_response(
                f"""请对以下章节进行整体评估：

章节：{chapter_title}
内容：{sample_for_analysis}

主要主题：{', '.join(themes)}
情绪走势：{' → '.join([item.get('emotion_type', 'neutral') for item in emotional_arc])}
节奏特点：{' → '.join(list(set([item.get('pace', '') for item in rhythm_pattern])))}

给出章节的总体文学价值评价。"""
            )
            return response
        except:
            # 降级返回基础分析
            return f"章节'{chapter_title}'分析：共包含{len(paragraph_entries)}段内容，主要主题为：{', '.join(themes[:3])}"