#!/usr/bin/env python3
"""
生成大于5000字的长篇故事
重构版：使用新的架构和专业处理器
"""
import asyncio
import sys
from pathlib import Path
import json

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from config import CREATION_CONFIG
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from core.agent_handlers_map import AgentHandlersMap
from src.phases import ResearchPhase, CreationPhase, ReviewPhase, FinalCheckPhase
from utils import load_all_prompts
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def generate_long_story():
    """生成一个大于5000字的长篇故事"""
    # 加载提示词
    prompts_dir = Path("prompts")
    prompts = load_all_prompts(prompts_dir)

    # 检查是否有必要提示词
    if not prompts:
        print("❌ 无法加载提示词文件")
        return

    # 更新创作配置以支持更长的故事
    print("📝 更新配置以支持大于5000字的长篇故事...")
    long_story_config = {
        'num_chapters': 1,
        'target_length_per_chapter': 6000,  # 增加每章目标到6000字
        'total_target_length': 6000        # 总目标字数设置为6000字
    }

    import os
    from dotenv import load_dotenv
    load_dotenv()  # 加载环境变量

    # 从环境变量获取API密钥
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        print("❌ 未找到QWEN_API_KEY环境变量")
        return

    # 创建模型客户端，使用ModelInfo
    from autogen_core.models import ModelInfo, ModelFamily

    model_client = OpenAIChatCompletionClient(
        model="qwen3-max",
        api_key=api_key,
        base_url="https://apis.iflow.cn/v1",
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            structured_output=False,
            family=ModelFamily.GPT_5
        )
    )

    # 创建代理管理器
    agent_manager = AgentManager(model_client)
    initialized = await agent_manager.initialize(prompts)

    if not initialized:
        print("❌ 代理管理器初始化失败")
        return

    # 创建其他必要组件
    conversation_manager = ConversationManager()
    documentation_manager = DocumentationManager()

    # 创建专门代理处理器映射
    agent_handlers_map = agent_manager.create_agent_handlers_map(documentation_manager)
    if not agent_handlers_map:
        print("❌ 代理处理器映射创建失败")
        return

    print(f"✅ 代理处理器映射创建完成，共有 {len(agent_handlers_map.list_handlers())} 个处理器")

    # 创建新的阶段管理器（使用重构后的版本）
    research_phase = ResearchPhase(agent_handlers_map, documentation_manager, conversation_manager)
    creation_phase = CreationPhase(agent_handlers_map, documentation_manager, conversation_manager)
    review_phase = ReviewPhase(agent_handlers_map, conversation_manager)
    final_check_phase = FinalCheckPhase(agent_handlers_map, conversation_manager)

    # 读取测试概念
    with open("test_concept.txt", 'r', encoding='utf-8') as f:
        concept = f.read()

    print(f"📚 使用概念: {concept[:100]}...")

    print("🔍 开始第一阶段：研究和规划...")
    research_data = await research_phase.execute_research(concept)

    print("✍️ 开始第二阶段：生成大于5000字的长篇故事...")
    # 设置进度回调
    async def progress_callback(phase, step, message, progress):
        print(f"[PROGRESS] {phase} - {step}: {message}")
    creation_phase.progress_callback = progress_callback
    long_story = await creation_phase.execute_creation(research_data)

    print("🧐 开始第三阶段：评审和修订...")
    review_phase.progress_callback = progress_callback
    revised_story = await review_phase.execute_review(long_story)

    print("✅ 开始第四阶段：最终检查...")
    final_story = await final_check_phase.execute_final_check(revised_story)

    # 计算中文汉字数量，这更符合用户关心的指标
    import re
    chinese_chars_count = len(re.findall(r'[\\u4e00-\\u9fff]', final_story))
    print(f"✅ 生成的长篇故事长度: {len(final_story)} 总字符 | {chinese_chars_count} 中文汉字")

    # 保存生成的故事
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    story_file = output_dir / "long_story_6000_chars.txt"
    with open(story_file, 'w', encoding='utf-8') as f:
        f.write(long_story)

    print(f"💾 长篇故事已保存: {story_file}")

    # 生成过程可视化报告
    if hasattr(conversation_manager, 'print_meeting_minutes_summary'):
        print("\n" + "="*70)
        print("📋 长篇故事生成过程AI代理协作总结")
        print("="*70)
        conversation_manager.print_meeting_minutes_summary()

        # 保存会议纪要到文件
        conversation_manager.save_meeting_minutes_to_file()

        # 使用ProcessVisualizer进行高级可视化分析
        try:
            from src.process_visualizer import ProcessVisualizer
            visualizer = ProcessVisualizer()
            visualizer.visualize_meeting_minutes(conversation_manager, "file")
            visualizer.visualize_detailed_participants(conversation_manager, "file")
            visualizer.save_complete_process_log(conversation_manager)
        except Exception as e:
            print(f"⚠️  扩展可视化失败: {e}")

    # 同时保存完整的代理工作日志
    if hasattr(novel_phases, 'agent_work_log'):
        log_file = output_dir / "long_story_agent_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(novel_phases.agent_work_log, f, ensure_ascii=False, indent=2)
        print(f"📋 代理工作日志已保存: {log_file}")

    return long_story


if __name__ == "__main__":
    try:
        result = asyncio.run(generate_long_story())
        if result and len(result) > 5000:
            print(f"\n🎉 成功生成大于5000字的长篇故事! 实际长度: {len(result)} 字符")
        elif result:
            print(f"\n⚠️  生成的故事长度: {len(result)} 字符，没有达到5000字，可能需要增加迭代或丰富情节内容")
        else:
            print("\n❌ 生成失败")
    except Exception as e:
        print(f"❌ 生成过程出现错误: {e}")
        import traceback
        traceback.print_exc()