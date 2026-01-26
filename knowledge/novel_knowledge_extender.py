"""
拓展知识管理器 - 处理PDF小说分析结果

功能:
- 扩展原有知识管理功能，专门处理文学分析结果
- 管理新的知识类型（novel-technique、classic-paragraph等）
- 提供PDF批量处理和导入功能
- 支持多层分析（分段→章节→全书）
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from .manager import KnowledgeManager
from .base import KnowledgeEntry
from .pdf_processor import PDFProcessor
from .literary_analyzer import LiteraryAnalyzer
from .chapter_analyzer import ChapterAnalyzer  # 新增章节分析器
from core.workflow_service import WorkflowService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NovelKnowledgeExtender:
    """小说知识扩展管理器 - 专门处理PDF小说分析和知识条目生成"""

    def __init__(self, workflow_service: WorkflowService):
        # 使用增强存储系统来处理分层分析结果
        self.km = KnowledgeManager(storage_path="data/knowledge_repo/enhanced/", use_enhanced_storage=True)
        self.pdf_processor = PDFProcessor()
        self.literary_analyzer = LiteraryAnalyzer(workflow_service)
        self.workflow_service = workflow_service  # 保存以支持整体分析

    async def process_pdf_and_import(self, pdf_path: str) -> Dict[str, Any]:
        """
        完整处理单个PDF文件并导入知识库（支持多层分析）

        Args:
            pdf_path: PDF文件路径

        Returns:
            处理结果字典
        """
        try:
            file_path = Path(pdf_path)
            if not file_path.exists():
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

            print(f"📚 开始处理PDF文件: {file_path.name}")
            logger.info(f"开始处理PDF文件: {pdf_path}")

            # 1. PDF内容提取和分割
            print("🔄 步骤1: 提取并分段PDF内容...")
            logger.info("步骤1: 提取并分段PDF内容...")
            segments = self.pdf_processor.process_pdf(pdf_path)

            total_segments = len(segments)
            print(f"✅ PDF内容已分割为 {total_segments} 个段落")
            logger.info(f"PDF内容已分割为 {total_segments} 个段落")

            # 2. 使用AI分析器分析每个段落
            print(f"🔄 步骤2: 使用AI分析 {total_segments} 个段落...")
            logger.info("步骤2: 使用AI分析每个段落...")
            knowledge_entries = await self.literary_analyzer.batch_analyze(
                segments,
                file_path.name
            )

            # 3. 生成章节级分析摘要（基于段落分析结果）
            print("🔄 步骤3: 生成章节级分析摘要...")
            logger.info("步骤3: 生成章节级分析摘要...")
            chapter_analyzer = ChapterAnalyzer(self.workflow_service.model_client)
            chapter_summaries = await chapter_analyzer.analyze_chapters_from_segments(segments)

            # 添加章节摘要作为新的知识条目
            print(f"🔄 正在保存章节分析结果...")
            for i, chapter_summary in enumerate(chapter_summaries):
                success = await self.km.add_entry(
                    title=chapter_summary.title,
                    content=chapter_summary.content,
                    tags=chapter_summary.tags,
                    knowledge_type=chapter_summary.knowledge_type,
                    source=chapter_summary.source
                )
                if success:
                    knowledge_entries.append(chapter_summary)

            print(f"✅ 章节分析摘要已保存 ({len(chapter_summaries)} 个)")

            # 4. 整体结构分析（基于章节摘要）
            print("🔄 步骤4: 进行整书结构分析...")
            logger.info("步骤4: 进行整书结构分析...")
            try:
                overall_analysis = await chapter_analyzer.analyze_overall_narrative_structure(
                    segments, file_path.name
                )

                if overall_analysis:
                    success = await self.km.add_entry(
                        title=overall_analysis.title,
                        content=overall_analysis.content,
                        tags=overall_analysis.tags,
                        knowledge_type=overall_analysis.knowledge_type,
                        source=overall_analysis.source
                    )
                    if success:
                        knowledge_entries.append(overall_analysis)
                    print("✅ 整书结构分析已保存")
            except Exception as e:
                logger.warning(f"整书结构分析出错，将跳过: {str(e)}")
                print(f"⚠️  整书结构分析出错: {str(e)}")

            # 5. 总结处理结果
            print(f"🔄 步骤5: 保存所有知识条目到知识库...")
            logger.info(f"步骤5: 批量保存 {len(knowledge_entries)} 个知识条目到知识库...")
            successful_imports = 0
            total_entries = len(knowledge_entries)
            for i, entry in enumerate(knowledge_entries):
                try:
                    success = await self.km.add_entry(
                        title=entry.title,
                        content=entry.content,
                        tags=entry.tags,
                        knowledge_type=entry.knowledge_type,
                        source=entry.source
                    )
                    if success:
                        successful_imports += 1
                except Exception as e:
                    logger.error(f"保存知识条目失败 (ID: {entry.id}): {str(e)}")

                # 每处理10个条目或在关键节点显示一次进度
                if (i + 1) % 10 == 0 or (i + 1) == total_entries or i == 0:
                    progress_percent = ((i + 1) / total_entries) * 100
                    print(f"💾 已保存 {i+1}/{total_entries} 个知识条目到JSON文件 ({progress_percent:.1f}%)")

                # 每处理50个条目后，显示当前存储状态
                if (i + 1) % 50 == 0:
                    current_stats = await self.get_novel_analysis_stats()
                    print(f"📊 当前知识库统计: 共 {current_stats['total_knowledge_entries']} 个条目 | "
                          f"小说分析: {current_stats['novel_analysis_entries']} 个 | "
                          f"来源PDF: {current_stats['unique_sources']} 个")

            # 6. 生成处理报告
            result = {
                'status': 'success',
                'pdf_file': pdf_path,
                'total_segments_analyzed': total_segments,
                'knowledge_entries_created': len(knowledge_entries),
                'successful_imports': successful_imports,
                'failed_imports': len(knowledge_entries) - successful_imports,
                'message': f"成功处理PDF文件，创建了 {successful_imports} 个知识条目 (含段落级、章节级、全书级分析)"
            }

            print(f"🎉 PDF处理完成!")
            print(f"📊 统计信息:")
            print(f"   - 总段落数: {total_segments}")
            print(f"   - 创建知识条目: {len(knowledge_entries)}")
            print(f"   - 成功导入: {successful_imports}")
            print(f"   - 失败导入: {len(knowledge_entries) - successful_imports}")

            logger.info(f"PDF处理完成: {result['message']}")
            return result

        except Exception as e:
            logger.error(f"处理PDF文件时出错: {str(e)}")
            print(f"❌ 处理PDF文件时出错: {str(e)}")
            return {
                'status': 'error',
                'pdf_file': pdf_path,
                'message': str(e),
                'total_segments_analyzed': 0,
                'knowledge_entries_created': 0,
                'successful_imports': 0,
                'failed_imports': 0
            }

    async def process_pdf_batch(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        批量处理多个PDF文件

        Args:
            pdf_paths: PDF文件路径列表

        Returns:
            批量处理结果汇总
        """
        total_files = len(pdf_paths)
        print(f"📚 开始批量处理 {total_files} 个PDF文件...")
        logger.info(f"开始批量处理 {len(pdf_paths)} 个PDF文件...")

        results = []
        total_successful = 0
        total_entries = 0

        for i, pdf_path in enumerate(pdf_paths):
            current_file_num = i + 1
            progress_percent = current_file_num / total_files * 100
            print(f"\n📋 进度: {current_file_num}/{total_files} ({progress_percent:.1f}%) - {Path(pdf_path).name}")
            logger.info(f"处理进度: {current_file_num}/{total_files} - {pdf_path}")

            result = await self.process_pdf_and_import(pdf_path)
            results.append(result)

            total_successful += result.get('successful_imports', 0)
            total_entries += result.get('knowledge_entries_created', 0)

            # 显示当前进度汇总
            print(f"📈 当前汇总: 已处理 {current_file_num} 个文件，"
                  f"累计生成 {total_entries} 个知识条目，"
                  f"成功导入 {total_successful} 个")

        # 汇总结果
        overall_result = {
            'status': 'completed',
            'total_files_processed': len(pdf_paths),
            'successful_files': sum(1 for r in results if r.get('status') == 'success'),
            'failed_files': sum(1 for r in results if r.get('status') == 'error'),
            'total_knowledge_entries_created': total_entries,
            'total_successful_imports': total_successful,
            'failed_imports': total_entries - total_successful,
            'individual_results': results
        }

        print(f"\n🎉 批量处理完成!")
        print(f"📊 最终统计:")
        print(f"   - 总处理文件数: {total_files}")
        print(f"   - 成功处理: {overall_result['successful_files']}")
        print(f"   - 失败处理: {overall_result['failed_files']}")
        print(f"   - 创建知识条目: {total_entries}")
        print(f"   - 成功导入: {total_successful}")
        print(f"   - 导入失败: {total_entries - total_successful}")

        logger.info(f"批量处理完成: 成功处理 {overall_result['successful_files']} 个文件, "
                   f"创建 {total_successful} 个知识条目")

        return overall_result

    async def process_directory(self, directory_path: str, file_pattern: str = "*.pdf") -> Dict[str, Any]:
        """
        处理目录中的所有PDF文件

        Args:
            directory_path: 包含PDF文件的目录路径
            file_pattern: 文件匹配模式

        Returns:
            处理结果汇总
        """
        dir_path = Path(directory_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")

        # 查找所有匹配的PDF文件
        pdf_files = list(dir_path.glob(file_pattern))
        pdf_files_str = [str(f) for f in pdf_files if f.suffix.lower() == '.pdf']

        if not pdf_files_str:
            return {
                'status': 'error',
                'message': f"在目录 {directory_path} 中未找到PDF文件"
            }

        logger.info(f"在目录中找到 {len(pdf_files_str)} 个PDF文件")
        return await self.process_pdf_batch(pdf_files_str)

    async def get_novel_analysis_stats(self) -> Dict[str, Any]:
        """
        获取小说分析知识库统计信息

        Returns:
            包含统计信息的字典
        """
        all_entries = await self.km.get_all_entries()

        # 按知识类型统计
        type_counts = {}
        for entry in all_entries:
            k_type = entry.knowledge_type
            if k_type in ['novel-technique', 'classic-paragraph', 'character-development', 'dialogue-technique']:
                type_counts[k_type] = type_counts.get(k_type, 0) + 1

        # 按来源统计
        source_counts = {}
        for entry in all_entries:
            source = entry.source
            if source.startswith('PDF:'):
                source_counts[source] = source_counts.get(source, 0) + 1

        return {
            'total_knowledge_entries': len(all_entries),
            'novel_analysis_entries': sum(type_counts.values()),
            'breakdown_by_type': type_counts,
            'breakdown_by_source': source_counts,
            'unique_sources': len(source_counts)
        }

    async def search_novel_techniques(self, query: str, tags: List[str] = None) -> List[KnowledgeEntry]:
        """
        搜索小说技巧相关的知识条目

        Args:
            query: 搜索查询词
            tags: 标签筛选条件

        Returns:
            匹配的知识条目列表
        """
        # 搜索所有小说分析类型的知识入口
        types_to_search = ['novel-technique', 'classic-paragraph', 'character-development', 'dialogue-technique']

        results = []
        all_entries = await self.km.get_all_entries()

        for entry in all_entries:
            if entry.knowledge_type in types_to_search:
                # 检查查询匹配
                matches_query = (query.lower() in entry.title.lower() or
                               query.lower() in entry.content.lower())

                # 检查标签匹配
                if tags is None or all(tag in entry.tags for tag in tags):
                    # 如果满足所有条件，加入结果
                    if query == "" or matches_query:
                        results.append(entry)

        return results

    async def get_examples_by_novel_type(self, novel_type: str, limit: int = 10) -> List[KnowledgeEntry]:
        """
        获取特定类型的小说技巧示例

        Args:
            novel_type: 小说技巧类型 (如 'character-development', 'dialogue', 'descriptive' 等)
            limit: 返回数量限制

        Returns:
            匹配的知识条目列表
        """
        all_entries = await self.km.get_all_entries()
        matching_entries = []

        type_mappings = {
            'character-development': ['character-development'],
            'dialogue-techniques': ['dialogue-technique'],
            'descriptive-passages': ['novel-technique'],
            'classic-passages': ['classic-paragraph'],
            'narrative-techniques': ['novel-technique']
        }

        if novel_type in type_mappings:
            target_types = type_mappings[novel_type]
            for entry in all_entries:
                if entry.knowledge_type in target_types:
                    matching_entries.append(entry)

        # 可以进一步根据标签过滤
        if novel_type == 'character-development':
            matching_entries = [e for e in matching_entries if 'character' in str(e.tags).lower()]
        elif novel_type == 'dialogue-techniques':
            matching_entries = [e for e in matching_entries if 'dialogue' in str(e.tags).lower()]
        elif novel_type == 'descriptive-passages':
            matching_entries = [e for e in matching_entries if 'descriptive' in str(e.tags).lower()]

        return matching_entries[:limit]