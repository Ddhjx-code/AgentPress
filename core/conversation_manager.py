from typing import Dict, Any, List
from datetime import datetime
from utils import extract_content, extract_all_json, calculate_average_score


class ConversationManager:
    """管理对话和版本历史"""

    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.story_versions: List[Dict[str, Any]] = []
        self.feedback_records: List[Dict[str, Any]] = []
        self.documentation_records: List[Dict[str, Any]] = []  # ✅ 已添加
        self.meeting_minutes: List[Dict[str, Any]] = []  # 会议纪要（代理讨论摘要）
        self.phase_summaries: List[Dict[str, Any]] = []  # 阶段摘要

    def add_conversation(self, phase: str, conversation: str, metadata: Dict = None):
        """添加对话记录"""
        record = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "conversation": conversation,
            "length": len(conversation),
            "metadata": metadata or {}
        }
        self.conversation_history.append(record)

    def add_documentation(self, chapter_num: int, extraction_info: Dict,
                         consistency_check: Dict):
        """记录档案员的提取和检查结果"""
        self.documentation_records.append({  # ✅ 现在可以正确使用
            "chapter_num": chapter_num,
            "timestamp": datetime.now().isoformat(),
            "extraction": extraction_info,      # 提取的人物、时间线等
            "consistency_check": consistency_check  # 一致性检查结果
        })

    def add_story_version(self, version: int, content: str, metadata: Dict = None):
        """添加故事版本"""
        record = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "length": len(content),
            "metadata": metadata or {}
        }
        self.story_versions.append(record)


    def add_meeting_minutes(self, stage: str, participants: List[str], summary: str,
                          decisions: List[str] = None, duration: int = 0, turn_count: int = 0):
        """
        添加会议纪要（代理讨论过程摘要）

        Args:
            stage: 讨论阶段（如 'research_phase', 'collaboration_1'）
            participants: 参与讨论的代理列表
            summary: 讨论内容的简洁摘要
            decisions: 达成的主要决策列表
            duration: 讨论持续时间（秒）
            turn_count: 对话轮次总数
        """
        record = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "participants": participants,
            "summary": summary,
            "decisions": decisions or [],
            "duration": duration,
            "turn_count": turn_count,
            "agent_interactions": len(participants)
        }
        self.meeting_minutes.append(record)
        print(f"📋 会议纪要: {stage} | 参与者: {', '.join(participants[:3])}{'...' if len(participants) > 3 else ''}")
        print(f"   摘要: {summary[:150]}{'...' if len(summary) > 150 else ''}")

    def add_phase_summary(self, phase: str, status: str, summary: str,
                         agent_reports: List[Dict[str, str]] = None,
                         metrics: Dict[str, Any] = None):
        """
        添加阶段总结

        Args:
            phase: 阶段名称
            status: 阶段状态（success, failed, completed等）
            summary: 阶段总结
            agent_reports: 各代理的报告
            metrics: 阶段相关统计指标
        """
        record = {
            "phase": phase,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "agent_reports": agent_reports or [],
            "metrics": metrics or {}
        }
        self.phase_summaries.append(record)

    def add_feedback(self, round_num: int, feedback: Dict[str, Any], metadata: Dict = None):
        """添加反馈记录"""
        # 只计算有效的评分
        valid_scores = [
            data.get("score")
            for data in feedback.values()
            if isinstance(data, dict) and isinstance(data.get("score"), (int, float))
        ]

        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

        record = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "avg_score": avg_score,
            "valid_scores_count": len(valid_scores),
            "metadata": metadata or {}
        }
        self.feedback_records.append(record)


    def get_story_version(self, version: int) -> str:
        """获取指定版本的故事"""
        for record in self.story_versions:
            if record["version"] == version:
                return record["content"]
        return ""

    def get_latest_story(self) -> str:
        """获取最新版本的故事"""
        if self.story_versions:
            return self.story_versions[-1]["content"]
        return ""

    def get_meeting_minutes_summary(self) -> List[Dict[str, Any]]:
        """获取会议纪要摘要"""
        return [
            {
                "stage": meeting["stage"],
                "timestamp": meeting["timestamp"],
                "summary": meeting["summary"],
                "participants": meeting["participants"],
                "decisions": meeting["decisions"],
                "turns": meeting.get("turn_count", 0)
            }
            for meeting in self.meeting_minutes
        ]

    def get_phase_summaries(self) -> List[Dict[str, Any]]:
        """获取所有阶段摘要"""
        return [
            {
                "phase": summary["phase"],
                "status": summary["status"],
                "timestamp": summary["timestamp"],
                "summary": summary["summary"],
                "metric_count": len(summary["metrics"])
            }
            for summary in self.phase_summaries
        ]

    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "total_conversations": len(self.conversation_history),
            "total_versions": len(self.story_versions),
            "total_feedback_rounds": len(self.feedback_records),
            "total_documentation_records": len(self.documentation_records),  # ✅ 新增
            "total_meeting_minutes": len(self.meeting_minutes),  # 会议纪要总数
            "total_phase_summaries": len(self.phase_summaries),  # 阶段总结总数
            "avg_scores": [r["avg_score"] for r in self.feedback_records],
            "meeting_participants": list(set(
                agent for meeting in self.meeting_minutes
                for agent in meeting["participants"]
            ))
        }

    def get_all_history(self) -> Dict[str, Any]:
        """获取完整的对话历史"""
        return {
            "conversations": self.conversation_history,
            "versions": self.story_versions,
            "feedbacks": self.feedback_records,
            "documentations": self.documentation_records,
            "meeting_minutes": self.meeting_minutes,  # 会议纪要
            "phase_summaries": self.phase_summaries  # 阶段总结
        }

    def print_meeting_minutes_summary(self):
        """在控制台上打印会议纪要摘要"""
        if not self.meeting_minutes:
            print("📋 暂无会议记录")
            return

        print("\n" + "="*60)
        print("📋 AI代理协作过程摘要")
        print("="*60)

        for i, meeting in enumerate(self.meeting_minutes, 1):
            print(f"{i:2d}. 阶段: {meeting['stage']}")
            print(f"     时间: {meeting['timestamp']}")
            print(f"     参与: {', '.join(meeting['participants'])}")
            print(f"     摘要: {meeting['summary'][:120]}{'...' if len(meeting['summary']) > 120 else ''}")
            if meeting['decisions']:
                for decision in meeting['decisions']:
                    print(f"     → {decision[:100]}{'...' if len(decision) > 100 else ''}")
            print(f"     轮次: {meeting.get('turn_count', 0)}")
            print()

        print(f"总计: {len(self.meeting_minutes)} 个会议纪要记录")

    def save_meeting_minutes_to_file(self, output_dir: str = "output", file_prefix: str = "meeting_minutes"):
        """保存会议纪要到文件，支持自定义前缀以避免覆盖"""
        import json
        from pathlib import Path
        from datetime import datetime

        if not self.meeting_minutes:
            print("📋 暂无会议记录可保存")
            return

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成带时间戳和自定义前缀的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"{file_prefix}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.meeting_minutes, f, ensure_ascii=False, indent=2)

        print(f"📁 会议纪要已保存到: {filename}")

        # 也保存一份文本格式便于阅读
        txt_filename = output_path / f"{file_prefix}_summary_{timestamp}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("AI代理协作过程摘要\n")
            f.write("="*60 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"会议记录总数: {len(self.meeting_minutes)}\n\n")

            for i, meeting in enumerate(self.meeting_minutes, 1):
                f.write(f"{i:2d}. 阶段: {meeting['stage']}\n")
                f.write(f"     时间: {meeting['timestamp']}\n")
                f.write(f"     参与: {', '.join(meeting['participants'])}\n")
                f.write(f"     摘要: {meeting['summary']}\n")
                if meeting['decisions']:
                    for decision in meeting['decisions']:
                        f.write(f"     → {decision}\n")
                f.write(f"     轮次: {meeting.get('turn_count', 0)}\n")
                f.write("\n")

        print(f"📄 会议纪要文本摘要已保存到: {txt_filename}")

    def save_meeting_minutes_at_stage(self, stage_name: str, output_dir: str = "output"):
        """在特定阶段结束后保存会议纪要"""
        if not self.meeting_minutes:
            return

        # 只保存到当前阶段的会议纪要
        current_meetings = [m for m in self.meeting_minutes if m['stage'].startswith(stage_name.lower().replace(' ', '_'))]
        if not current_meetings:
            return

        import json
        from pathlib import Path
        from datetime import datetime

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"stage_{stage_name.replace(' ', '_').lower()}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(current_meetings, f, ensure_ascii=False, indent=2)

        print(f"📁 阶段 '{stage_name}' 的会议纪要已保存到: {filename}")

    def save_interim_report(self, stage_name: str, output_dir: str = "output"):
        """保存阶段性报告"""
        import json
        from pathlib import Path
        from datetime import datetime

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 创建阶段性数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        interim_data = {
            "stage": stage_name,
            "timestamp": datetime.now().isoformat(),
            "meeting_minutes_count": len(self.meeting_minutes),
            "current_meeting_minutes": self.meeting_minutes[-3:] if len(self.meeting_minutes) >= 3 else self.meeting_minutes,  # 最近的会议纪要
            "total_conversations": len(self.conversation_history),
            "total_versions": len(self.story_versions),
            "total_feedback_rounds": len(self.feedback_records)
        }

        filename = output_path / f"interim_report_{stage_name.replace(' ', '_').lower()}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(interim_data, f, ensure_ascii=False, indent=2)

        print(f"📊 阶段中间报告已保存到: {filename}")

        # 保存阶段性会议摘要
        if self.meeting_minutes:
            txt_filename = output_path / f"interim_summary_{stage_name.replace(' ', '_').lower()}_{timestamp}.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write(f"阶段性会议纪要摘要: {stage_name}\n")
                f.write("="*60 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"截至当前总会议记录数: {len(self.meeting_minutes)}\n\n")

                # 仅输出最近的会议
                recent_meetings = self.meeting_minutes[-3:] if len(self.meeting_minutes) >= 3 else self.meeting_minutes
                for i, meeting in enumerate(recent_meetings, 1):
                    f.write(f"{i:2d}. 阶段: {meeting['stage']}\n")
                    f.write(f"     时间: {meeting['timestamp']}\n")
                    f.write(f"     参与: {', '.join(meeting['participants'])}\n")
                    f.write(f"     摘要: {meeting['summary'][:120]}{'...' if len(meeting['summary']) > 120 else ''}\n")
                    if meeting['decisions']:
                        for decision in meeting['decisions']:
                            f.write(f"     → {decision[:100]}{'...' if len(decision) > 100 else ''}\n")
                    f.write(f"     轮次: {meeting.get('turn_count', 0)}\n")
                    f.write("\n")

            print(f"📋 阶段中间摘要已保存到: {txt_filename}")