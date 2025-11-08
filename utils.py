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
    """计算平均评分"""
    scores = []
    for item in feedback.values():
        if isinstance(item, dict) and "score" in item:
            scores.append(item["score"])
    
    return sum(scores) / len(scores) if scores else 0

def format_feedback_summary(feedback: Dict[str, Any]) -> str:
    """格式化反馈摘要"""
    summary = []
    for reviewer, data in feedback.items():
        if isinstance(data, dict):
            score = data.get("score", "N/A")
            issues = data.get("issues", [])
            summary.append(f"  • {reviewer}: 分数 {score} - {issues[0] if issues else '通过'}")
    
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
