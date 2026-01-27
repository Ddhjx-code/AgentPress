# AgentPress - 精简版小说生成系统

## 项目结构说明

经过清理后，项目专注于核心小说生成功能，移除了知识库、测试代码等无关功能。

### 目录结构
```
├── config.py                 # 项目配置文件
├── generate_long_story.py    # 长篇小说生成主入口
├── phases.py                # 小说生成工作流编排器
├── utils.py                 # 公用工具函数
├── core/                    # 核心功能模块
│   ├── agent_manager.py     # AI代理管理器
│   ├── chapter_decision_engine.py # 章节决策引擎
│   ├── config_manager.py    # 配置管理器
│   ├── continuity_manager.py # 连续性管理器
│   ├── conversation_manager.py # 会话管理器
│   ├── story_state_manager.py # 故事状态管理器
│   └── workflow_service.py  # 工作流服务
├── src/                     # 核心生成组件
│   ├── documentation_manager.py # 文档管理器
│   └── novel_phases_manager.py # 小说阶段管理器
├── prompts/                 # AI代理提示词（核心功能必需）
├── apps/web_ui.py          # 简化的API接口服务
├── test_concept.txt        # 测试用创作概念
└── real_outputs/           # 小说生成输出目录
```

### 核心功能
- **多AI代理协作**：多个专业AI代理协同创作小说
- **4阶段工作流**：研究规划→创作→评审→最终检查
- **自适应生成**：根据内容复杂度动态调整生成策略
- **质量保证**：多重质量检查确保内容连贯性

### 运行方式
1. 设置环境变量 `QWEN_API_KEY`
2. 直接运行: `python generate_long_story.py`
3. 或通过API: `python apps/web_ui.py`

### 核心模块功能
- **WorkflowService**: 统一工作流服务入口
- **NovelWritingPhases**: 小说创作的各阶段管理
- **AgentManager**: 多AI代理管理
- **各种Manager**: 专项管理器(连续性、状态、会话等)

### API接口
- `/api/init-workflow` : 初始化工作流
- `/api/generate-novel` : 生成小说
- `/api/conversation-history` : 获取对话历史
- `/health` : 健康检查

此版本仅保留小说生成的核心功能，移除了所有扩展和测试相关代码。