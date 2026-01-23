"""
命令行测试模式 (原main.py的简化版)
- 用于快速测试核心功能
- 可用于开发和调试目的
- 不作为主要运行方式
"""
import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json

from config import MODEL_CONFIG
from utils import save_json, save_text
from core.workflow_service import WorkflowService

async def test_cli():
    """简化测试入口"""
    # 加载环境变量
    load_dotenv()

    print("\n" + "="*60)
    print("🧪 AgentPress - 核心功能快速测试")
    print("="*60)

    # 检查API密钥
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        print("❌ 缺少QWEN_API_KEY环境变量 - 请设置后再运行")
        return

    # 初始化工作流服务
    print("\n🔧 初始化服务...")
    workflow_service = WorkflowService()

    try:
        await workflow_service.initialize_models(
            api_key=api_key,
            base_url=MODEL_CONFIG["base_url"],
            model_name=MODEL_CONFIG["model"]
        )
        print("✅ 初始化完成")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 使用简化的测试概念
    test_concept = "刑天与帝至此争神，帝断其首，葬之常羊之山。乃以乳为目，以脐为口，操干戚以舞。"

    print(f"\n📝 测试概念: {test_concept[:60]}...")

    try:
        print("\n🔄 执行测试生成...")
        result = await workflow_service.execute_workflow(
            novel_concept=test_concept,
            multi_chapter=True,  # 现在使用AI驱动的动态章节
            total_chapters=3  # 实际章数将由AI决定
        )

        if result["status"] == "success":
            final_output = result["data"]
            print(f"✅ 测试生成成功 - 故事长度: {len(final_output['final_story'])} 字")

            # 简化输出
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = output_dir / f"test_output_{timestamp}.txt"
            save_text(final_output["final_story"], test_file)
            print(f"💾 输出保存: {test_file}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭模型客户端
        if hasattr(workflow_service, 'model_client') and workflow_service.model_client:
            await workflow_service.model_client.close()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    # 明确这是仅用于命令行测试的入口
    print("⚠️  这是命令行测试模式，主要用于开发/调试")
    print("➡️  主要用法请使用Web UI: python -m apps.web_ui")
    asyncio.run(test_cli())