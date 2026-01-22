"""
Web UI for AgentPress Enhancement
"""
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import json
import os
from core.agent_manager import ModelConfig
from knowledge.manager import KnowledgeManager
from core.workflow import StoryWorkflow

app = FastAPI(title="AgentPress Enhanced UI")
templates = Jinja2Templates(directory="ui/templates")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Initialize services
model_config = ModelConfig()
knowledge_manager = KnowledgeManager()
# workflow = StoryWorkflow(knowledge_manager=knowledge_manager)  # We'll implement this in a later task

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/models")
async def get_model_configurations():
    """Endpoint to get available model configurations"""
    return {"model_configs": model_config.model_configs}

@app.get("/api/knowledge/search")
async def search_knowledge(query: str, category: Optional[str] = None):
    """Endpoint to search knowledge base"""
    results = await knowledge_manager.search_knowledge(query, category)
    return {"results": [r.__dict__ for r in results]}

# We'll add more routes in subsequent tasks