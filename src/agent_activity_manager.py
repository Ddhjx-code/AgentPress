"""Agent activity management module for tracking and visualizing agent work across phases."""

import json
import time
from typing import Dict, List, Any
from pathlib import Path


class AgentActivityManager:
    """Core agent activity management functionality"""

    def __init__(self):
        self.agent_work_log = []  # Log to store all agent activities
        # 导入配置管理器
        try:
            from core.config_manager import ConfigManager
            self.config_manager = ConfigManager()
        except ImportError:
            # 如果没有配置管理器，则使用原始配置
            self.config_manager = None

    def log_agent_activity(self, phase: str, agent_name: str, task: str, result: str, metadata: dict = None):
        """Log agent activity for tracking and reporting"""
        activity = {
            "timestamp": time.time(),
            "phase": phase,
            "agent_name": agent_name,
            "task": task,
            "result_summary": result[:200] + "..." if len(result) > 200 else result,  # 简短摘要
            "result_full": result,
            "metadata": metadata or {}
        }
        self.agent_work_log.append(activity)

    def get_agent_work_summary(self) -> list:
        """Get summary of all agent activities"""
        return self.agent_work_log

    def get_web_visualization_data(self) -> dict:
        """Generate data for web visualization of agent activities"""
        if not self.agent_work_log:
            return {
                "error": "No agent work log available"
            }

        # Group activities by agent
        agent_activities = {}
        for activity in self.agent_work_log:
            agent_name = activity["agent_name"]
            if agent_name not in agent_activities:
                agent_activities[agent_name] = {
                    "display_name": self._get_agent_display_name(agent_name),
                    "activities": []
                }
            agent_activities[agent_name]["activities"].append({
                "phase": activity["phase"],
                "task_summary": activity["task"][:100] + "..." if len(activity["task"]) > 100 else activity["task"],
                "result_summary": activity["result_summary"],
                "timestamp": activity["timestamp"],
                "metadata": activity["metadata"]
            })

        # Generate phase summary
        phase_summary = {}
        for activity in self.agent_work_log:
            phase = activity["phase"]
            if phase not in phase_summary:
                phase_summary[phase] = {"count": 0, "agents": set()}
            phase_summary[phase]["count"] += 1
            phase_summary[phase]["agents"].add(activity["agent_name"])

        # Convert sets to lists for JSON serialization
        for phase in phase_summary:
            phase_summary[phase]["agents"] = list(phase_summary[phase]["agents"])

        web_data = {
            "timeline": [
                {
                    "timestamp": activity["timestamp"],
                    "agent": self._get_agent_display_name(activity["agent_name"]),
                    "agent_key": activity["agent_name"],
                    "phase": activity["phase"].replace("_", " ").title(),
                    "task": activity["task"][:80] + "..." if len(activity["task"]) > 80 else activity["task"],
                    "result": activity["result_summary"][:120] + "..." if len(activity["result_summary"]) > 120 else activity["result_summary"]
                }
                for activity in self.agent_work_log
            ],
            "agent_activities": agent_activities,
            "phase_summary": phase_summary,
            "summary_stats": {
                "total_activities": len(self.agent_work_log),
                "total_agents": len(agent_activities),
                "phases_covered": list(phase_summary.keys()),
                "agents_involved": list(agent_activities.keys())
            }
        }

        return web_data

    def _get_agent_display_name(self, agent_name: str) -> str:
        """Get display name for agent"""
        from config import AGENT_CONFIGS
        return AGENT_CONFIGS.get(agent_name, {}).get("display_name", agent_name)

    def save_agent_work_log(self, output_dir: str = "output"):
        """Save agent work log to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 保存详细的日志
        log_file = output_path / "agent_work_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.agent_work_log, f, ensure_ascii=False, indent=2)

        # 创建汇总报告
        summary_data = {
            "total_activities": len(self.agent_work_log),
            "agents_involved": list(set([activity["agent_name"] for activity in self.agent_work_log])),
            "phases_covered": list(set([activity["phase"] for activity in self.agent_work_log])),
            "work_summary": self.agent_work_log
        }

        summary_file = output_path / "agent_work_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        # 保存web可视化数据
        web_data = self.get_web_visualization_data()
        web_file = output_path / "agent_work_web_data.json"
        with open(web_file, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2)

        return str(log_file), str(summary_file), str(web_file)