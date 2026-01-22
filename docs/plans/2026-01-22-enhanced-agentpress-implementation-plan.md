# Enhanced AgentPress Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor AgentPress into a modern, modular architecture with web UI, knowledge base, and dynamic AI model selection supporting 1-2万字小说生成 across multiple themes.

**Architecture:** Multi-module system with clean separation of concerns, knowledge-enhanced AI agents, and a comprehensive web-based management platform. The system will include dynamic model allocation per agent role and a knowledge management system.

**Tech Stack:** Python 3.11+, FastAPI, Web UI framework, OpenAI-compatible models, vector stores, async/await

---

### Task 1: Create new directory structure according to design

**Files:**
- Create: `apps/web_ui.py`
- Create: `apps/cli.py`
- Create: `core/workflow.py`
- Create: `core/agent_manager.py`
- Create: `ai_agents/base.py`
- Create: `knowledge/base.py`
- Create: `ui/templates/index.html`

**Step 1: Create directory structure**

```bash
mkdir -p apps
mkdir -p core
mkdir -p ai_agents
mkdir -p knowledge
mkdir -p prompts/templates
mkdir -p ui/templates
mkdir -p ui/static/css
mkdir -p ui/static/js
mkdir -p configs
mkdir -p data/knowledge_repo
mkdir -p tests/integration
mkdir -p scripts
```

**Step 2: Create base files with minimal content**

```python
# apps/web_ui.py
"""
Web UI for AgentPress Enhancement
"""
from fastapi import FastAPI

app = FastAPI(title="AgentPress Enhanced UI")

@app.get("/")
async def root():
    return {"message": "AgentPress Enhanced Web UI"}
```

**Step 3: Verify new files were created**

```bash
ls -la apps/
ls -la core/
ls -la ai_agents/
```

**Step 4: Commit the new directory structure**

```bash
git add apps/ core/ ai_agents/ knowledge/ prompts/ ui/ configs/ data/ tests/ scripts/
git commit -m "feat: create new modular directory structure for enhanced AgentPress"
```

### Task 2: Migrate existing logic to new architecture

**Files:**
- Create: `core/conversation_manager.py` (moved from top level)
- Create: `core/agent_manager.py` (updated)
- Modify: `src/novel_phases_manager.py` (move and rename to workflow.py)

**Step 1: Update import paths for existing classes**

```bash
# Move conversation manager to correct location
cp conversation_manager.py core/conversation_manager.py

# Update the import to reference new locations
# Modify all existing code to use: from core.conversation_manager import ConversationManager
```

**Step 2: Write updated agent manager for new architecture**

```python
# core/agent_manager.py
from typing import Dict, Any, Optional
from autogen import AssistantAgent
import json
import os
from pathlib import Path

class ModelConfig:
    """Configuration for different AI models per agent type"""

    def __init__(self):
        self.model_configs = {
            "writer": self._get_writer_config(),
            "editor": self._get_editor_config(),
            "fact_checker": self._get_fact_checker_config(),
            "dialogue_specialist": self._get_dialogue_specialist_config(),
            "mythologist": self._get_researcher_config(),
            "documentation_specialist": self._get_documentation_config()
        }

    def _get_writer_config(self):
        # Strong generative model
        return {
            "model": os.getenv("WRITER_MODEL", "gpt-4"),
            "description": "Primary story content creation",
            "capabilities": ["creative_generation", "narrative_control"]
        }

    def _get_editor_config(self):
        # Assessment model
        return {
            "model": os.getenv("EDITOR_MODEL", "gpt-4"),
            "description": "Overall story evaluation",
            "capabilities": ["quality_assessment", "holistic_review"]
        }

    def _get_fact_checker_config(self):
        # Logic reasoning model
        return {
            "model": os.getenv("FACT_CHECKER_MODEL", "gpt-4"),
            "description": "Logic and consistency verification",
            "capabilities": ["logical_inference", "consistency_check"]
        }

    def _get_dialogue_specialist_config(self):
        # Language understanding focused model
        return {
            "model": os.getenv("DIALOGUE_MODEL", "gpt-4"),
            "description": "Dialogue evaluation and optimization",
            "capabilities": ["dialogue_analysis", "character_voice"]
        }

    def _get_researcher_config(self):
        # Knowledge retrieval model (can be generic)
        return {
            "model": os.getenv("RESEARCHER_MODEL", "gpt-4"),
            "description": "Background research and setting development",
            "capabilities": ["research_synthesis", "background_development"]
        }

    def _get_documentation_config(self):
        # Memory tracking model (long context)
        return {
            "model": os.getenv("DOCUMENTATION_MODEL", "gpt-4"),
            "description": "Maintain consistency across long-form content",
            "capabilities": ["memory_retention", "consistency_tracking"]
        }

class AgentManager:
    """Updated Agent Manager with model-specific allocation"""

    def __init__(self, model_configs: Optional[ModelConfig] = None):
        self.model_configs = model_configs or ModelConfig()
        self.agents = {}

    def get_agent(self, agent_type: str) -> AssistantAgent:
        """Return specialized agent with appropriate configuration"""
        if agent_type not in self.model_configs.model_configs:
            raise ValueError(f"Unknown agent type: {agent_type}")

        config = self.model_configs.model_configs[agent_type]
        prompt_file_path = f"prompts/{agent_type}.md"

        if not os.path.exists(prompt_file_path):
            prompt_file_path = f"prompts/{self._agent_type_to_prompt(agent_type)}.md"

        with open(prompt_file_path, "r", encoding="utf-8") as f:
            system_message = f.read()

        # Create agent with configuration specific to this model type
        agent = AssistantAgent(
            name=self._get_agent_display_name(agent_type, config),
            system_message=system_message,
            model_config={
                "config_list": [{
                    "model": config["model"],
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }]
            }
        )
        return agent

    def _agent_type_to_prompt(self, agent_type: str) -> str:
        """Convert agent type to standard prompt naming"""
        mapping = {
            "mythologist": "mythologist",
            "writer": "writer",
            "fact_checker": "fact_checker",
            "dialogue_specialist": "dialogue_specialist",
            "editor": "editor",
            "documentation_specialist": "documentation_specialist"
        }
        return mapping.get(agent_type, agent_type)

    def _get_agent_display_name(self, agent_type: str, config: Dict[str, Any]) -> str:
        """Generate standard display names for agents"""
        names = {
            "mythologist": "Mythologist Agent",
            "writer": "Writer Agent",
            "fact_checker": "Fact Checker Agent",
            "dialogue_specialist": "Dialogue Specialist Agent",
            "editor": "Editor Agent",
            "documentation_specialist": "Documentation Specialist Agent"
        }
        return names.get(agent_type, f"{agent_type} Agent")

    def get_agents(self, agent_types: list) -> list:
        """Get multiple agents at once"""
        return [self.get_agent(agent_type) for agent_type in agent_types]
```

**Step 3: Commit the migrated core modules**

```bash
git add core/agent_manager.py core/conversation_manager.py
git commit -m "refactor: migrate agent manager to support dynamic model selection"
```

### Task 3: Create Knowledge Base System Architecture

**Files:**
- Create: `knowledge/base.py`
- Create: `knowledge/storage.py`
- Create: `knowledge/retriever.py`
- Create: `knowledge/manager.py`

**Step 1: Create the Knowledge Base base module**

```python
# knowledge/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class KnowledgeEntry:
    """Represents a single knowledge entry"""
    id: str
    title: str
    content: str
    tags: List[str]
    source: str
    creation_date: str
    last_modified: str
    knowledge_type: str  # "example", "technique", "background", "template"

class BaseKnowledgeStorage(ABC):
    """Abstract base class for knowledge storage implementations"""

    @abstractmethod
    async def save_entry(self, entry: KnowledgeEntry) -> bool:
        pass

    @abstractmethod
    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        pass

    @abstractmethod
    async def search_entries(self, query: str, tags: Optional[List[str]] = None) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def get_all_entries(self) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        pass

    @abstractmethod
    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        pass

class BaseKnowledgeRetriever(ABC):
    """Abstract base class for knowledge retrieval implementations"""

    @abstractmethod
    async def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        pass

    @abstractmethod
    async def semantic_search(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        pass
```

**Step 2: Create Knowledge Storage Implementation**

```python
# knowledge/storage.py
import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime
from .base import BaseKnowledgeStorage, KnowledgeEntry

class JsonFileKnowledgeStorage(BaseKnowledgeStorage):
    """Default file-based knowledge storage implementation"""

    def __init__(self, storage_path: str = "data/knowledge_repo/json_storage.json"):
        self.storage_path = Path(storage_path)
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._ensure_directory()
        self._load_existing_data()

    def _ensure_directory(self):
        """Ensure the storage directory exists"""
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True)

    def _load_existing_data(self):
        """Load existing knowledge entries from persistent storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for entry_data in data.get("entries", []):
                    entry = KnowledgeEntry(**entry_data)
                    self.entries[entry.id] = entry
            except Exception as e:
                print(f"Error loading knowledge storage: {e}")
                # Initialize with empty structure
                self.entries = {}
        else:
            # Create new file with empty structure
            self._save_to_file()

    def _save_to_file(self):
        """Save all entries to persistent storage"""
        entries_data = []
        for entry in self.entries.values():
            entries_data.append({
                "id": entry.id,
                "title": entry.title,
                "content": entry.content,
                "tags": entry.tags,
                "source": entry.source,
                "creation_date": entry.creation_date,
                "last_modified": entry.last_modified,
                "knowledge_type": entry.knowledge_type
            })

        data_to_save = {
            "entries": entries_data,
            "metadata": {
                "last_updated": datetime.now().isoformat()
            }
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    async def save_entry(self, entry: KnowledgeEntry) -> bool:
        """Save a knowledge entry"""
        entry.last_modified = datetime.now().isoformat()
        self.entries[entry.id] = entry
        self._save_to_file()
        return True

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific knowledge entry"""
        return self.entries.get(entry_id)

    async def search_entries(self, query: str, tags: Optional[List[str]] = None) -> List[KnowledgeEntry]:
        """Search for entries matching query and tags"""
        results = []
        lower_query = query.lower()

        for entry in self.entries.values():
            # Check if query matches in title or content
            if lower_query in entry.title.lower() or lower_query in entry.content.lower():
                # If tags specified, check if entry has all required tags
                if tags is not None:
                    if all(tag in entry.tags for tag in tags):
                        results.append(entry)
                else:
                    results.append(entry)
            # Otherwise check if tags match (if provided)
            elif tags is not None:
                if all(tag in entry.tags for tag in tags):
                    results.append(entry)

        return results

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        """Get all knowledge entries"""
        return list(self.entries.values())

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_to_file()
            return True
        return False

    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        """Update a knowledge entry"""
        if entry.id in self.entries:
            entry.last_modified = datetime.now().isoformat()
            self.entries[entry.id] = entry
            self._save_to_file()
            return True
        return False

    async def get_entries_by_type(self, knowledge_type: str) -> List[KnowledgeEntry]:
        """Get entries of a specific knowledge type"""
        return [entry for entry in self.entries.values() if entry.knowledge_type == knowledge_type]
```

**Step 3: Create Knowledge Retrieval Implementation**

```python
# knowledge/retriever.py
import asyncio
from typing import Any, Dict, List, Optional
from .base import BaseKnowledgeRetriever, BaseKnowledgeStorage, KnowledgeEntry
from .storage import JsonFileKnowledgeStorage

class SimpleKnowledgeRetriever(BaseKnowledgeRetriever):
    """Simple knowledge retrieval based on keyword matching"""

    def __init__(self, storage: BaseKnowledgeStorage):
        self.storage = storage

    async def retrieve_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """Retrieve knowledge based on query and optional category"""
        tags = [category] if category else None
        results = await self.storage.search_entries(query, tags)

        # Sort by "relevance" (simple word count match for now)
        query_lower = query.lower()
        def relevance_score(entry: KnowledgeEntry):
            content_lower = entry.content.lower()
            title_lower = entry.title.lower()
            # Score based on keyword matches
            score = content_lower.count(query_lower) + title_lower.count(query_lower)
            # Prefer exact matches in title
            if query.lower() in title_lower.lower():
                score += 10
            return score

        # Sort by relevance score descending
        results.sort(key=relevance_score, reverse=True)
        return results[:limit]

    async def semantic_search(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Simple fallback if semantic search is not available"""
        # For now, just return keyword search
        # This would be replaced with real embedding/semantic search later
        return await self.retrieve_knowledge(query, limit=limit)
```

**Step 4: Create Knowledge Manager**

```python
# knowledge/manager.py
import asyncio
from typing import Any, Dict, List, Optional
from .base import KnowledgeEntry
from .storage import JsonFileKnowledgeStorage
from .retriever import SimpleKnowledgeRetriever

class KnowledgeManager:
    """Main manager for knowledge base functionality"""

    def __init__(self, storage_path: str = "data/knowledge_repo/json_storage.json"):
        self.storage = JsonFileKnowledgeStorage(storage_path)
        self.retriever = SimpleKnowledgeRetriever(self.storage)

    async def add_entry(
        self,
        title: str,
        content: str,
        tags: List[str],
        knowledge_type: str,
        source: str = "manual"
    ) -> bool:
        """Add a new knowledge entry"""
        # Generate ID from hash of content
        import hashlib
        content_hash = hashlib.md5((title + content).encode()).hexdigest()

        entry = KnowledgeEntry(
            id=content_hash,
            title=title,
            content=content,
            tags=tags,
            source=source,
            creation_date=str(__import__('datetime').datetime.now().isoformat()),
            last_modified=str(__import__('datetime').datetime.now().isoformat()),
            knowledge_type=knowledge_type
        )

        return await self.storage.save_entry(entry)

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific knowledge entry"""
        return await self.storage.get_entry(entry_id)

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """Search knowledge based on query and category"""
        return await self.retriever.retrieve_knowledge(query, category, limit)

    async def get_all_entries(self) -> List[KnowledgeEntry]:
        """Get all knowledge entries"""
        return await self.storage.get_all_entries()

    async def update_entry(self, entry: KnowledgeEntry) -> bool:
        """Update an existing knowledge entry"""
        return await self.storage.update_entry(entry)

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        return await self.storage.delete_entry(entry_id)

    async def get_examples_by_type(self, example_type: str) -> List[KnowledgeEntry]:
        """Get examples of a specific type from knowledge base"""
        all_entries = await self.get_all_entries()
        return [
            entry for entry in all_entries
            if entry.knowledge_type == "example" and example_type.lower() in entry.tags
        ]

    async def get_techniques_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Get writing techniques in a specific category"""
        all_entries = await self.get_all_entries()
        return [
            entry for entry in all_entries
            if entry.knowledge_type == "technique" and category.lower() in entry.tags
        ]
```

**Step 5: Commit the knowledge base modules**

```bash
git add knowledge/
git commit -m "feat: implement knowledge base system with storage and retrieval"
```

### Task 4: Create Web UI Structure with Model Selection and Prompt Management

**Files:**
- Create: `apps/web_ui.py` (completed)
- Create: `apps/routes/model_routes.py`
- Create: `apps/routes/prompt_routes.py`
- Create: `apps/routes/agent_routes.py`
- Create: `ui/templates/index.html`

**Step 1: Complete Web UI implementation**

```python
# apps/web_ui.py
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
```

**Step 2: Create model configuration routes**

```python
# apps/routes/model_routes.py
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

    # Update the configuration
    model_config.model_configs[agent_type].update(config)
    return {"agent_type": agent_type, "updated_config": config}
```

**Step 3: Create prompt management routes**

```python
# apps/routes/prompt_routes.py
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
```

**Step 4: Create agent management routes**

```python
# apps/routes/agent_routes.py
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
```

**Step 5: Create the main HTML template**

```html
<!-- ui/templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentPress Enhanced - AI Story Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">AgentPress Enhanced</a>
            <div class="navbar-nav">
                <a class="nav-link" href="#workflow">Workflow</a>
                <a class="nav-link" href="#agents">Agents</a>
                <a class="nav-link" href="#knowledge">Knowledge</a>
                <a class="nav-link" href="#settings">Settings</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1>AgentPress Enhanced</h1>
                <p class="lead">AI-Powered Story Generation Platform with Knowledge Base and Model Flexibility</p>
            </div>
        </div>

        <div class="row mt-4" id="workflow">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Story Creation Workflow</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="storyIdea" class="form-label">Enter your story idea (1-2萬字):</label>
                            <textarea class="form-control" id="storyIdea" rows="3" placeholder="Describe your story idea..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="storyTheme" class="form-label">Story Theme:</label>
                            <select class="form-select" id="storyTheme">
                                <option value="mythological">Mythological (not just Shanhai Jing)</option>
                                <option value="fantasy">Fantasy</option>
                                <option value="science_fiction">Science Fiction</option>
                                <option value="realistic_fiction">Realistic Fiction</option>
                                <option value="historical">Historical</option>
                                <option value="contemporary">Contemporary</option>
                                <option value="custom">Custom</option>
                            </select>
                        </div>
                        <button id="startCreation" class="btn btn-primary">Start Story Creation</button>
                        <div id="creationProgress" class="mt-3" style="display: none;">
                            <div class="progress">
                                <div class="progress-bar" role="progressbar" style="width: 25%" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">25%</div>
                            </div>
                            <p>Processing...</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Quick Info</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Target Length:</strong> 1-2萬字</p>
                        <p><strong>Supported Genres:</strong> All genres supported</p>
                        <p><strong>AI Agents:</strong> Multi-role collaboration</p>
                        <p><strong>Knowledge Base:</strong> Dynamic content enhancement</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4" id="agents">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>AI Agent Management</h5>
                    </div>
                    <div class="card-body">
                        <h6>Select Models for Each Agent:</h6>
                        <div class="table-responsive">
                            <table class="table" id="agentModelTable">
                                <thead>
                                    <tr>
                                        <th>Agent Role</th>
                                        <th>Current Model</th>
                                        <th>Capabilities</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Writer</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="writerModel"></td>
                                        <td>Creative generation, narrative structure</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                    <tr>
                                        <td>Mythologist/Researcher</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="researcherModel"></td>
                                        <td>Background research, setting development</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                    <tr>
                                        <td>Fact Checker</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="factCheckerModel"></td>
                                        <td>Logic verification, consistency check</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                    <tr>
                                        <td>Dialogue Specialist</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="dialogueModel"></td>
                                        <td>Dialogue quality, character voice</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                    <tr>
                                        <td>Editor</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="editorModel"></td>
                                        <td>Quality assessment, final refinement</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                    <tr>
                                        <td>Documentation Specialist</td>
                                        <td><input type="text" class="form-control" value="gpt-4" id="documentationModel"></td>
                                        <td>Consistency tracking, character management</td>
                                        <td><button class="btn btn-sm btn-outline-primary">Change</button></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4" id="knowledge">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Knowledge Base</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Add Knowledge Entry:</h6>
                                <div class="mb-3">
                                    <input type="text" class="form-control" placeholder="Entry Title" id="knowledgeTitle">
                                </div>
                                <div class="mb-3">
                                    <select class="form-select mb-2" id="knowledgeType">
                                        <option value="example">Example Story</option>
                                        <option value="technique">Writing Technique</option>
                                        <option value="background">Background Info</option>
                                        <option value="template">Template/Structure</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <textarea class="form-control" placeholder="Knowledge Content" id="knowledgeContent" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <input type="text" class="form-control" placeholder="Tags (comma-separated)" id="knowledgeTags">
                                </div>
                                <button class="btn btn-primary" id="addKnowledge">Add to Knowledge Base</button>
                            </div>
                            <div class="col-md-6">
                                <h6>Search Knowledge:</h6>
                                <div class="input-group mb-3">
                                    <input type="text" class="form-control" placeholder="Search knowledge base" id="knowledgeSearch">
                                    <button class="btn btn-outline-secondary" type="button" id="searchBtn">Search</button>
                                </div>
                                <div class="list-group" id="searchResults">
                                    <!-- Search results will appear here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

**Step 6: Commit the Web UI modules**

```bash
git add apps/ ui/
git commit -m "feat: implement web UI with model selection and knowledge management"
```