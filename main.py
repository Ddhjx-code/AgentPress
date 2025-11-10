# main.py
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily

from config import MODEL_CONFIG, PROMPTS_DIR, OUTPUT_DIR, CREATION_CONFIG
from utils import load_all_prompts, save_json, save_text
from agents_manager import AgentsManager
from conversation_manager import ConversationManager
from phases import NovelWritingPhases

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
    
    # 初始化管理器
    print("\n🔧 初始化管理器...")
    agents_manager = AgentsManager(model_client)
    conversation_manager = ConversationManager()
    
    # 初始化Agent
    success = await agents_manager.initialize(prompts)
    if not success:
        print("❌ 错误: Agent初始化失败")
        return
    
    # 初始化流程管理器
    phases = NovelWritingPhases(agents_manager, conversation_manager)
    
    # 显示创作配置
    print(f"\n⚙️  创作配置:")
    print(f"   创作模式: {'分章节模式' if CREATION_CONFIG['num_chapters'] > 1 else '单章模式'}")
    print(f"   总章数: {CREATION_CONFIG['num_chapters']}")
    print(f"   每章目标字数: {CREATION_CONFIG['target_length_per_chapter']} 字")
    print(f"   总目标字数: {CREATION_CONFIG['total_target_length']} 字")
    
    # 获取用户输入
    print("\n" + "="*60)
    print("📝 请输入你的小说创意")
    print("="*60)
    
    novel_concept = """
    又北二百里，曰发鸠之山，其上多柘木。有鸟焉，其状如乌，文首、白喙、赤足，名曰精卫，其鸣自詨。是炎帝之少女，名曰女娃。女娃游于东海，溺而不返，故为精卫。常衔西山之木石，以堙于东海。
    """
    
    # 可选：从用户输入读取
    # novel_concept = input("\n请描述你的小说创意（或按Enter使用默认示例）:\n")
    # if not novel_concept.strip():
    #     novel_concept = default_concept
    
    print(f"\n📖 你的创意:")
    print(f"{novel_concept}")
    
    # 运行完整流程
    try:
        final_output = await phases.run_full_pipeline(novel_concept)
        
        # 保存结果
        print("\n" + "="*60)
        print("💾 保存结果")
        print("="*60)
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 保存故事文本
        story_file = OUTPUT_DIR / "novel_story.txt"
        save_text(final_output["final_story"], story_file)
        
        # 保存完整数据
        data_file = OUTPUT_DIR / "novel_data.json"
        save_json(final_output, data_file)
        
        # 保存对话历史
        history_file = OUTPUT_DIR / "conversation_history.json"
        history_data = {
            "conversations": conversation_manager.conversation_history,
            "versions": conversation_manager.story_versions,
            "feedbacks": conversation_manager.feedback_records,
            "documentation": conversation_manager.documentation_records
        }
        save_json(history_data, history_file)
        
        # 显示摘要
        print("\n" + "="*60)
        print("✅ 创作完成！")
        print("="*60)
        print(f"\n📊 创作摘要:")
        print(f"  • 故事字数: {len(final_output['final_story'])} 字")
        print(f"  • 创建版本数: {final_output['summary']['total_versions']}")
        print(f"  • 评审轮数: {final_output['summary']['total_feedback_rounds']}")
        print(f"  • 对话轮数: {final_output['summary']['total_conversations']}")
        print(f"  • 创作模式: {'分章节模式' if CREATION_CONFIG['num_chapters'] > 1 else '单章模式'}")
        
        if final_output['final_check']:
            print(f"  • 发布就绪: {final_output['final_check'].get('ready_for_publication', False)}")
            print(f"  • 最终评分: {final_output['final_check'].get('final_score', 'N/A')}/100")
        
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
