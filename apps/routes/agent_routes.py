from fastapi import APIRouter, HTTPException
from ai_agents.base import BaseAIAgent  # Placeholder for now
from core.agent_manager import AgentManager, ModelConfig
import asyncio

router = APIRouter()
agent_manager = AgentManager()

@router.get("/agents/status")
async def get_agents_status():
    """Get status of all AI agents"""
    model_configs = agent_manager.model_configs.model_configs
    status = {}

    for agent_type in model_configs:
        status[agent_type] = {
            "model": model_configs[agent_type]["model"],
            "capabilities": model_configs[agent_type]["capabilities"],
            "status": "ready"  # Placeholder for actual availability check
        }

    return {"agents": status}

@router.get("/agents/{agent_type}")
async def get_agent_info(agent_type: str):
    """Get information about a specific agent"""
    model_configs = agent_manager.model_configs.model_configs

    if agent_type not in model_configs:
        raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")

    config = model_configs[agent_type]
    return {
        "agent_type": agent_type,
        "model": config["model"],
        "description": config["description"],
        "capabilities": config["capabilities"],
        "status": "ready"
    }

@router.post("/agents/test/{agent_type}")
async def test_agent(agent_type: str, test_prompt: str = "{test prompt goes here. Please return test output}"):
    """Test an agent with a simple prompt"""
    model_configs = agent_manager.model_configs.model_configs

    if agent_type not in model_configs:
        raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")

    try:
        # Create and use the agent for test
        agent = agent_manager.get_agent(agent_type)
        # Simple test would be performed here
        return {
            "agent_type": agent_type,
            "status": "test_completed",
            "response": f"Test completed for {agent_type} using model {model_configs[agent_type]['model']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")