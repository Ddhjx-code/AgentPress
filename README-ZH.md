# AgentPress - 多智能体 AI 编辑社

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AutoGen](https://img.shields.io/badge/AutoGen-AgentChat-orange)](https://microsoft.github.io/autogen/)

**AgentPress** 是一个通用的多智能体 AI 编辑社框架。通过多个专业 AI 角色的协作，系统能够进行高质量的内容创作、校验和优化。虽然示例使用《山海经》作为背景，但通过修改提示词，可以轻松适配任何创作场景。

## 🌟 核心特性

- **模块化多智能体架构**：4 个专业角色分工协作
  - 📚 **研究员**：提供准确的背景研究和考据
  - ✍️ **作家**：创作高质量内容
  - 🔍 **事实校验员**：确保内容准确性
  - 📝 **编辑**：提升文学和表达质量
- **结构化通信**：Agent 间通过 JSON 格式进行精准交流
- **多轮迭代优化**：自动进行多轮修订直至达到质量标准
- **提示词驱动**：所有角色行为通过提示词定义，易于定制
- **国产模型友好**：完美兼容通义千问等 OpenAI 兼容模型

## 🚀 快速开始

### 1. 克隆项目
git clone https://github.com/your-username/AgentPress.git
cd AgentPress

### 2. 安装依赖
pip install "autogen-agentchat>=0.7.5" "autogen-ext[openai]>=0.7.5" python-dotenv

### 3. 配置 API 密钥
创建 `.env` 文件：
QWEN_API_KEY=你的API密钥

### 4. 运行示例
python main.py

### 5. 查看输出
- `final_output.json` - 完整的结构化输出
- `final_story.md` - 格式化的 Markdown 内容

## 📁 项目结构

AgentPress/
├── main.py                  # 主程序入口
├── prompts/                 # 角色提示词目录
│   ├── researcher.md        # 研究员提示词
│   ├── writer.md           # 作家提示词
│   ├── fact_checker.md     # 事实校验员提示词
│   └── editor.md           # 编辑提示词
├── final_output.json        # 最终 JSON 输出
├── final_story.md          # 最终 Markdown 输出
└── .env                    # API 密钥配置

## 🎯 使用场景

- **内容创作**：AI 辅助写作、博客、故事创作
- **学术写作**：论文草稿、研究报告
- **教育应用**：教学材料生成、学习辅助
- **多智能体研究**：AI Agent 协作模式探索
- **提示词工程**：高质量提示词设计和测试

## 🔄 自定义提示词

要适配不同场景，只需修改 `prompts/` 目录下的提示词文件：

- **更换主题**：修改 researcher.md 中的研究领域
- **调整风格**：修改 writer.md 中的写作风格要求  
- **改变标准**：修改 fact_checker.md 和 editor.md 中的校验标准

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！特别欢迎：
- 新的提示词模板
- 更多使用场景示例
- 新的 Agent 角色设计
- 性能和稳定性改进

## 📜 许可证

MIT License - 详情请见 [LICENSE](LICENSE)
