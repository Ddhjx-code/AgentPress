import asyncio
from typing import Dict, Any
from core.agent_manager import AgentManager
from core.conversation_manager import ConversationManager
from utils import extract_content, extract_all_json


class ResearchPhaseManager:
    """专门处理研究与规划阶段的类，从NovelWritingPhases中分离出来"""

    def __init__(self, conversation_manager: ConversationManager, agent_manager: AgentManager):
        self.conversation_manager = conversation_manager
        self.agent_manager = agent_manager

    async def execute_research_phase(self, novel_concept: str) -> Dict[str, Any]:
        """执行研究和规划阶段的完整流程"""
        print("\n" + "="*60)
        print("📚 第一阶段：创意研究和规划")
        print("="*60)

        if not self.agent_manager:
            # Fallback implementation
            return {
                "outline": f"基于 {novel_concept} 的大纲",
                "world_setting": "山海经世界观",
                "character_profiles": [],
                "key_conflicts": [],
                "research_data": f"背景研究：{novel_concept}"
            }

        from config import GROUPCHAT_CONFIGS
        config = GROUPCHAT_CONFIGS["research_phase"]
        agent_list = self.agent_manager.get_agents(config["agents"])

        print(f"\n🔧 GroupChat 配置:")
        print(f"   Agents: {[agent.name for agent in agent_list]}")
        print(f"   Max turns: {config['max_turns']}")

        # Sequential research and planning
        mythologist = self.agent_manager.get_agent("mythologist")
        writer = self.agent_manager.get_agent("writer")

        if mythologist:
            myth_task = f"分析这个网络小说创意的世界观设定：{novel_concept}\n返回JSON格式的分析结果。"
            myth_result = await mythologist.run(task=myth_task)
            myth_content = extract_content(myth_result.messages)
        else:
            myth_content = ""

        if writer:
            research_summary = myth_content if myth_content else novel_concept
            writer_task = f"""
根据以下背景信息设计故事大纲：{research_summary}

创意需求：{novel_concept}

请设计：
1. 故事的三幕结构
2. 主要角色及性格
3. 核心冲突和转折点
4. 预期的故事走向

返回JSON格式。
            """

            writer_result = await writer.run(task=writer_task)
            writer_content = extract_content(writer_result.messages)
        else:
            writer_content = ""

        conversation = (myth_content if myth_content else '') + "\n---\n" + (writer_content if writer_content else '')
        self.conversation_manager.add_conversation("phase1_research", conversation)

        # Extract actual research data
        combined_json = {}
        for content in [myth_content, writer_content]:
            if content:
                json_objects = extract_all_json(content)
                for json_obj in json_objects:
                    if isinstance(json_obj, dict):
                        combined_json.update(json_obj)

        # 提取目标字数信息并更新结果
        target_length_info = combined_json.get("target_length")
        if target_length_info and isinstance(target_length_info, dict):
            suggested_length = target_length_info.get("suggested")
            length_units = target_length_info.get("units", "chinese_characters")

            if suggested_length and isinstance(suggested_length, (int, float)):
                if length_units == "chinese_characters" or "字" in str(suggested_length) or "汉字" in str(novel_concept):
                    # 更新AI对配置管理器的访问，以便在当前实例中也能更新配置（如果有）
                    if hasattr(self, 'conversation_manager'):
                        from core.config_manager import ConfigManager
                        try:
                            config_manager = ConfigManager()
                            current_config = config_manager.get_creation_config()

                            # 优先使用AI识别的目标长度，但只在用户明显表达要求时
                            current_config["min_chinese_chars"] = int(suggested_length)
                            current_config["total_target_length"] = int(suggested_length) * 1.2  # 留20%空间以确保达到目标

                            print(f"🎯 AI从用户概念中识别到目标字数: {suggested_length} 汉字")
                            print(f"   配置已自动更新以匹配用户要求")
                        except:
                            # 如果上面失败，至少记录AI的建议
                            pass

        # 确保我们有默认值
        result = {
            "outline": combined_json.get("outline", f"基于 {novel_concept} 的大纲"),
            "world_setting": combined_json.get("world_setting", "山海经世界观"),
            "character_profiles": combined_json.get("character_profiles", [
                {"name": "主角", "role": "hero", "trait": "勇敢"}
            ]),
            "key_conflicts": combined_json.get("key_conflicts", ["初期冲突"]),
            "research_data": combined_json.get("research_data", f"背景研究：{novel_concept}"),
            "background": combined_json.get("background", f"背景设定：{novel_concept}"),
            "target_length_suggestion": target_length_info
        }

        # 添加会议纪要在研究阶段完成时
        participants = []
        if mythologist:
            participants.append("mythologist")
        if writer:
            participants.append("writer")

        summary = f"研究阶段完成，mythologist分析了故事世界观设定，writer设计了故事大纲，包含角色、冲突和情节走向"

        # 检查并添加会议纪要
        if hasattr(self.conversation_manager, 'add_meeting_minutes'):
            self.conversation_manager.add_meeting_minutes(
                stage="research_phase",
                participants=participants,
                summary=summary,
                decisions=[
                    f"世界观设定: {result.get('world_setting', '未指定')}",
                    f"主要角色: {[char.get('name', '未知') for char in result.get('character_profiles', []) if isinstance(char, dict)]}",
                    f"核心冲突: {', '.join(result.get('key_conflicts', ['未指定']))}",
                    f"故事大纲: {result.get('outline', '未指定')[:100]}..."
                ],
                turn_count=2  # mythologist 和 writer 讨论轮次
            )

            # 实时保存阶段性报告
            if hasattr(self.conversation_manager, 'save_interim_report'):
                self.conversation_manager.save_interim_report("research_phase")

        print(f"✅ 研究阶段完成")
        print(f"   提取字段: {list(result.keys())}")

        return result