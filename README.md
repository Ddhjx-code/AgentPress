# AgentPress - Multi-Agent AI Publishing House

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AutoGen](https://img.sh.io/badge/AutoGen-AgentChat-orange)](https://microsoft.github.io/autogen/)

**AgentPress** is a streamlined multi-agent AI publishing framework for creating high-quality stories. It leverages specialized AI agents that collaborate through detailed prompts to research, write, edit, and fact-check content. The system is specifically tailored for "Shan Hai Jing" stories but can be adapted to any narrative genre.

## 🌟 Key Features

- **Modular Agent Architecture**: Specialized AI agents in distinct roles:
  - 📚 **Mythologist**: Handles background research and mythological research
  - ✍️ **Writer**: Creates story content
  - 🔍 **Fact Checker**: Ensures narrative consistency and logic accuracy
  - 💬 **Dialogue Specialist**: Optimizes dialogue quality and character voices
  - 📝 **Editor**: Reviews overall story quality
  - 📋 **Documentation Specialist**: Maintains story consistency across chapters
- **Multi-Chapter Support**: Complete workflow supporting both single and multi-chapter stories with consistency tracking
- **Iterative Review**: Multi-round review and refinement until stories meet quality standards
- **Prompt-Driven**: All agent behaviors defined by detailed prompts for easy customization
- **Chinese LLM Friendly**: Compatible with Qwen and other OpenAI-compatible models
- **Consistency Checking**: Automatic consistency validation and updates across chapters

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Ddhjx-code/AgentPress.git
cd AgentPress
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
# Or manually:
pip install "autogen-agentchat>=0.7.5" "autogen-ext[openai]>=0.7.5" python-dotenv
```

### 3. Configure API key
Create `.env` file with:
```
QWEN_API_KEY=your_api_key_here
```

### 4. Run the example
```bash
python main.py
```

### 5. Check outputs in output/ directory
- `output/novel_story_*.txt` - Final story content
- `output/novel_data_*.json` - Complete structured data
- `output/conversation_history_*.json` - Full conversation records

## 📁 Project Structure

AgentPress/
├── main.py                          # Entry point with async support
├── phases.py                        # Workflow orchestrator
├── src/                             # Core modules directory
│   ├── novel_phases_manager.py      # Complete multi-phase writing implementation
│   └── documentation_manager.py     # Story consistency management
├── agents_manager.py                # AI agent manager
├── conversation_manager.py          # Communication and history manager
├── config.py                        # Configuration and settings
├── utils.py                         # Utility functions
├── prompts/                         # Detailed agent prompts
│   ├── mythologist.md              # Background researcher system prompt
│   ├── writer.md                   # Story writer system prompt
│   ├── fact_checker.md             # Fact checker system prompt
│   ├── dialogue_specialist.md      # Dialogue reviewer system prompt
│   └── editor.md                   # Final editor system prompt
├── output/                         # Generated content directory
│   ├── novel_story_*.txt           # Story text files
│   ├── novel_data_*.json           # Complete structured output
│   └── conversation_history_*.json # Communication logs
└── .env                            # API configuration

## 🎯 Use Cases

- **Mythological Fiction**: "Shan Hai Jing"-style stories
- **Novel Writing**: Multi-chapter story creation with consistency
- **Content Creation**: AI-assisted fiction writing
- **Multi-Agent Collaboration**: AI agent coordination research
- **Prompt Engineering**: High-quality prompt experimentation

## 🔄 Customizing Prompts

To adapt to different genres, modify prompt files in `prompts/` directory:

- **Change Setting**: Modify mythology and background in mythologist.md
- **Adjust Style**: Update narrative requirements in writer.md
- **Modify Genres**: Change story types and tones across all prompts

## 📚 Architecture

This system uses a clean, modular architecture with clear separation of concerns:
- **Orchestration layer**: `main.py` and `phases.py`
- **Business logic**: `src/novel_phases_manager.py`
- **Data management**: `src/documentation_manager.py` and `conversation_manager.py`
- **AI agents**: `agents_manager.py` and `prompts/`

This structure allows for independent development and testing of components.

## 🤝 Contributing

Contributions are welcome! We especially welcome:
- New agent prompt designs
- Genre-specific configurations
- Multi-chapter consistency improvements
- Performance and reliability enhancements

## 📜 License

MIT License - see [LICENSE](LICENSE) for details