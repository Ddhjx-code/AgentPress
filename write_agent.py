# main.py
import asyncio
import os
import json
import re
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily

def load_prompt(file_path: str) -> str:
    """从 Markdown 文件加载提示词"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 移除 Markdown 标题和代码块标记
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'```[a-z]*\n?', '', content)
        return content.strip()

def extract_content(messages):
    """通用内容提取"""
    for msg in reversed(messages):
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            return msg.content
    return ""

def parse_json_response(response: str) -> dict:
    """安全解析 JSON 响应"""
    try:
        # 提取 JSON 部分（兼容 markdown 代码块）
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        print(f"⚠️ JSON 解析失败，返回原始内容")
        return {"raw_response": response}

async def main():
    print("🚀 启动结构化山海经编辑社...")
    
    # 加载提示词
    prompt_dir = Path("prompts")
    prompts = {
        "mythologist": load_prompt(prompt_dir / "mythologist.md"),
        "writer": load_prompt(prompt_dir / "writer.md"),
        "fact_checker": load_prompt(prompt_dir / "fact_checker.md"),
        "editor": load_prompt(prompt_dir / "editor.md")
    }

    # 模型配置
    model_client = OpenAIChatCompletionClient(
        model="qwen-max",
        api_key=os.getenv("QWEN_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            structured_output=False,
            family=ModelFamily.GPT_5
        )
    )

    # 创建角色
    agents = {
        "mythologist": AssistantAgent("Mythologist", model_client=model_client, system_message=prompts["mythologist"]),
        "writer": AssistantAgent("Writer", model_client=model_client, system_message=prompts["writer"]),
        "fact_checker": AssistantAgent("FactChecker", model_client=model_client, system_message=prompts["fact_checker"]),
        "editor": AssistantAgent("Editor", model_client=model_client, system_message=prompts["editor"])
    }

    # 原文输入
    shanhai_text = "青丘之山，有兽焉，其状如狐而九尾，其音如婴儿，能食人，食者不蛊。"
    print(f"\n📝 原文: {shanhai_text}")

    # Step 1: 神话学家考据
    print("\n🔍 Step 1: 神话学家考据...")
    myth_task = f"请分析以下《山海经》原文：{shanhai_text}"
    myth_result = await agents["mythologist"].run(task=myth_task)
    myth_content = extract_content(myth_result.messages)
    research_data = parse_json_response(myth_content)
    print(f"✅ 考据完成: {research_data.get('translation', 'N/A')[:100]}...")

    # Step 2: 作家创作初稿
    print("\n✍️ Step 2: 作家创作初稿...")
    writer_input = json.dumps({"research": research_data}, ensure_ascii=False)
    writer_result = await agents["writer"].run(task=writer_input)
    story = extract_content(writer_result.messages)
    print(f"✅ 初稿完成: {len(story)} 字符")

    # Step 3: 多轮修订
    max_rounds = 3
    for round_num in range(max_rounds):
        print(f"\n🔄 Step 3.{round_num + 1}: 第 {round_num + 1} 轮校验与修订...")
        
        # 并行校验
        fact_task = agents["fact_checker"].run(task=story)
        edit_task = agents["editor"].run(task=story)
        fact_result, edit_result = await asyncio.gather(fact_task, edit_task)
        
        fact_content = extract_content(fact_result.messages)
        edit_content = extract_content(edit_result.messages)
        
        fact_feedback = parse_json_response(fact_content)
        edit_feedback = parse_json_response(edit_content)
        
        # 检查是否通过
        fact_passed = fact_feedback.get("is_accurate", False) or "FACT_CHECK_PASSED" in fact_content
        edit_passed = edit_feedback.get("is_approved", False) or "EDIT_APPROVED" in edit_content
        
        if fact_passed and edit_passed:
            print(f"✅ 第 {round_num + 1} 轮通过！")
            break
            
        # 准备修订输入
        revision_input = json.dumps({
            "research": research_data,
            "revision_feedback": {
                "fact_check": fact_feedback,
                "editor": edit_feedback
            },
            "current_story": story
        }, ensure_ascii=False, indent=2)
        
        # 作家修订
        writer_result = await agents["writer"].run(task=revision_input)
        story = extract_content(writer_result.messages)
        print(f"✅ 修订完成: {len(story)} 字符")
        
        # 显示反馈摘要
        fact_issues = fact_feedback.get("issues", [])
        edit_weaknesses = edit_feedback.get("weaknesses", [])
        if fact_issues or edit_weaknesses:
            print(f"📝 修订要点: {fact_issues[:2] + edit_weaknesses[:2]}")

    # 保存最终结果
    output_data = {
        "original_text": shanhai_text,
        "research": research_data,
        "final_story": story,
        "revision_rounds": round_num + 1
    }
    
    with open("shanhai_final_output.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    with open("shanhai_final_story.md", "w", encoding="utf-8") as f:
        f.write(f"# 《山海经》神话故事\n\n")
        f.write(f"## 原文\n{shanhai_text}\n\n")
        f.write(f"## 考据\n```json\n{json.dumps(research_data, ensure_ascii=False, indent=2)}\n```\n\n")
        f.write(f"## 故事\n{story}\n")
    
    print(f"\n✅ 最终故事已保存:")
    print(f"   - JSON 格式: shanhai_final_output.json")
    print(f"   - Markdown 格式: shanhai_final_story.md")
    
    await model_client.close()
    print("\n🎉 山海经编辑社协作完成！")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
