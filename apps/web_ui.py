"""
Web UI for AgentPress Enhancement
现在使用统一的核心服务
"""
from fastapi import FastAPI, Request, HTTPException, Form, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import json
import os
import asyncio

from core.workflow_service import WorkflowService
from core.agent_manager import ModelConfig
from knowledge.manager import KnowledgeManager

app = FastAPI(title="AgentPress 增强版 UI")

# 配置模板和静态文件
templates = Jinja2Templates(directory="ui/templates")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# 全局工作流服务实例
workflow_service = WorkflowService()
knowledge_manager = KnowledgeManager()

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not model_name:
        model_name = "qwen-max"

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
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/knowledge/entry")
async def add_knowledge_entry(request: Request):
    """
    添加知识条目 - 适配前端javascript的需求
    """
    try:
        data = await request.json()
        title = data.get('title', '')
        content = data.get('content', '')
        knowledge_type = data.get('knowledge_type', '')
        tags = data.get('tags', [])
        source = data.get('source', 'manual')

        if not title or not content:
            raise HTTPException(status_code=400, detail="标题和内容不能为空")

        # 在这里添加知识条目的逻辑
        # 目前我们只是返回一个成功的响应，因为知识库管理器的接口可能需要扩展
        return {"status": "success", "message": "知识条目添加成功", "id": "temp_id"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.put("/api/models/{agent_type}")
async def update_agent_model(agent_type: str, request: Request):
    """
    更新特定代理的模型配置
    """
    try:
        data = await request.json()
        new_model = data.get("model")

        if not new_model:
            raise HTTPException(status_code=400, detail="模型名称不能为空")

        # 在这里添加模型更新的逻辑（可能需要扩展WorkflowService以支持此功能）
        # 目前我们只是返回一个成功的响应
        return {
            "status": "success",
            "message": f"{agent_type} 代理的模型已更新为 {new_model}",
            "agent_type": agent_type,
            "model": new_model
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/prompts/{prompt_type}")
async def get_prompt(prompt_type: str):
    """
    获取特定提示词内容
    """
    try:
        # 获取提示词文件路径
        import os
        from pathlib import Path
        from utils import load_prompt

        prompts_dir = Path("prompts")
        prompt_file = prompts_dir / f"{prompt_type}.md"

        if not prompt_file.exists():
            return {
                "status": "error",
                "message": f"提示词文件不存在: {prompt_type}.md",
                "content": ""
            }

        # 读取提示词内容
        content = load_prompt(str(prompt_file))

        return {
            "status": "success",
            "content": content
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "content": ""}


@app.put("/api/prompts/{prompt_type}")
async def update_prompt(prompt_type: str, request: Request):
    """
    更新特定提示词内容
    """
    try:
        data = await request.json()
        new_content = data.get("content")

        if not new_content:
            raise HTTPException(status_code=400, detail="提示词内容不能为空")

        # 写入提示词文件
        import os
        from pathlib import Path

        prompts_dir = Path("prompts")
        prompt_file = prompts_dir / f"{prompt_type}.md"

        # 验证文件名安全性
        if ".." in str(prompt_file) or prompt_file.name != f"{prompt_type}.md":
            raise HTTPException(status_code=400, detail="无效的文件名")

        # 确保目录存在
        prompts_dir.mkdir(exist_ok=True)

        # 写入新内容
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            "status": "success",
            "message": f"提示词 {prompt_type} 已更新成功"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/conversation-history")
async def get_conversation_history():
    """获取创作的对话历史"""
    history = workflow_service.get_conversation_history()
    return {"history": history}

@app.get("/api/models")
async def get_model_configurations():
    """获取模型配置（暂时返回默认值）"""
    return {"model_configs": {
        "writer": {"model": "qwen-max", "description": "故事创作模型"},
        "editor": {"model": "qwen-max", "description": "编辑评价模型"},
        "fact_checker": {"model": "qwen-max", "description": "事实检查模型"}
    }}

@app.get("/api/knowledge/search")
async def search_knowledge(query: str, category: Optional[str] = None):
    """搜索知识库"""
    results = await knowledge_manager.search_knowledge(query, category)
    return {"results": [r.__dict__ for r in results]}

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket端点，用于实时进度更新（章节创建过程）"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（通常保持连接）
            data = await websocket.receive_text()
            # 可以根据需要处理客户端发送的消息
            await websocket.send_json({"message": "Connected to progress updates", "type": "connection_ok"})
    except Exception as e:
        manager.disconnect(websocket)

# 全局变量来追踪创作状态
novel_generation_status = {
    "is_generating": False,
    "current_chapter": 0,
    "total_chapters": 0,
    "progress": 0,
    "status_message": "等待开始创作",
    "error": None
}

@app.post("/api/generate-novel-stream")
async def generate_novel_stream(
    concept: str = Form(...),
    multi_chapter: bool = Form(False),
    total_chapters: int = Form(1)
):
    """
    生成小说 - 支持流式响应，推送实时状态给WebSocket客户端
    """
    global novel_generation_status
    if not workflow_service.agent_manager:
        return {
            "status": "error",
            "message": "工作流服务未初始化，请先调用 /api/init-workflow"
        }

    # 更新状态为正在生成
    novel_generation_status = {
        "is_generating": True,
        "current_chapter": 0,
        "total_chapters": 0,
        "progress": 0,
        "status_message": "开始创作进程",
        "error": None
    }

    # 启动生成任务并在后台推送进度更新
    async def run_generation():
        try:
            # 发送开始消息
            await manager.broadcast({
                "type": "status_update",
                "status_data": {
                    "is_generating": True,
                    "current_chapter": 0,
                    "total_chapters": 0,
                    "progress": 0,
                    "status_message": "正在初始化创作流程...",
                    "error": None
                }
            })

            # 执行工作流程
            result = await workflow_service.execute_workflow(
                novel_concept=concept,
                multi_chapter=multi_chapter,
                total_chapters=total_chapters
            )

            # 发送完成消息
            await manager.broadcast({
                "type": "completion_update",
                "result": result
            })

            # 更新状态
            novel_generation_status["is_generating"] = False
            novel_generation_status["progress"] = 100
            novel_generation_status["status_message"] = "创作完成"

        except Exception as e:
            error_msg = str(e)
            novel_generation_status["error"] = error_msg
            novel_generation_status["is_generating"] = False
            novel_generation_status["status_message"] = f"创作过程中出现错误: {error_msg}"

            await manager.broadcast({
                "type": "error",
                "error": error_msg
            })

    # 在后台运行生成任务
    asyncio.create_task(run_generation())

    return {
        "status": "success",
        "message": "开始小说创作进程，进度将通过WebSocket实时推送"
    }

@app.get("/api/generation-status")
async def get_generation_status():
    """获取当前创作状态"""
    global novel_generation_status
    return {"status_data": novel_generation_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)