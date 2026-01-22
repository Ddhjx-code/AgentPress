from fastapi import APIRouter, HTTPException
from typing import Dict
from core.agent_manager import ModelConfig

router = APIRouter()
model_config = ModelConfig()

@router.get("/models")
async def get_model_types():
    """Get all available agent and their model configurations"""
    return {"models": model_config.model_configs}

@router.get("/models/{agent_type}")
async def get_model_config(agent_type: str):
    """Get model configuration for a specific agent type"""
    if agent_type not in model_config.model_configs:
        raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")

    return {"agent_type": agent_type, "config": model_config.model_configs[agent_type]}

@router.put("/models/{agent_type}")
async def update_model_config(agent_type: str, config: Dict):
    """Update model configuration for specific agent"""
    if agent_type not in model_config.model_configs:
        raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")

    # Update the configuration - for now we'll just log this as a sample
    # In a real implementation, you might update specific config properties
    return {"agent_type": agent_type, "updated_config": config}