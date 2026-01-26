#!/usr/bin/env python3
"""
简化版小说分析测试 - 仅测试前几个段落
"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from core.workflow_service import WorkflowService
from knowledge.pdf_processor import PDFProcessor
from knowledge.literary_analyzer import LiteraryAnalyzer
from knowledge.novel_knowledge_extender import NovelKnowledgeExtender

load_dotenv()  # 加载环境变量


async def test_novel_analysis():
    """测试小说分析功能"""
    print("🔧 初始化工作流服务...")

    workflow_service = WorkflowService()

    # 获取API配置
    api_key = os.getenv("QWEN_API_KEY", "")
    base_url = os.getenv("BASE_URL", "https://apis.iflow.cn/v1")
    model_name = os.getenv("MODEL_NAME", "qwen3-max")

    if not api_key:
        print("⚠️  未找到API密钥，请检查 .env 文件中的 QWEN_API_KEY 设置")
        return

    print("✅ API密钥已加载")

    try:
        await workflow_service.initialize_models(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        print("✅ 工作流服务初始化完成")
    except Exception as e:
        print(f"❌ 工作流初始化失败: {e}")
        return

    # 创建一个简化版的测试
    processor = PDFProcessor()

    # 只提取PDF的前几页内容
    pdf_data = processor.extract_pdf_content("安徒生童话选.pdf")
    content = pdf_data['content']

    # 截取前3个小节/章节的内容用于测试（避免大量API调用）
    # 找到前几个段落
    paragraphs = content.split('\n\n')

    # 取前5个段落用于测试，确保总字符数适中
    test_paragraphs = []
    total_chars = 0
    for para in paragraphs:
        para = para.strip()
        if para and len(para) > 10:  # 非空且够长的段落
            if total_chars + len(para) < 2000:  # 累计不超过2000字符
                test_paragraphs.append(para)
                total_chars += len(para)
            else:
                break

    print(f"📖 测试内容段落数: {len(test_paragraphs)}")
    for i, para in enumerate(test_paragraphs):
        print(f"  段落 {i+1}: {len(para)} 字符 - \"{para[:60]}...\"")

    print("\n🔄 初始化测试分析模块...")

    # 创建一个扩展管理器并进行简化测试
    extender = NovelKnowledgeExtender(workflow_service)

    # 手动创建分段的数据结构（模拟PDF分割结果）
    test_segments = [
        {
            'id': f'test_para_{i:03d}',
            'text': para,
            'original_pos': i,
            'chapter_info': {'section_title': '测试段落'},
            'word_count': len(para),
            'is_chapter_header': False,
            'section_title': f'测试段落 {i+1}',
            'original_title': '安徒生童话选-测试'
        }
        for i, para in enumerate(test_paragraphs)
    ]

    print(f"🔍 开始分析 {len(test_segments)} 个测试段落...")

    # 只分析前几个段落，而不是全部521个
    success_count = 0
    results = []

    for i, segment in enumerate(test_segments):
        print(f"  分析段落 {i+1}/{len(test_segments)}...")
        try:
            entry = await extender.literary_analyzer.analyze_paragraph(
                segment,
                '安徒生童话选-测试'
            )
            if entry:
                # 保存到知识库
                success = await extender.km.add_entry(
                    title=entry.title,
                    content=entry.content,
                    tags=entry.tags,
                    knowledge_type=entry.knowledge_type,
                    source=entry.source
                )
                if success:
                    print(f"    ✅ 成功创建知识条目: {entry.knowledge_type} - {len(entry.content)} 字符")
                    results.append(entry)
                    success_count += 1
            else:
                print(f"    ⚠️ 未生成知识条目，可能此段不需要分析")
        except Exception as e:
            print(f"    ❌ 分析失败: {str(e)}")
            continue

    print(f"\n🎯 测试结果:")
    print(f"   成功分析: {success_count}/{len(test_segments)} 个段落")
    print(f"   新增知识条目: {len(results)} 个")

    if results:
        print(f"\n📝 新增知识示例:")
        for i, entry in enumerate(results):
            print(f"   {i+1}. 类型: {entry.knowledge_type}")
            print(f"      标题: {entry.title[:50]}...")
            print(f"      标签: {entry.tags}")
            print(f"      内容长度: {len(entry.content)} 字符")
            print(f"      摘录: {entry.content[:100]}...")
            print()

    # 显示最新知识库信息
    all_entries = await extender.km.get_all_entries()
    print(f"📊 最新知识库统计: {len(all_entries)} 个条目")

    type_stats = {}
    for entry in all_entries:
        k_type = entry.knowledge_type
        type_stats[k_type] = type_stats.get(k_type, 0) + 1

    print(f"   按类型统计: {type_stats}")

    # 检查条目大小
    if all_entries:
        sizes = [len(entry.content) for entry in all_entries]
        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)
        print(f"   条目大小 - 平均: {avg_size:.0f}, 最大: {max_size} 字符")


def sync_main():
    """同步入口点"""
    import asyncio

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(test_novel_analysis())


if __name__ == "__main__":
    sync_main()