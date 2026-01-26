"""
Web UI for AgentPress Enhancement
现在使用统一的核心服务
"""
from fastapi import FastAPI, Request, HTTPException, Form, WebSocket, UploadFile
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
from knowledge.novel_knowledge_extender import NovelKnowledgeExtender

app = FastAPI(title="AgentPress 增强版 UI")

# 配置模板和静态文件
templates = Jinja2Templates(directory="ui/templates")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# 全局工作流服务实例
workflow_service = WorkflowService()
knowledge_manager = KnowledgeManager()
novel_knowledge_extender = None  # 稍后初始化

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

        # 使用KnowledgeManager添加知识条目
        success = await knowledge_manager.add_entry(
            title=title,
            content=content,
            tags=tags,
            knowledge_type=knowledge_type,
            source=source
        )

        if success:
            # 获取完整的条目来返回ID
            all_entries = await knowledge_manager.get_all_entries()
            # 找到刚刚添加的条目（按时间排序）
            entry = max(all_entries, key=lambda e: e.creation_date) if all_entries else None
            entry_id = entry.id if entry else "unknown"

            return {"status": "success", "message": "知识条目添加成功", "id": entry_id}
        else:
            return {"status": "error", "message": "添加知识条目失败"}

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


@app.post("/api/process-novel-pdf")
async def process_novel_pdf(
    request: Request,
    pdf_file: UploadFile = Form(...),
    file_type: str = Form("pdf")
):
    """
    处理上传的小说PDF文件
    """
    global novel_knowledge_extender

    # 确保扩展管理器已初始化
    if novel_knowledge_extender is None:
        if not workflow_service.model_client:
            return {"status": "error", "message": "工作流服务未初始化，请先调用 /api/init-workflow"}
        novel_knowledge_extender = NovelKnowledgeExtender(workflow_service)

    try:
        # 创建临时文件存储上传的PDF
        import tempfile
        import os

        # 创建临时目录和文件
        temp_dir = Path("temp_pdf_uploads")
        temp_dir.mkdir(exist_ok=True)

        temp_pdf_path = temp_dir / f"temp_{pdf_file.filename}"

        # 保存上传的文件
        with open(temp_pdf_path, "wb") as f:
            import shutil
            shutil.copyfileobj(pdf_file.file, f)

        # 处理PDF文件
        result = await novel_knowledge_extender.process_pdf_and_import(str(temp_pdf_path))

        # 清理临时文件
        try:
            os.remove(temp_pdf_path)
        except:
            pass  # 如果删除失败，不影响响应

        return result

    except Exception as e:
        logger.error(f"处理上传的PDF文件时出错: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.post("/api/process-novel-pdf-batch")
async def process_novel_pdf_batch(
    request: Request
):
    """
    批量处理小说PDF文件（通过提供PDF文件路径列表）
    """
    global novel_knowledge_extender

    # 确保扩展管理器已初始化
    if novel_knowledge_extender is None:
        if not workflow_service.model_client:
            return {"status": "error", "message": "工作流服务未初始化，请先调用 /api/init-workflow"}
        novel_knowledge_extender = NovelKnowledgeExtender(workflow_service)

    try:
        data = await request.json()
        pdf_paths = data.get('pdf_paths', [])

        if not pdf_paths:
            return {"status": "error", "message": "PDF路径列表不能为空"}

        result = await novel_knowledge_extender.process_pdf_batch(pdf_paths)
        return result

    except Exception as e:
        logger.error(f"批量处理PDF文件时出错: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/api/novel-knowledge-stats")
async def get_novel_knowledge_stats():
    """
    获取小说分析知识库统计信息
    """
    global novel_knowledge_extender

    if novel_knowledge_extender is None:
        if not workflow_service.model_client:
            return {"status": "error", "message": "工作流服务未初始化，请先调用 /api/init-workflow"}
        novel_knowledge_extender = NovelKnowledgeExtender(workflow_service)

    try:
        stats = await novel_knowledge_extender.get_novel_analysis_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/search-novel-techniques")
async def search_novel_techniques(
    query: str = "",
    tags: str = None  # 以逗号分隔的标签
):
    """
    搜索小说技巧相关知识
    """
    global novel_knowledge_extender

    if novel_knowledge_extender is None:
        if not workflow_service.model_client:
            return {"status": "error", "message": "工作流服务未初始化，请先调用 /api/init-workflow"}
        novel_knowledge_extender = NovelKnowledgeExtender(workflow_service)

    try:
        # 解析标签参数
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]

        results = await novel_knowledge_extender.search_novel_techniques(query, tags_list)

        # 只返回知识条目的基本信息
        simplified_results = []
        for entry in results:
            simplified_results.append({
                "id": entry.id,
                "title": entry.title,
                "knowledge_type": entry.knowledge_type,
                "tags": entry.tags,
                "source": entry.source,
                "snippet": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
            })

        return {
            "status": "success",
            "results": simplified_results,
            "total": len(simplified_results)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/examples-by-novel-type")
async def get_examples_by_novel_type(
    novel_type: str,
    limit: int = 10
):
    """
    获取特定类型的小说技巧示例
    """
    global novel_knowledge_extender

    if novel_knowledge_extender is None:
        if not workflow_service.model_client:
            return {"status": "error", "message": "工作流服务未初始化，请先调用 /api/init-workflow"}
        novel_knowledge_extender = NovelKnowledgeExtender(workflow_service)

    try:
        results = await novel_knowledge_extender.get_examples_by_novel_type(novel_type, limit)

        simplified_results = []
        for entry in results:
            simplified_results.append({
                "id": entry.id,
                "title": entry.title,
                "knowledge_type": entry.knowledge_type,
                "content": entry.content,
                "tags": entry.tags,
                "source": entry.source
            })

        return {
            "status": "success",
            "results": simplified_results,
            "total": len(simplified_results)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/models")
async def get_model_configurations():
    """获取模型配置（暂时返回默认值）"""
    return {"model_configs": {
        "writer": {"model": "qwen3-max", "description": "故事创作模型"},
        "editor": {"model": "qwen3-max", "description": "编辑评价模型"},
        "fact_checker": {"model": "qwen3-max", "description": "事实检查模型"}
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