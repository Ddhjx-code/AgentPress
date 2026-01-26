#!/usr/bin/env python3
"""
安徒生童话全面分析脚本 - 使用优化后的分段分析系统
"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import time

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from core.workflow_service import WorkflowService
from knowledge.novel_knowledge_extender import NovelKnowledgeExtender

load_dotenv()  # 加载环境变量


async def analyze_anded_sheng():
    """使用新优化系统分析安徒生童话"""
    print("📚 开始使用优化系统分析安徒生童话")
    print("="*60)

    workflow_service = WorkflowService()

    # 获取API配置
    api_key = os.getenv("QWEN_API_KEY", "")
    base_url = os.getenv("BASE_URL", "https://apis.iflow.cn/v1")
    model_name = os.getenv("MODEL_NAME", "qwen3-max")

    if not api_key:
        print("⚠️  未找到API密钥，请检查 .env 文件中的 QWEN_API_KEY 设置")
        return

    print("✅ API密钥已加载")

    # 初始化模型
    start_init_time = time.time()
    try:
        await workflow_service.initialize_models(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        print(f"✅ 工作流服务初始化完成 (耗时: {time.time() - start_init_time:.1f}秒)")
    except Exception as e:
        print(f"❌ 工作流初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 创建扩展管理器并使用优化分析
    extender = NovelKnowledgeExtender(workflow_service)

    # 分析单个PDF文件
    start_process_time = time.time()
    result = await extender.process_pdf_and_import("安徒生童话选.pdf")

    total_time = time.time() - start_process_time
    print(f"⏱️  安徒生童话分析完成 (总耗时: {total_time:.1f}秒)")
    print()

    # 显示结果统计
    print("📊 处理结果:")
    print(f"   原始PDF文件: {result['pdf_file']}")
    print(f"   分析段落数: {result['total_segments_analyzed']}")
    print(f"   知识条目创建数: {result['knowledge_entries_created']}")
    print(f"   成功导入数: {result['successful_imports']}")
    print(f"   失败数量: {result['failed_imports']}")
    print()

    # 提取完整知识库信息
    stats = await extender.get_novel_analysis_stats()
    print("🎯 知识库当前统计:")
    print(f"   总知识条目数: {stats['total_knowledge_entries']}")
    print(f"   小说分析相关条目: {stats['novel_analysis_entries']}")
    print(f"   按类型分布: {stats['breakdown_by_type']}")

    # 显示部分新创建的知识条目
    all_entries = await extender.km.get_all_entries()
    created_entries = [e for e in all_entries if '安徒生童话选' in e.source]

    print()
    print(f"📝 新增分析条目示例 (显示前5个):")
    for i, entry in enumerate(created_entries[-5:]):  # 显示最新创建的5个
        print(f"   {i+1}. 【{entry.knowledge_type}】 {entry.title}")
        print(f"      标签: {entry.tags}")
        print(f"      大小: {len(entry.content)} 字符")
        print(f"      内容预览: {entry.content[:120]}...")
        print()

    print("="*60)
    print("✅ 安徒生童话分析完成！")
    print("   数据已保存到 knowledge base 供后续创作参考")


def sync_main():
    """同步入口点"""
    import asyncio

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(analyze_anded_sheng())


if __name__ == "__main__":
    sync_main()