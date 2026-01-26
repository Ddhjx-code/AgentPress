#!/usr/bin/env python3
"""
快速测试优化后的AgentPress小说生成系统
"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

# 将项目根目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.workflow_service import WorkflowService
from config import CREATION_CONFIG


async def run_optimized_test():
    """运行优化后的小说生成测试"""

    print("="*70)
    print("⚡ 优化后的小说生成测试（控制长度和token消耗）")
    print("="*70)

    print("⚙️  当前设置状态：")
    print(f"   - 每章目标长度: {CREATION_CONFIG['target_length_per_chapter']} 字")
    print(f"   - 总目标长度: {CREATION_CONFIG['total_target_length']} 字")
    print(f"   - 章节数: {CREATION_CONFIG['num_chapters']} 章")


    # 读取测试设定
    try:
        with open("test_concept.txt", "r", encoding="utf-8") as f:
            concept = f.read().strip()
        print(f"\n📋 测试概念: {len(concept)} 字符")
    except FileNotFoundError:
        concept = "一个简短的故事概念"
        print("⚠️  test_concept.txt 未找到，使用默认概念")

    print(f"📋 概念预览: {concept[:100]}...")

    # 创建工作流服务
    workflow_service = WorkflowService()

    # 初始化模型
    print("\n🔧 初始化模型...")
    try:
        api_key = os.getenv("QWEN_API_KEY", "")

        if not api_key:
            print("⚠️  未找到API密钥")
            return

        print("✅ API密钥已加载")

        await workflow_service.initialize_models(
            api_key=api_key,
            base_url="https://apis.iflow.cn/v1",
            model_name="qwen3-max"
        )
        print("✅ 模型初始化完成\n")
    except Exception as e:
        print(f"❌ 模型初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 执行小说生成工作流（限制内容量）
    print("⏳ 开始优化后的小说创作流程...")
    print("   (限制: 长度控制, 减少评审轮数, 跳过修订以节省token)")
    try:
        result = await workflow_service.execute_workflow(
            novel_concept=concept,
            multi_chapter=True,
            total_chapters=1
        )

        if result.get("status") == "success":
            print("\n🎉 小说生成成功!")

            final_story = result.get("data", {}).get("final_story", "")
            print(f"📝 生成内容字数: {len(final_story)} 字")

            # 保存生成的小说
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_optimized")
            output_file = Path("output") / f"novel_optimized_{timestamp}.txt"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("Optimized Novel Generation Result\n")
                f.write("="*50 + "\n")
                f.write(f"Concept: {concept}\n\n")
                f.write(f"Expected Length: ~{CREATION_CONFIG['total_target_length']} chars\n")
                f.write(f"Actual Length: {len(final_story)} chars\n")
                f.write("\nStory Content:\n")
                f.write(final_story)

            print(f"💾 生成结果已保存到: {output_file}")
            print(f"📊 长度控制效果: 目标 {CREATION_CONFIG['total_target_length']}, 实际 {len(final_story)}")

            # 显示部分内容预览
            preview_length = min(800, len(final_story))
            print(f"\n📖 前 {preview_length} 字符预览:")
            print("-" * 40)
            print(final_story[:preview_length])
            if len(final_story) > preview_length:
                print("...")
            print("-" * 40)

        else:
            error_msg = result.get("message", "未知错误")
            print(f"\n❌ 小说生成失败: {error_msg}")
            # 输出更详细的错误信息，如果有
            if "data" in result:
                import json
                print(f"   返回数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)[:500]}...")

    except Exception as e:
        print(f"❌ 执行小说生成流程时出错: {e}")
        import traceback
        traceback.print_exc()


def sync_main():
    """同步入口点"""
    asyncio.run(run_optimized_test())


if __name__ == "__main__":
    sync_main()