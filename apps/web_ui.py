"""
简化版 Web UI - 仅保留核心小说生成功能
"""
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import json
import os
import asyncio

from core.workflow_service import WorkflowService

app = FastAPI(title="AgentPress 小说生成服务")

# 配置模板和静态文件（若存在）
if os.path.exists("ui/templates"):
    templates = Jinja2Templates(directory="ui/templates")
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
else:
    # 创建最小化模板处理器
    class MockTemplate:
        @staticmethod
        def TemplateResponse(name, context):
            return HTMLResponse(content="<h1>AgentPress 小说生成服务</h1>")

    templates = MockTemplate()

# 全局工作流服务实例
workflow_service = WorkflowService()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if os.path.exists("ui/templates/index.html"):
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(content="<h1>AgentPress 核心小说生成服务</h1><p>服务正在运行</p>")

@app.post("/api/init-workflow")
async def initialize_workflow(
    api_key: str = Form(...),
    base_url: str = Form(None),
    model_name: str = Form(None)
):
    """
    初始化工作流服务
    """
    if not base_url:
        base_url = "https://apis.iflow.cn/v1"
    if not model_name:
        model_name = "qwen3-max"

    try:
        await workflow_service.initialize_models(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        return {"status": "success", "message": "工作流服务初始化成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-novel")
async def generate_novel(
    concept: str = Form(...),
    multi_chapter: bool = Form(False),
    total_chapters: int = Form(1)
):
    """
    生成小说 - 调用统一的核心工作流
    """
    if not workflow_service.agent_manager:
        return {
            "status": "error",
            "message": "工作流服务未初始化，请先调用 /api/init-workflow"
        }

    try:
        result = await workflow_service.execute_workflow(
            novel_concept=concept,
            multi_chapter=multi_chapter,
            total_chapters=total_chapters
        )

        # 添加代理工作日志到返回结果中
        if hasattr(workflow_service, 'get_conversation_manager') and workflow_service.get_conversation_manager():
            conv_manager = workflow_service.get_conversation_manager()
            if hasattr(conv_manager, 'get_all_history'):
                result["conversation_history"] = conv_manager.get_all_history()

        # 如果workflow_service有novel_phases_manager，添加代理工作日志
        if hasattr(workflow_service, 'novel_phases_manager') and workflow_service.novel_phases_manager:
            if hasattr(workflow_service.novel_phases_manager, 'get_agent_work_summary'):
                result["agent_work_log"] = workflow_service.novel_phases_manager.get_agent_work_summary()

        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/conversation-history")
async def get_conversation_history():
    """获取创作的对话历史"""
    history = workflow_service.get_conversation_history()
    return {"history": history}

@app.get("/api/models")
async def get_model_configurations():
    """获取模型配置（简化版）"""
    return {"model_configs": {
        "writer": {"model": "qwen3-max", "description": "故事创作模型"},
        "editor": {"model": "qwen3-max", "description": "编辑评价模型"},
        "fact_checker": {"model": "qwen3-max", "description": "事实检查模型"}
    }}

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "novel-generation-core"}

# WebSocket支持（简化版，用于进度更新）
import logging
logger = logging.getLogger("uvicorn")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)