"""
过程可视化助手 - 管理和输出代理协作过程
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from core.conversation_manager import ConversationManager


class ProcessVisualizer:
    """过程可视化辅助类"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def visualize_meeting_minutes(self, conversation_manager: ConversationManager, output_type: str = "both"):
        """
        可视化会议纪要

        Args:
            conversation_manager: 对话管理器
            output_type: 输出类型 - 'console', 'file', 'both'
        """
        meeting_minutes = conversation_manager.get_meeting_minutes_summary()

        if not meeting_minutes:
            if output_type in ['console', 'both']:
                print("📋 暂无会议记录")
            return

        # 准备输出内容
        output_content = []
        output_content.append("=" * 60)
        output_content.append("📋 代理协作过程可视化报告")
        output_content.append("=" * 60)
        output_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_content.append(f"会议记录总数: {len(meeting_minutes)}")
        output_content.append("")

        for i, meeting in enumerate(meeting_minutes, 1):
            output_content.append(f"{i:2d}. 阶段: {meeting['stage']}")
            output_content.append(f"    时间: {meeting['timestamp']}")
            output_content.append(f"    参与: {', '.join(meeting['participants'])}")
            output_content.append(f"    摘要: {meeting['summary']}")
            if meeting.get('decisions'):
                output_content.append(f"    决策: {', '.join(meeting['decisions'])}")
            output_content.append(f"    轮次: {meeting.get('turns', 0)}")
            output_content.append("")

        # 输出到控制台
        if output_type in ['console', 'both']:
            for line in output_content:
                print(line)

        # 输出到文件
        if output_type in ['file', 'both']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"meeting_minutes_summary_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_content))
            print(f"📁 会议纪要已保存到: {filename}")

    def visualize_detailed_participants(self, conversation_manager: ConversationManager, output_type: str = "both"):
        """输出详细的参与者和交互信息"""
        all_history = conversation_manager.get_all_history()
        meeting_minutes = all_history.get('meeting_minutes', [])

        if not meeting_minutes:
            if output_type in ['console', 'both']:
                print("📋 暂无详细的参与者记录")
            return

        output_content = []
        output_content.append("=" * 80)
        output_content.append("👥 代理详细参与者和交互分析")
        output_content.append("=" * 80)
        output_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 统计各代理的工作
        agent_participation = {}
        total_turns = 0
        total_meetings = len(meeting_minutes)

        for meeting in meeting_minutes:
            for agent in meeting['participants']:
                if agent not in agent_participation:
                    agent_participation[agent] = {
                        'count': 0,
                        'total_turns': 0,
                        'stages': []
                    }
                agent_participation[agent]['count'] += 1
                agent_participation[agent]['total_turns'] += meeting.get('turn_count', 0)
                agent_participation[agent]['stages'].append(meeting['stage'])

            total_turns += meeting.get('turn_count', 0)

        output_content.append(f"总交互次数: {total_meetings}")
        output_content.append(f"总对话轮次: {total_turns}")
        output_content.append(f"参与代理数: {len(agent_participation)}")
        output_content.append("")

        for agent, stats in agent_participation.items():
            output_content.append(f"🤖 {agent}:")
            output_content.append(f"   参与会议: {stats['count']} 次")
            output_content.append(f"   执行轮次: {stats['total_turns']} 轮")
            output_content.append(f"   参与阶段: {', '.join(stats['stages'])}")

            # 计算参与率
            participation_rate = (stats['count'] / total_meetings) * 100
            output_content.append(f"   参与率: {participation_rate:.1f}%")
            output_content.append("")

        # 完整会议记录
        output_content.append("-" * 80)
        output_content.append("📋 完整会议记录:")
        output_content.append("-" * 80)

        for i, meeting in enumerate(meeting_minutes, 1):
            output_content.append(f"{i:2d}. [{meeting['timestamp']}] {meeting['stage']}")
            output_content.append(f"    参与代理: {', '.join(meeting['participants'])}")
            output_content.append(f"    摘要: {meeting['summary'][:200]}{'...' if len(meeting['summary']) > 200 else ''}")
            if meeting['decisions']:
                for decision in meeting['decisions']:
                    output_content.append(f"    → {decision}")
            output_content.append("")

        # 输出到控制台
        if output_type in ['console', 'both']:
            for line in output_content:
                print(line)

        # 输出到文件
        if output_type in ['file', 'both']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"detailed_participation_analysis_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_content))
            print(f"📁 详细分析已保存到: {filename}")

    def save_complete_process_log(self, conversation_manager: ConversationManager):
        """保存完整的流程日志到JSON文件"""
        all_history = conversation_manager.get_all_history()

        # 添加可视化相关的时间戳
        all_history['visualizer_export_time'] = datetime.now().isoformat()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"complete_process_log_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_history, f, ensure_ascii=False, indent=2)

        print(f"📊 完整流程日志已保存到: {filename}")
        print(f"   - 会议纪要: {len(all_history.get('meeting_minutes', []))} 条")
        print(f"   - 对话记录: {len(all_history.get('conversations', []))} 条")
        print(f"   - 版本记录: {len(all_history.get('versions', []))} 条")
        print(f"   - 反馈记录: {len(all_history.get('feedbacks', []))} 条")
        print(f"   - 文档记录: {len(all_history.get('documentations', []))} 条")


# 创建一个全局实例
visualizer = ProcessVisualizer()