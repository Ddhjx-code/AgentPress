# AgentPress - Multi-Agent AI Publishing House

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AutoGen](https://img.shields.io/badge/AutoGen-AgentChat-orange)](https://microsoft.github.io/autogen/)

**AgentPress** is a general-purpose multi-agent AI publishing house framework. Through the collaboration of multiple specialized AI agents, the system can create, verify, and optimize high-quality content. While the example uses "Shan Hai Jing" as background, it can be easily adapted to any creative scenario by modifying prompts.

## 🌟 Key Features

- **Modular Multi-Agent Architecture**: 4 specialized roles working together
  - 📚 **Researcher**: Provides accurate background research and analysis
  - ✍️ **Writer**: Creates high-quality content
  - 🔍 **Fact Checker**: Ensures content accuracy
  - 📝 **Editor**: Enhances literary and expressive quality
- **Structured Communication**: Agents communicate through precise JSON format
- **Iterative Optimization**: Automatic multi-round revision until quality standards are met
- **Prompt-Driven**: All agent behaviors are defined by prompts, easy to customize
- **Chinese LLM Friendly**: Fully compatible with Qwen and other OpenAI-compatible models

## 🚀 Quick Start

### 1. Clone the repository
git clone https://github.com/your-username/AgentPress.git
cd AgentPress

### 2. Install dependencies
pip install "autogen-agentchat>=0.7.5" "autogen-ext[openai]>=0.7.5" python-dotenv

### 3. Configure API key
Create `.env` file:
QWEN_API_KEY=your_api_key_here

### 4. Run the example
python main.py

### 5. Check outputs
- `final_output.json` - Complete structured output
- `final_story.md` - Formatted Markdown content

## 📁 Project Structure

AgentPress/
├── main.py                  # Main entry point
├── prompts/                 # Agent prompt directory
│   ├── researcher.md        # Researcher prompts
│   ├── writer.md           # Writer prompts
│   ├── fact_checker.md     # Fact checker prompts
│   └── editor.md           # Editor prompts
├── final_output.json        # Final JSON output
├── final_story.md          # Final Markdown output
└── .env                    # API key configuration

## 🎯 Use Cases

- **Content Creation**: AI-assisted writing, blogs, storytelling
- **Academic Writing**: Paper drafts, research reports
- **Educational Applications**: Teaching materials, learning aids
- **Multi-Agent Research**: AI agent collaboration patterns
- **Prompt Engineering**: High-quality prompt design and testing

## 🔄 Customizing Prompts

To adapt to different scenarios, simply modify the prompt files in `prompts/` directory:

- **Change Topic**: Modify the research domain in researcher.md
- **Adjust Style**: Modify writing style requirements in writer.md
- **Change Standards**: Modify verification criteria in fact_checker.md and editor.md

## 🤝 Contributing

Contributions are welcome! We especially welcome:
- New prompt templates
- More use case examples
- New agent role designs
- Performance and stability improvements

## 📜 License

MIT License - see [LICENSE](LICENSE) for details
