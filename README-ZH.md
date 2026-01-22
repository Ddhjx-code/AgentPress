# AgentPress - 多智能体 AI 编辑社

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AutoGen](https://img.sh.io/badge/AutoGen-AgentChat-orange)](https://microsoft.github.io/autogen/)

**AgentPress** 是一个精简的多智能体AI发布框架，专为创作高质量故事而设计。它利用专门的AI代理通过详细提示协作来研究、写作、编辑和事实核查内容。该系统专门针对《山海经》故事进行优化，但可以适配至任何叙事体裁。

## 🌟 核心特性

- **模块化代理架构**：在不同角色中分配专门AI代理：
  - 📚 **神话学家**：负责背景研究和神话研究
  - ✍️ **作家**：创作故事内容
  - 🔍 **事实检查员**：确保故事情节一致性和逻辑准确性
  - 💬 **对话专家**：优化对话质量和角色声音
  - 📝 **编辑**：审查整体故事质量
  - 📋 **档案员**：维护章节间的故事情节一致性
- **多章节支持**：完整的单章和多章节故事创作流程，包含一致性跟踪
- **迭代审查**：多轮审查和修订直至故事达到质量标准
- **提示词驱动**：所有代理行为由详细提示词定义，便于定制
- **国产量LLM友好**：兼容通义千问和其他OpenAI兼容模型
- **一致性核查**：自动章节间一致性验证和更新

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/Ddhjx-code/AgentPress.git
cd AgentPress
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
# 或手动安装：
pip install "autogen-agentchat>=0.7.5" "autogen-ext[openai]>=0.7.5" python-dotenv
```

### 3. 配置 API 密钥
创建 `.env` 文件：
```
QWEN_API_KEY=你的API密钥
```

### 4. 运行示例
```bash
python main.py
```

### 5. 在 output/ 目录中查看输出
- `output/novel_story_*.txt` - 最终故事内容
- `output/novel_data_*.json` - 完整结构化数据
- `output/conversation_history_*.json` - 完整对话记录

## 📁 项目结构

AgentPress/
├── main.py                          # 入口点，支持异步处理
├── phases.py                        # 工作流程协调器
├── src/                             # 核心模块目录
│   ├── novel_phases_manager.py      # 完整多阶段写作实现
│   └── documentation_manager.py     # 故事一致性管理
├── agents_manager.py                # AI代理管理器
├── conversation_manager.py          # 通信和历史管理器
├── config.py                        # 配置和设置
├── utils.py                         # 工具函数
├── prompts/                         # 详细代理提示词
│   ├── mythologist.md              # 背景研究员系统提示词
│   ├── writer.md                   # 故事作家系统提示词
│   ├── fact_checker.md             # 事实检查员系统提示词
│   ├── dialogue_specialist.md      # 对话审查员系统提示词
│   └── editor.md                   # 最终编辑系统提示词
├── output/                         # 生成内容目录
│   ├── novel_story_*.txt           # 故事文本文件
│   ├── novel_data_*.json           # 完整结构化输出
│   └── conversation_history_*.json # 通信日志
└── .env                            # API配置

## 🎯 使用场景

- **神话类小说**：《山海经》式故事创作
- **小说写作**：保持情节一致性的多章节小说创作
- **内容创作**：AI辅助小说写作
- **多智能体协作**：AI代理协调研究
- **提示词工程**：高质量提示词实验

## 🔄 自定义提示词

为适配不同体裁，请修改 `prompts/` 目录中的提示词文件：

- **更改设定**：修改 mythologist.md 中的神话背景设定
- **调整风格**：更新 writer.md 中的叙事要求
- **变更体裁**：在所有提示词中更改故事类型和风格

## 📚 架构

该系统使用干净的模块化架构，清晰分离关注点：
- **协调层**：`main.py` 和 `phases.py`
- **业务逻辑**：`src/novel_phases_manager.py`
- **数据管理**：`src/documentation_manager.py` 和 `conversation_manager.py`
- **AI代理**：`agents_manager.py` 和 `prompts/`

这种结构允许对组件进行独立的开发和测试。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！特此欢迎：
- 新的代理提示词设计
- 体裁相关的配置
- 多章节一致性改进
- 性能和可靠性提高

## 📜 许可证

MIT License - 详情请见 [LICENSE](LICENSE)