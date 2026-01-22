# main.py
import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily
import json

from config import MODEL_CONFIG, PROMPTS_DIR, OUTPUT_DIR, CREATION_CONFIG
from utils import load_all_prompts, save_json, save_text
from phases import NovelWorkflowOrchestrator

async def main():
    """主程序"""

    # 加载环境变量
    load_dotenv()

    print("\n" + "="*60)
    print("🚀 网络小说AI创作系统")
    print("="*60)

    # 检查API密钥
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 QWEN_API_KEY 环境变量")
        return

    # 初始化模型客户端
    print("\n🔌 初始化模型客户端...")
    model_client = OpenAIChatCompletionClient(
        model=MODEL_CONFIG["model"],
        api_key=api_key,
        base_url=MODEL_CONFIG["base_url"],
        model_info=ModelInfo(
            vision=MODEL_CONFIG["vision"],
            function_calling=MODEL_CONFIG["function_calling"],
            json_output=MODEL_CONFIG["json_output"],
            structured_output=False,
            family=ModelFamily.GPT_5
        )
    )
    print("✅ 模型客户端就绪")

    # 加载提示词
    print("\n📖 加载提示词...")
    if not PROMPTS_DIR.exists():
        print(f"❌ 错误: 找不到提示词目录 {PROMPTS_DIR}")
        return

    prompts = load_all_prompts(PROMPTS_DIR)
    if not prompts:
        print("❌ 错误: 没有加载到提示词文件")
        return

    print(f"✅ 加载了 {len(prompts)} 个提示词")

    # 初始化AgentManager并加载代理
    print("\n🤖 初始化智能代理...")
    from core.agent_manager import AgentManager, ModelConfig
    agent_manager = AgentManager(model_client=model_client)

    # 加载提示词文件并初始化代理
    agent_init_success = await agent_manager.initialize(prompts)
    if not agent_init_success:
        print("❌ 代理初始化失败")
        return

    # 初始化 orchestrator (this will create conversation manager and documentation manager internally)
    print("\n🔧 初始化工作流orchestrator...")
    orchestrator = NovelWorkflowOrchestrator()
    print("✅ 工作流orchestrator就绪")

    # 显示创作配置
    print(f"\n⚙️  创作配置:")
    print(f"   创作模式: {'分章节模式' if CREATION_CONFIG['num_chapters'] > 1 else '单章模式'}")
    print(f"   总章数: {CREATION_CONFIG['num_chapters']}")
    print(f"   每章目标字数: {CREATION_CONFIG['target_length_per_chapter']} 字")
    print(f"   总目标字数: {CREATION_CONFIG['total_target_length']} 字")

    # 获取默认创意输入
    print("\n" + "="*60)
    print("📝 使用默认创意进行创作")
    print("="*60)

    novel_concept = """
    刑天与帝至此争神，帝断其首，葬之常羊之山。乃以乳为目，以脐为口，操干戚以舞。
    """

    print(f"\n📖 默认创意:")
    print(f"{novel_concept}")

    # 运行完整流程 using the new orchestrator
    try:
        # Note: Our orchestrator needs to call async methods as needed based on the current architecture
        # For now we'll call a simplified version - in proper implementation this would work asynchronously
        # But if we have an agent_manager, let's use the async workflow
        if agent_manager and agent_manager.is_initialized():
            final_output = await orchestrator.run_async_workflow(
                initial_idea=novel_concept,
                multi_chapter=CREATION_CONFIG['num_chapters'] > 1,
                total_chapters=CREATION_CONFIG['num_chapters'],
                agents_manager=agent_manager
            )
        else:
            final_output = orchestrator.run_complete_workflow(
                initial_idea=novel_concept,
                multi_chapter=CREATION_CONFIG['num_chapters'] > 1,
                total_chapters=CREATION_CONFIG['num_chapters']
            )

        # 保存结果
        print("\n" + "="*60)
        print("💾 保存结果")
        print("="*60)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 保存故事文本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        story_file = OUTPUT_DIR / f"novel_story_{timestamp}.txt"
        save_text(final_output["final_story"], story_file)

        # 保存完整数据
        data_file = OUTPUT_DIR / f"novel_data_{timestamp}.json"
        save_json(final_output, data_file)

        # 保存对话历史 (从orchestrator)
        conversation_manager = orchestrator.get_conversation_manager()
        history_file = OUTPUT_DIR / f"conversation_history_{timestamp}.json"
        history_data = {
            "conversations": getattr(conversation_manager, 'conversation_history', []),
            "versions": getattr(conversation_manager, 'story_versions', {}),
            "feedbacks": getattr(conversation_manager, 'feedback_records', {}),
            "documentation": getattr(conversation_manager, 'documentation_records', {}),
            "all_history": conversation_manager.get_all_history()
        }
        save_json(history_data, history_file)

        # 显示摘要
        print("\n" + "="*60)
        print("✅ 创作完成！")
        print("="*60)
        print(f"\n📊 创作摘要:")
        print(f"  • 初始想法: {final_output['initial_idea'][:50]}...")  # First 50 chars
        print(f"  • 故事字数: {len(final_output['final_story'])} 字")
        print(f"  • 研究计划长度: {len(final_output['research_plan'])} 字符")
        print(f"  • 创作模式: {'分章节模式' if CREATION_CONFIG['num_chapters'] > 1 else '单章模式'}")

        print(f"\n📁 输出文件:")
        print(f"  • 故事文本: {story_file}")
        print(f"  • 完整数据: {data_file}")
        print(f"  • 对话历史: {history_file}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭模型客户端
        await model_client.close()
        print("\n👋 程序结束")

if __name__ == "__main__":
    asyncio.run(main())
