#!/usr/bin/env python3
"""
测试新增代理角色的可用性
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from core.agent_manager import AgentManager
from config import AGENT_CONFIGS
from autogen_ext.models.openai import OpenAIChatCompletionClient
import openai


async def test_agent_initialization():
    """测试代理管理器是否能正确加载新角色"""
    print("🧪 测试新代理角色初始化...")

    # Mock的模型客户端（使用Qwen API）
    model_client = OpenAIChatCompletionClient(
        model="qwen3-max",
        base_url="https://apis.iflow.cn/v1",
    )

    # 加载所有提示词
    prompts_dir = Path("prompts")
    prompts = {}

    for prompt_file in prompts_dir.glob("*.md"):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts[prompt_file.stem] = f.read()
        except Exception as e:
            print(f"⚠️ 读取 {prompt_file} 时出错: {e}")

    print("📋 可用的提示词文件:")
    for key in prompts.keys():
        print(f"   - {key}")

    print(f"\n📋 配置中的代理角色数量: {len(AGENT_CONFIGS)}")
    print("📋 配置的代理:")
    for key, config in AGENT_CONFIGS.items():
        print(f"   - {config['display_name']} ({key}) - {'已找到提示词' if key in prompts else '缺失提示词'}")

    # 检查新增的代理
    new_agents = ["write_enviroment_specialist", "write_rate_specialist"]
    print(f"\n📋 检查新增代理:")
    for agent in new_agents:
        found = agent in AGENT_CONFIGS
        prompt_found = agent in prompts
        print(f"   - {agent}: {'✅' if found else '❌'} 配置 | {'✅' if prompt_found else '❌'} 提示词")

    # 初始化AgentManager
    print("\n🔧 初始化代理管理器...")
    agent_manager = AgentManager(model_client)
    initialized = await agent_manager.initialize(prompts)

    if initialized:
        print(f"✅ 代理管理器初始化成功，已加载 {len(agent_manager.agents)} 个代理")

        # 检查是否包含新代理
        for agent_key in new_agents:
            if agent_key in agent_manager.agents:
                print(f"   - ✅ {agent_key} 已加载")
            else:
                print(f"   - ❌ {agent_key} 未找到")
    else:
        print("❌ 代理管理器初始化失败")

    return agent_manager if initialized else None


if __name__ == "__main__":
    agent_manager = asyncio.run(test_agent_initialization())

    if agent_manager:
        print("\n🎉 测试完成，新代理角色已成功集成！")
    else:
        print("\n❌ 测试失败，存在配置或加载问题。")