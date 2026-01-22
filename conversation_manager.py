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
    
    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "total_conversations": len(self.conversation_history),
            "total_versions": len(self.story_versions),
            "total_feedback_rounds": len(self.feedback_records),
            "total_documentation_records": len(self.documentation_records),  # ✅ 新增
            "avg_scores": [r["avg_score"] for r in self.feedback_records]
        }
