# utils.py
import re
import json
from pathlib import Path
from typing import Dict, Any, List

def load_prompt(file_path: str) -> str:
    """从 Markdown 文件加载提示词"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'```[a-z]*\n?', '', content)
            return content.strip()
    except FileNotFoundError:
        print(f"⚠️  找不到提示词文件: {file_path}")
        return ""

def load_all_prompts(prompts_dir: Path) -> Dict[str, str]:
    """加载所有提示词"""
    prompts = {}
    for prompt_file in prompts_dir.glob("*.md"):
        agent_name = prompt_file.stem
        prompts[agent_name] = load_prompt(str(prompt_file))
    return prompts

def extract_content(messages) -> str:
    """通用内容提取"""
    for msg in reversed(messages):
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            return msg.content
    return ""

def parse_json_response(response: str) -> dict:
    """安全解析 JSON 响应"""
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return {"raw_response": response}

def extract_all_json(text: str) -> List[Dict[str, Any]]:
    """从文本中提取所有JSON对象"""
    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
    results = []
    
    for match in json_matches:
        try:
            data = json.loads(match)
            results.append(data)
        except json.JSONDecodeError:
            continue
    
    return results

def calculate_average_score(feedback: Dict[str, Any]) -> float:
    """计算平均评分，兼容旧格式和新策略格式"""
    scores = []

    for item in feedback.values():
        if not isinstance(item, dict):
            continue

        # 尝试旧格式 - 直接包含 score 字段
        if "score" in item:
            scores.append(item["score"])
        elif "coherence_score" in item:
            # 新的设定评审格式，需转换为数值评分
            score_map = {"low": 50, "medium": 70, "high": 90}
            coherence = item["coherence_score"]
            if coherence in score_map:
                scores.append(score_map[coherence])
        elif "original_excerpt" in item or "setting_summary" in item:
            # 单段评审格式：根据logic_gaps数量计算评分
            gaps = item.get("logic_gaps", [])
            # 基础分为85，每发现一个重要逻辑缺口扣5分
            base_score = 85
            gap_penalty = len(gaps) * 5
            calculated_score = max(30, base_score - gap_penalty)  # 最低为30分
            scores.append(calculated_score)

    return sum(scores) / len(scores) if scores else 0

def format_feedback_summary(feedback: Dict[str, Any]) -> str:
    """格式化反馈摘要，兼容旧格式和新策略格式"""
    summary = []
    for reviewer, data in feedback.items():
        if isinstance(data, dict):
            if "score" in data:
                # 旧格式
                score = data.get("score", "N/A")
                issues = data.get("issues", [])
                summary.append(f"  • {reviewer}: 分数 {score} - {issues[0] if issues else '通过'}")
            elif "logic_gaps" in data or "unanchored_risks" in data:
                # 新格式 - fact_checker策略格式
                gaps = data.get("logic_gaps", [])
                risks = data.get("unanchored_risks", [])
                total_issues = len(gaps) + len(risks)
                score = calculate_average_score({reviewer: data})  # 计算新格式的分数
                summary.append(f"  • {reviewer}: 逻辑缺口/风险 {total_issues} 个 - 推荐策略 {len(data.get('recommended_additions', []))}")
            elif "original_excerpt" in data:
                # 新格式 - 单段评审格式
                gaps = data.get("logic_gaps", [])
                strategies = data.get("applied_strategies", [])
                score = calculate_average_score({reviewer: data})
                summary.append(f"  • {reviewer}: 发现逻辑缺口 {len(gaps)} 个 - 已用策略 {len(strategies)} 种")
            elif "setting_summary" in data:
                # 新格式 - 世界观设定评审格式
                unanchored_risks = data.get("unanchored_risks", [])
                recommendations = data.get("recommended_additions", [])
                summary.append(f"  • {reviewer}: 发现未锚定风险 {len(unanchored_risks)} 个 - 推荐策略 {len(recommendations)} 项")
            else:
                # 默认格式
                score = data.get("score", "N/A")
                summary.append(f"  • {reviewer}: 评分 {score if score != 'N/A' else '可用'}")

    return "\n".join(summary)

def save_json(data: Dict[str, Any], file_path: Path):
    """保存JSON文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {file_path}")

def save_text(content: str, file_path: Path):
    """保存文本文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已保存: {file_path}")
