"""
文学分析代理模块

功能:
- 使用AI模型分析提取的小说片段
- 识别文学技巧、节奏模式、经典段落
- 生成结构化的知识条目
- 提供对段落内容的深度解读
"""
import logging
from typing import List, Dict, Any, Optional
from .base import KnowledgeEntry
from core.workflow_service import WorkflowService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiteraryAnalyzer:
    """文学分析代理 - 使用AI分析小说内容"""

    def __init__(self, workflow_service: WorkflowService):
        self.workflow_service = workflow_service
        if not workflow_service.model_client:
            raise ValueError("WorkflowService 必须已初始化模型客户端")

        # 从prompts目录加载分析提示词模板
        import os
        from pathlib import Path

        prompts_dir = Path("prompts") if Path("prompts").exists() else Path(__file__).parent.parent / "prompts"

        technique_prompt_path = prompts_dir / "literary_analysis_base.md"
        if technique_prompt_path.exists():
            with open(technique_prompt_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 按照提示词块分割
            sections = {}
            current_section = None
            current_content = ""

            for line in template_content.split('\n'):
                if line.startswith('## '):
                    if current_section:
                        sections[current_section] = current_content.strip()
                    current_section = line[3:].strip().lower().replace(' ', '_')
                    current_content = ""
                else:
                    current_content += line + "\n"

            # 保存最后一个section
            if current_section:
                sections[current_section] = current_content.strip()

            # 设置分析提示词模板
            self.analysis_prompt_templates = {
                "technique_analysis": sections.get("technique_analysis", "请深度分析以下文本片段的文学技巧：\n\n文本内容: {text}\n\n请从以下维度分析：修辞手法, 叙述技巧, 情感表达, 结构布局, 人物塑造。"),
                "rhythm_analysis": sections.get("rhythm_analysis", "请从叙事技巧角度分析以下文本片段的节奏控制:\n\n文本内容: {text}"),
                "classic_paragraph_analysis": sections.get("classic_analysis", "请判断以下段落是否具有经典文学段落的价值：\n\n文本内容: {text}"),
                "character_development_analysis": sections.get("character_analysis", "请分析以下文本片段中的人物塑造艺术：\n\n文本内容: {text}"),
                "dialogue_analysis": sections.get("dialogue_analysis", "请分析以下文本片段中对话的文学技巧：\n\n文本内容: {text}")
            }
        else:
            # 如果提示词文件不存在，使用默认模板
            self.analysis_prompt_templates = {
                "technique_analysis": """请深度分析以下文本片段的文学技巧：

文本内容: {text}

请从以下维度进行分析：
1. 修辞手法 (如比喻、拟人、排比等形象化表达技巧)
2. 叙述技巧 (如视角选择、时间处理、节奏控制、伏笔、铺垫等)
3. 情感表达方法 (如对比、衬托、象征、氛围营造等)
4. 结构布局技巧 (如起承转合、开合呼应、层次推进等)
5. 人物塑造技法 (如外貌描写、心理刻画、对话运用、行为展示等)
6. 语言艺术特色 (如词句选择、语调节奏、风格特点等)

请用中文简洁输出，每项不超过50字。""",

                "rhythm_analysis": """请从叙事技巧角度分析以下文本片段的节奏控制：

文本内容: {text}

请评价：
1. 情节节奏：起承转合、悬念设置、转折安排、情节张力等
2. 信息递进节奏：信息释放的速度与方式，逐步揭示还是突然揭露
3. 情感波动节奏：情绪的起伏变化与控制，铺垫与高潮设计
4. 节奏变化技巧：欲扬先抑、先声夺人、节奏突变等手法

说明：重点关注故事叙述节奏安排、情节推进技巧及情绪控制方法。""",

                "classic_paragraph_analysis": """请判断以下段落是否具有经典文学段落的价值：

文本内容: {text}

判断标准：
1. 是否运用了卓越的文学技巧（如修辞、结构、节奏等）
2. 是否展现了独特的艺术手法或创新性表达
3. 是否体现了深刻的人文思想或哲理内涵
4. 是否具有代表性或典型性的文学意义

请给出明确判断并详细分析其文学价值和技巧亮点。""",

                "character_development_analysis": """请分析以下文本片段中的人物塑造艺术：

文本内容: {text}

分析要点：
1. 人物性格刻画技法 (如外貌、语言、行为、心理等塑造方法)
2. 人物形象的立体性与独特性
3. 人物与情节的关系及推动作用
4. 人物塑造的技巧创新点
5. 人物象征意义或典型性

如果文本中没有明显人物，请说明。""",

                "dialogue_analysis": """请分析以下文本片段中对话的文学技巧：

文本内容: {text}

分析重点：
1. 对话的性格化特征 (体现人物独特语言风格)
2. 对话的戏剧性作用 (推进情节、制造冲突、揭示矛盾)
3. 对话的潜台词技巧 (言外之意、弦外之音)
4. 对话与叙述的配合 (对话与旁白的平衡处理)
5. 对话的节奏控制 (快慢、停顿、交互模式)

如果文本中没有对话，请说明。"""
            }

    async def analyze_paragraph(
        self,
        paragraph_data: Dict,
        source_novel: str
    ) -> Optional[KnowledgeEntry]:
        """
        分析单个段落并生成知识条目

        Args:
            paragraph_data: 段落数据字典
            source_novel: 原始小说名称

        Returns:
            KnowledgeEntry对象或None
        """
        text = paragraph_data['text']
        original_title = paragraph_data.get('original_title', 'Unknown')
        chunk_id = paragraph_data['id']
        chapter_info = paragraph_data.get('chapter_info', {})

        try:
            # 多维度分析
            techniques = await self._analyze_technique(text)
            rhythm = await self._analyze_rhythm(text)
            is_classic, classic_reason = await self._identify_classic_paragraph(text)
            char_dev = await self._analyze_character_development(text)
            dialogue = await self._analyze_dialogue(text)

            # 决定生成什么类型的知识条目
            knowledge_entries = []

            # 根据分析结果创建不同类型的知识条目
            if techniques:
                technique_entry = await self._create_technique_entry(
                    text, techniques, original_title, chunk_id, chapter_info
                )
                knowledge_entries.append(technique_entry)

            if is_classic:
                classic_entry = await self._create_classic_paragraph_entry(
                    text, classic_reason, original_title, chunk_id, chapter_info
                )
                knowledge_entries.append(classic_entry)

            if char_dev and "没有明显人物" not in char_dev:
                char_entry = await self._create_character_entry(
                    text, char_dev, original_title, chunk_id, chapter_info
                )
                knowledge_entries.append(char_entry)

            # 返回最有价值的一个条目
            # 优先返回经典段落，其次技巧条目
            for entry in knowledge_entries:
                if entry.knowledge_type == "classic-paragraph":
                    return entry

            # 如果有技巧条目，返回第一个
            for entry in knowledge_entries:
                if entry.knowledge_type == "novel-technique":
                    return entry

            # 如果有角色条目，返回第一个
            for entry in knowledge_entries:
                if entry.knowledge_type == "character-development":
                    return entry

            # 如果段落包含对话且分析结果有价值，创建对话技巧条目
            if "没有对话" not in dialogue:
                dialogue_entry = await self._create_dialogue_entry(
                    text, dialogue, original_title, chunk_id, chapter_info
                )
                return dialogue_entry

        except Exception as e:
            logger.error(f"分析段落时出错 (ID: {chunk_id}): {str(e)}")
            return None

        return None

    async def _analyze_technique(self, text: str) -> str:
        """分析文本的文学技巧"""
        if len(text.strip()) < 10:
            return ""
        prompt = self.analysis_prompt_templates["technique_analysis"].format(text=text)
        try:
            response = await self._get_ai_response(prompt)
            return response
        except:
            return ""

    async def _analyze_rhythm(self, text: str) -> str:
        """分析文本的节奏"""
        if len(text.strip()) < 20:
            return ""
        prompt = self.analysis_prompt_templates["rhythm_analysis"].format(text=text)
        try:
            response = await self._get_ai_response(prompt)
            return response
        except:
            return ""

    async def _identify_classic_paragraph(self, text: str) -> tuple[bool, str]:
        """判断段落是否是经典段落"""
        if len(text.strip()) < 50:
            return False, "段落长度不足，不构成经典段落。"
        prompt = self.analysis_prompt_templates["classic_paragraph_analysis"].format(text=text)
        try:
            response = await self._get_ai_response(prompt)
            is_classic = "是" in response[:50]  # 检查前50个字符是否包含"是"
            return is_classic, response
        except:
            return False, "分析出错"

    async def _analyze_character_development(self, text: str) -> str:
        """分析文本的人物塑造"""
        if len(text.strip()) < 10:
            return "没有明显人物"
        prompt = self.analysis_prompt_templates["character_development_analysis"].format(text=text)
        try:
            response = await self._get_ai_response(prompt)
            return response
        except:
            return "没有明显人物"

    async def _analyze_dialogue(self, text: str) -> str:
        """分析文本的对话技巧"""
        if len(text.strip()) < 10 or '“' not in text and '"' not in text:
            return "没有对话"
        prompt = self.analysis_prompt_templates["dialogue_analysis"].format(text=text)
        try:
            response = await self._get_ai_response(prompt)
            return response
        except:
            return "没有对话"

    async def _get_ai_response(self, prompt: str) -> str:
        """使用AI模型获取响应"""
        try:
            # 从workflow_service获取已初始化的模型客户端
            model_client = self.workflow_service.model_client

            # 导入所需的消息类型 - 根据autogen_core的实际结构
            from autogen_core.models._types import UserMessage, AssistantMessage, SystemMessage

            # 创建消息列表 - 模型客户端create方法需要messages参数
            # 需要包含source字段解决验证错误
            messages = [
                SystemMessage(
                    content="你是一个资深的文学批评家和写作技巧研究专家，拥有深厚的文学理论知识。你需要深度分析文学作品中的叙事技巧、结构安排、修辞手法、节奏控制等高阶文学技法，并能识别经典段落的文学价值。",
                    source="literary_analyzer_system"
                ),
                UserMessage(
                    content=prompt,
                    source="literary_analyzer_user"
                )
            ]

            # 调用模型客户端生成响应
            result = await model_client.create(
                messages=messages
            )

            # 根据CreateResult对象的结构提取内容
            if hasattr(result, 'output') and result.output:
                # 如果输出有content属性
                if hasattr(result.output, 'content'):
                    return str(result.output.content) if result.output.content else ""
                else:
                    # 直接返回输出
                    return str(result.output)
            elif hasattr(result, 'choices') and len(result.choices) > 0:
                # 如果有选择项（OpenAI兼容格式）
                choice = result.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return str(choice.message.content) if choice.message.content else ""
                else:
                    return str(choice)
            else:
                # 尝试直接转换result对象
                return str(result) if result else ""
        except Exception as e:
            logger.warning(f"AI分析时出错，使用降级处理: {str(e)}")
            # 降级处理时返回一个有意义的默认值，而不是空内容
            return f"分析时遇到技术问题，保留原文内容：{prompt[:100]}...详情: {str(e)}"

    async def _create_technique_entry(
        self,
        text: str,
        technique_analysis: str,
        source_novel: str,
        chunk_id: str,
        chapter_info: Dict
    ) -> KnowledgeEntry:
        """创建文学技巧知识条目"""
        # 只保存分析结果，不保存原文内容（避免重复存储大文本）
        content = f"分析：{technique_analysis}\n\n原文摘录：{text[:200]}..."  # 只保留前200字符作为上下文
        title = f"文学技巧分析 - {source_novel[:20]}..."

        # 为技巧类型生成标签
        tags = ["literary-techniques"]
        if "比喻" in technique_analysis or "拟人" in technique_analysis:
            tags.append("figurative-language")
        if "心理描写" in technique_analysis or "外貌描写" in technique_analysis:
            tags.append("character-portrayal")
        if "视角" in technique_analysis:
            tags.append("narrative-perspective")
        if "对话" in technique_analysis:
            tags.append("dialogue-technique")

        # 添加章节信息作为标签
        if chapter_info:
            chapter_title = chapter_info.get('section_title', '')
            if chapter_title:
                tags.append(chapter_title.replace(' ', '-'))

        import hashlib
        content_hash = hashlib.md5((title + technique_analysis).encode()).hexdigest()  # 使用分析内容而非原文生成哈希

        import datetime
        current_time = datetime.datetime.now().isoformat()

        return KnowledgeEntry(
            id=f"tech_{content_hash}",
            title=title,
            content=content,
            tags=tags,
            source=f"PDF: {source_novel}",
            creation_date=current_time,
            last_modified=current_time,
            knowledge_type="novel-technique",
            chapter_id=chapter_info.get('section_title', 'unknown') if chapter_info else None
        )

    async def _create_classic_paragraph_entry(
        self,
        text: str,
        analysis: str,
        source_novel: str,
        chunk_id: str,
        chapter_info: Dict
    ) -> KnowledgeEntry:
        """创建经典段落知识条目"""
        # 只保存分析结果和少量原文摘录，不保存全部文本
        content = f"评价：{analysis}\n\n段落摘录：{text[:300]}..."  # 只保留前300字符作为示例，避免重复存储大文本
        title = f"经典段落分析 - {source_novel[:20]}..."

        # 为经典段落生成标签
        tags = ["classic-paragraph", "high-quality-writing"]

        # 根据内容推断类型
        if any(word in text for word in ["描写", "描绘", "景色", "环境"]):
            tags.append("descriptive-passages")
        if any(word in text for word in ["对话", "说", "道", "讲"]):
            tags.append("dialogue")
        if any(word in text for word in ["心理", "内心", "想法", "思考"]):
            tags.append("psychological-description")

        # 添加章节信息作为标签
        if chapter_info:
            chapter_title = chapter_info.get('section_title', '')
            if chapter_title:
                tags.append(chapter_title.replace(' ', '-'))

        import hashlib
        content_hash = hashlib.md5((title + text[:100]).encode()).hexdigest()  # 使用少量原文生成哈希避免重复

        import datetime
        current_time = datetime.datetime.now().isoformat()

        return KnowledgeEntry(
            id=f"classic_{content_hash}",
            title=title,
            content=content,
            tags=tags,
            source=f"PDF: {source_novel}",
            creation_date=current_time,
            last_modified=current_time,
            knowledge_type="classic-paragraph",
            chapter_id=chapter_info.get('section_title', 'unknown') if chapter_info else None
        )

    async def _create_character_entry(
        self,
        text: str,
        char_analysis: str,
        source_novel: str,
        chunk_id: str,
        chapter_info: Dict
    ) -> KnowledgeEntry:
        """创建人物塑造知识条目"""
        # 保存分析结果和相关原文摘录，而非全部文本
        content = f"人物分析：{char_analysis}\n\n相关摘录：{text[:300]}..."  # 只保存部分摘录作为上下文
        title = f"人物刻画分析 - {source_novel[:20]}..."

        # 为人物塑造生成标签
        tags = ["character-development", "characterization"]

        # 细化标签
        if "外貌描写" in char_analysis:
            tags.append("physical-description")
        if "心理描写" in char_analysis:
            tags.append("psychological-portrayal")
        if "行为表现" in char_analysis or "动作" in char_analysis:
            tags.append("behavior-description")
        if "语言特点" in char_analysis or "对话" in char_analysis:
            tags.append("verbal-characteristics")

        # 添加章节信息作为标签
        if chapter_info:
            chapter_title = chapter_info.get('section_title', '')
            if chapter_title:
                tags.append(chapter_title.replace(' ', '-'))

        import hashlib
        content_hash = hashlib.md5((title + char_analysis).encode()).hexdigest()  # 使用分析内容生成哈希

        import datetime
        current_time = datetime.datetime.now().isoformat()

        return KnowledgeEntry(
            id=f"char_{content_hash}",
            title=title,
            content=content,
            tags=tags,
            source=f"PDF: {source_novel}",
            creation_date=current_time,
            last_modified=current_time,
            knowledge_type="character-development",
            chapter_id=chapter_info.get('section_title', 'unknown') if chapter_info else None
        )

    async def _create_dialogue_entry(
        self,
        text: str,
        dialogue_analysis: str,
        source_novel: str,
        chunk_id: str,
        chapter_info: Dict
    ) -> KnowledgeEntry:
        """创建对话技巧知识条目"""
        # 保存分析结果和对话摘录，而非全部原文
        content = f"对话分析：{dialogue_analysis}\n\n对话摘录：{text[:300]}..."  # 只保存部分作为示例
        title = f"对话技巧分析 - {source_novel[:20]}..."

        tags = ["dialogue", "dialogue-technique", "conversation"]

        # 根据分析细化标签
        if "个性化" in dialogue_analysis:
            tags.append("character-specific-dialogue")
        if "情境" in dialogue_analysis or "背景" in dialogue_analysis:
            tags.append("contextual-dialogue")
        if "情感" in dialogue_analysis:
            tags.append("emotional-dialogue")

        # 添加章节信息作为标签
        if chapter_info:
            chapter_title = chapter_info.get('section_title', '')
            if chapter_title:
                tags.append(chapter_title.replace(' ', '-'))

        import hashlib
        content_hash = hashlib.md5((title + dialogue_analysis).encode()).hexdigest()  # 使用分析内容生成哈希

        import datetime
        current_time = datetime.datetime.now().isoformat()

        return KnowledgeEntry(
            id=f"dialogue_{content_hash}",
            title=title,
            content=content,
            tags=tags,
            source=f"PDF: {source_novel}",
            creation_date=current_time,
            last_modified=current_time,
            knowledge_type="dialogue-technique",
            chapter_id=chapter_info.get('section_title', 'unknown') if chapter_info else None
        )

    async def batch_analyze(
        self,
        paragraphs_list: List[Dict],
        source_novel: str
    ) -> List[KnowledgeEntry]:
        """
        批量分析段落

        Args:
            paragraphs_list: 段落数据列表
            source_novel: 原始小说名称

        Returns:
            知识条目列表
        """
        all_entries = []
        total = len(paragraphs_list)

        for i, paragraph_data in enumerate(paragraphs_list):
            logger.info(f"正在分析文本段落 {i+1}/{total}")

            try:
                entry = await self.analyze_paragraph(paragraph_data, source_novel)
                if entry:
                    all_entries.append(entry)
            except Exception as e:
                logger.error(f"分析第 {i+1} 个段落时出错: {str(e)}")
                continue  # 继续处理下一个段落

        logger.info(f"批量分析完成，共生成 {len(all_entries)} 个知识条目")
        return all_entries