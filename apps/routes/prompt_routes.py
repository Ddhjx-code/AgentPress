from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import Dict, List
import os
import json
from pathlib import Path

router = APIRouter()

@router.get("/prompts/{agent_type}")
async def get_prompt(agent_type: str):
    """Get prompt for a specific agent type"""
    prompt_file_path = f"prompts/{agent_type}.md"

    if not os.path.exists(prompt_file_path):
        # Also try the original naming format
        mapping = {
            "mythologist": "mythologist",
            "writer": "writer",
            "fact_checker": "fact_checker",
            "dialogue_specialist": "dialogue_specialist",
            "editor": "editor",
            "documentation_specialist": "documentation_specialist"
        }
        agent_short = mapping.get(agent_type)
        if agent_short:
            prompt_file_path = f"prompts/{agent_short}.md"

    if not os.path.exists(prompt_file_path):
        # Return default templates if files don't exist
        default_templates = {
            "writer": "You are a creative story writer...",
            "editor": "You are a professional editor...",
            "fact_checker": "You are a logical fact checker...",
            # etc for all agent types
        }
        # If not even a default is found
        content = default_templates.get(agent_type, f"Default prompt for {agent_type}")
        return {"agent_type": agent_type, "content": content, "path": prompt_file_path}

    with open(prompt_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"agent_type": agent_type, "content": content, "path": prompt_file_path}

@router.put("/prompts/{agent_type}")
async def update_prompt(agent_type: str, content: str):
    """Update prompt for a specific agent type"""
    # Map the agent type to proper file name
    mapping = {
        "mythologist": "mythologist",
        "writer": "writer",
        "fact_checker": "fact_checker",
        "dialogue_specialist": "dialogue_specialist",
        "editor": "editor",
        "documentation_specialist": "documentation_specialist"
    }

    agent_short = mapping.get(agent_type)
    if not agent_short:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    prompt_file_path = f"prompts/{agent_short}.md"

    # Ensure directory exists
    os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)

    with open(prompt_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"agent_type": agent_type, "updated": True, "path": prompt_file_path}

@router.get("/prompt/templates")
async def get_prompt_templates():
    """Get available prompt templates"""
    templates_dir = Path("prompts/templates")
    if templates_dir.exists():
        templates = []
        for file in templates_dir.glob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                templates.append({
                    "name": file.name.replace('.md', ''),
                    "path": str(file),
                    "content_preview": content[:100] + "..." if len(content) > 100 else content
                })
        return {"templates": templates}
    return {"templates": []}