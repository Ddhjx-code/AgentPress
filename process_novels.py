#!/usr/bin/env python3
"""
PDF小说批量处理脚本

用途:
- 命令行批量处理PDF小说文件
- 提取文学技巧、经典段落等内容到知识库
- 支持目录处理和配置化处理
"""
import asyncio
import sys
import argparse
from pathlib import Path
import os
import json
from dotenv import load_dotenv

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from core.workflow_service import WorkflowService
from knowledge.novel_knowledge_extender import NovelKnowledgeExtender

load_dotenv()  # 加载环境变量


async def initialize_workflow():
    """初始化工作流服务"""
    print("🔧 初始化工作流服务...")

    workflow_service = WorkflowService()

    # 获取API配置
    api_key = os.getenv("QWEN_API_KEY", "")
    base_url = os.getenv("BASE_URL", "https://apis.iflow.cn/v1")  # 使用更新后的API端点
    model_name = os.getenv("MODEL_NAME", "qwen3-max")  # 使用更新后的模型

    if not api_key:
        print("⚠️  未找到API密钥，请检查 .env 文件中的 QWEN_API_KEY 设置")
        return None

    print("✅ API密钥已加载")

    try:
        await workflow_service.initialize_models(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        print("✅ 工作流服务初始化完成\n")
        return workflow_service
    except Exception as e:
        print(f"❌ 工作流初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def process_single_pdf(pdf_path: str, extender: NovelKnowledgeExtender):
    """处理单个PDF文件"""
    print(f"📄 处理PDF文件: {pdf_path}")
    result = await extender.process_pdf_and_import(pdf_path)

    print(f"📊 处理结果:")
    print(f"   - 总段落数: {result.get('total_segments_analyzed', 0)}")
    print(f"   - 创建知识条目数: {result.get('knowledge_entries_created', 0)}")
    print(f"   - 成功导入数: {result.get('successful_imports', 0)}")
    print(f"   - 失败导入数: {result.get('failed_imports', 0)}")

    if result['status'] == 'error':
        print(f"   - 错误信息: {result['message']}")

    print()
    return result


async def process_pdf_directory(directory_path: str, extender: NovelKnowledgeExtender):
    """处理PDF目录"""
    print(f"📁 处理PDF目录: {directory_path}")

    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"❌ 目录不存在: {directory_path}")
        return None

    # 查找所有PDF文件
    pdf_files = list(dir_path.glob("*.pdf"))
    pdf_files_str = [str(f) for f in pdf_files]

    print(f"📦 找到 {len(pdf_files_str)} 个PDF文件\n")

    if not pdf_files_str:
        print("⚠️  目录中未找到任何PDF文件")
        return None

    results = await extender.process_pdf_batch(pdf_files_str)
    return results


async def main():
    """主函数 - 命令行处理入口"""
    parser = argparse.ArgumentParser(description="PDF小说文学技巧分析处理工具")
    parser.add_argument("input", help="输入路径：PDF文件或包含PDF的目录")
    parser.add_argument("--mode", choices=["single", "directory"], default="directory",
                        help="处理模式：single(单文件)或directory(目录)")

    args = parser.parse_args()
    input_path = args.input
    mode = args.mode

    print("📚 AgentPress PDF小说分析处理工具")
    print("="*50)

    # 初始化工作流
    workflow_service = await initialize_workflow()
    if not workflow_service:
        return

    # 创建扩展管理器
    extender = NovelKnowledgeExtender(workflow_service)

    try:
        if mode == "single":
            # 处理单个PDF文件
            if not Path(input_path).exists():
                print(f"❌ 文件不存在: {input_path}")
                return

            if not input_path.lower().endswith('.pdf'):
                print("❌ 请输入PDF文件路径")
                return

            result = await process_single_pdf(input_path, extender)

        else:  # directory mode
            # 处理目录中的PDF文件
            result = await process_pdf_directory(input_path, extender)

        # 输出处理结果
        print("="*50)
        print("📈 最终处理统计:")
        if result and 'total_files_processed' in result:
            # 批量处理结果
            print(f"   - 总处理文件数: {result.get('total_files_processed', 0)}")
            print(f"   - 成功处理数: {result.get('successful_files', 0)}")
            print(f"   - 失败处理数: {result.get('failed_files', 0)}")
            print(f"   - 创建知识条目总数: {result.get('total_knowledge_entries_created', 0)}")
            print(f"   - 成功导入总数: {result.get('total_successful_imports', 0)}")
        elif result:
            # 单文件处理结果
            print(f"   - 成功导入: {result.get('successful_imports', 0)}")

        print("✅ 处理完成!")

    except KeyboardInterrupt:
        print("\n⚠️  处理被用户中断")
    except Exception as e:
        print(f"❌ 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()


def sync_main():
    """同步入口点"""
    # 导入 asyncio 以确保它始终可用
    import asyncio

    if sys.platform.startswith("win"):
        # Windows平台需要特殊处理 asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())


if __name__ == "__main__":
    sync_main()