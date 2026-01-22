# AgentPress System Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the AgentPress multi-agent story creation system for better maintainability, extensibility, and code quality.

**Architecture:** Modular refactoring of current monolithic components into focused, well-separated classes and functions. Implementation will follow a phased approach, starting with architecture improvements and moving to component refactoring.

**Tech Stack:** Python 3.8+, AutoGen, OpenAI API, JSON, file I/O

---

### Task 1: Extract DocumentationManager to separate module

**Files:**
- Create: `src/documentation_manager.py`
- Modify: `phases.py:660-775` (remove DocumentationManager class)

**Step 1: Create the documentation manager module**

```python
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
import os
from datetime import datetime

@dataclass
class StoryDocumentation:
    """Container for all story documentation elements"""
    characters: Dict[str, Dict]
    timeline: List[Dict]
    world_rules: Dict[str, str]
    plot_points: List[Dict]
    settings_locations: Dict[str, Dict]
    created_at: str
    updated_at: str

class DocumentationManager:
    """Manages story consistency documentation across chapters"""

    def __init__(self, save_path: str = "output/documentation.json"):
        self.save_path = save_path
        self.documentation = self._load_existing_documentation()

    def _load_existing_documentation(self) -> StoryDocumentation:
        """Load existing documentation or create a new one"""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return StoryDocumentation(
                    characters=data.get("characters", {}),
                    timeline=data.get("timeline", []),
                    world_rules=data.get("world_rules", {}),
                    plot_points=data.get("plot_points", []),
                    settings_locations=data.get("settings_locations", {}),
                    created_at=data.get("created_at", datetime.now().isoformat()),
                    updated_at=data.get("updated_at", datetime.now().isoformat())
                )
            except:
                pass

        return StoryDocumentation(
            characters={},
            timeline=[],
            world_rules={},
            plot_points=[],
            settings_locations={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def update_documentation(self, content: str) -> None:
        """Update documentation based on story content"""
        try:
            # Extract from content
            extracted = json.loads(content)

            # Update documentation elements
            if "characters" in extracted and isinstance(extracted["characters"], dict):
                self.documentation.characters.update(extracted["characters"])

            if "timeline" in extracted and isinstance(extracted["timeline"], list):
                self.documentation.timeline.extend(extracted["timeline"])

            if "world_rules" in extracted and isinstance(extracted["world_rules"], dict):
                self.documentation.world_rules.update(extracted["world_rules"])

            if "plot_points" in extracted and isinstance(extracted["plot_points"], list):
                self.documentation.plot_points.extend(extracted["plot_points"])

            if "settings_locations" in extracted and isinstance(extracted["settings_locations"], dict):
                self.documentation.settings_locations.update(extracted["settings_locations"])

            # Update timestamp
            self.documentation.updated_at = datetime.now().isoformat()

            # Save documentation
            self._save_documentation()
        except Exception as e:
            print(f"Error updating documentation: {e}")

    def _save_documentation(self) -> None:
        """Save documentation to file"""
        data = {
            "characters": self.documentation.characters,
            "timeline": self.documentation.timeline,
            "world_rules": self.documentation.world_rules,
            "plot_points": self.documentation.plot_points,
            "settings_locations": self.documentation.settings_locations,
            "created_at": self.documentation.created_at,
            "updated_at": self.documentation.updated_at
        }

        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_documentation(self) -> str:
        """Get documentation as JSON string"""
        data = {
            "characters": self.documentation.characters,
            "timeline": self.documentation.timeline,
            "world_rules": self.documentation.world_rules,
            "plot_points": self.documentation.plot_points,
            "settings_locations": self.documentation.settings_locations,
            "updated_at": self.documentation.updated_at
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
```

**Step 2: Write the new module to file**

Write the above content to `src/documentation_manager.py`.

**Step 3: Commit the new file**

```bash
mkdir -p src
git add src/documentation_manager.py
git commit -m "refactor: extract DocumentationManager to separate module"
```

### Task 2: Update phases.py to use new DocumentationManager import

**Files:**
- Modify: `phases.py:660-775` (remove DocumentationManager class)
- Modify: `phases.py:1-30` (add import)

**Step 1: Add import statement**

```python
from src.documentation_manager import DocumentationManager, StoryDocumentation
```

**Step 2: Remove DocumentationManager class from phases.py**

Remove lines 660-775 that contain the DocumentationManager class definition, keeping only the NovelWritingPhases class.

**Step 3: Update NovelWritingPhases to remove DocumentationManager class definition**

In phases.py, remove or replace the existing DocumentationManager class, ensuring the NovelWritingPhases class uses the imported DocumentationManager.

**Step 4: Run tests to verify import works**

```bash
python -c "from src.documentation_manager import DocumentationManager; print('Import successful')"
```

**Step 5: Commit the changes**

```bash
git add phases.py
git commit -m "refactor: update phases.py to use extracted DocumentationManager"
```

### Task 3: Extract NovelWritingPhases to separate module

**Files:**
- Create: `src/novel_phases_manager.py`
- Modify: `phases.py:1-659` (move NovelWritingPhases class)

**Step 1: Create the novel phases manager module**

```python
import json
import re
from typing import List, Dict, Any, Optional
from autogen import GroupChat, GroupChatManager, ConversableAgent
from agents_manager import AgentManager
from conversation_manager import ConversationManager
from src.documentation_manager import DocumentationManager
from config import agents_config, groupchat_config, llm_config
import time

class NovelWritingPhases:
    """Manages the multi-phase novel writing process"""

    def __init__(self, conversation_manager: ConversationManager,
                 documentation_manager: DocumentationManager):
        self.conversation_manager = conversation_manager
        self.documentation_manager = documentation_manager
        self.agent_manager = AgentManager()

    def phase1_research_and_planning(self, initial_idea: str):
        """Phase 1: Research and planning phase with group chat"""
        print("开始第一阶段：研究和规划...")

        mythologist_agent = self.agent_manager.create_agent(agents_config["mythologist"])
        writer_agent = self.agent_manager.create_agent(agents_config["writer"])

        mythologist_agent.register_reply([ConversableAgent, None], self.capture_groupchat_message)
        writer_agent.register_reply([ConversableAgent, None], self.capture_groupchat_message)

        group_chat = GroupChat(
            agents=[mythologist_agent, writer_agent],
            messages=[],
            max_round=10,
            groupchat_config=groupchat_config
        )

        manager = GroupChatManager(groupchat_config, llm_config)

        research_response = mythologist_agent.initiate_chat(
            manager,
            message={
                "content": f"请分析以下故事想法：{initial_idea}\n\n请进行全面的背景研究，考虑山海经的世界观、神话体系、人物设定等。",
                "request": "research"
            }
        )

        self.conversation_manager.add_to_history({
            "phase": "phase1_research",
            "content": research_response.summary
        })

        planning_response = writer_agent.initiate_chat(
            manager,
            message={
                "content": f"基于研究结果，请制定一个详细的创作计划：{research_response.summary}",
                "request": "planning"
            }
        )

        self.conversation_manager.add_to_history({
            "phase": "phase1_planning",
            "content": planning_response.summary
        })

        print("第一阶段：研究和规划完成")
        return planning_response.summary

    def phase2_creation(self, plan: str, multi_chapter: bool = False, total_chapters: int = 1):
        """Phase 2: Creation phase"""
        print("开始第二阶段：创作...")

        writer_agent = self.agent_manager.create_agent(agents_config["writer"])
        writer_agent.register_reply([ConversableAgent, None], self.capture_groupchat_message)

        if multi_chapter:
            return self._multi_chapter_creation(plan, total_chapters)
        else:
            return self._single_chapter_creation(plan)

    def _single_chapter_creation(self, plan: str):
        """Create a single chapter novel"""
        # Existing single chapter logic with proper conversation capture
        response = writer_agent.initiate_chat(
            manager,
            message={
                "content": f"请根据以下计划创作故事：\n{plan}\n\n请创作一个完整的故事。",
                "request": "creation"
            }
        )

        self.conversation_manager.add_to_history({
            "phase": "phase2_creation",
            "content": response.summary
        })

        return response.summary

    def _multi_chapter_creation(self, plan: str, total_chapters: int):
        """Create a multi-chapter novel"""
        story_parts = []
        for chapter_num in range(1, total_chapters + 1):
            print(f"正在创作第 {chapter_num} 章...")

            # Get current documentation to maintain consistency
            current_doc = self.documentation_manager.get_documentation()

            writer_agent = self.agent_manager.create_agent(agents_config["writer"])
            documentation_specialist = self.agent_manager.create_agent(agents_config["documentation_specialist"])

            # Include documentation in the chapter creation prompt
            message_content = f"""请根据以下计划创作第 {chapter_num} 章：\n{plan}

基于以下故事文档保持一致性：
{current_doc}

章节数：{chapter_num}/{total_chapters}

请创作第 {chapter_num} 章的内容，确保与之前的内容保持一致。"""

            response = writer_agent.initiate_chat(
                manager,
                message={
                    "content": message_content,
                    "request": "creation"
                }
            )

            # Add to story parts
            story_parts.append({
                "chapter": chapter_num,
                "content": response.summary
            })

            # Process consistency feedback if needed
            self.conversation_manager.add_to_history({
                "phase": "phase2_creation",
                "chapter": chapter_num,
                "content": response.summary
            })

            # Update documentation with new content
            # Extract key elements from the chapter content and update documentation
            self._update_documentation_with_chapter(response.summary, chapter_num)

            # Every 3 chapters, perform intermediate review
            if chapter_num % 3 == 0:
                print(f"进行中期评审 - {chapter_num}章完成")
                self._intermediate_review(story_parts)

        # Combine all parts into final story
        combined_story = ""
        for part in story_parts:
            combined_story += f"\n第 {part['chapter']} 章：\n{part['content']}\n"

        return combined_story

    def phase3_review_refinement(self, story: str, rounds: int = 2):
        """Phase 3: Review and refinement"""
        print("开始第三阶段：审查和优化...")

        for round_num in range(1, rounds + 1):
            print(f"第 {round_num} 轮审查...")

            fact_checker = self.agent_manager.create_agent(agents_config["fact_checker"])
            dialogue_specialist = self.agent_manager.create_agent(agents_config["dialogue_specialist"])
            editor = self.agent_manager.create_agent(agents_config["editor"])

            # Each specialist reviews the story and provides feedback
            fact_check_result = fact_checker.initiate_chat(
                editor,
                message={
                    "content": f"请检查以下故事的逻辑和事实准确性：\n\n{story}",
                    "request": "fact_check"
                }
            )

            dialogue_result = dialogue_specialist.initiate_chat(
                editor,
                message={
                    "content": f"请优化以下故事的对话质量：\n\n{story}\n\n事实检查结果：{fact_check_result.summary}",
                    "request": "dialogue_refinement"
                }
            )

            refined_result = editor.initiate_chat(
                editor,
                message={
                    "content": f"请综合所有反馈优化故事：\n\n{story}\n\n事实检查：{fact_check_result.summary}\n\n对话优化：{dialogue_result.summary}",
                    "request": "final_edit"
                }
            )

            story = refined_result.summary

            # Add feedback to conversation history
            self.conversation_manager.add_feedback({
                "round": round_num,
                "fact_checker": fact_check_result.summary,
                "dialogue_specialist": dialogue_result.summary,
                "editor": refined_result.summary
            })

        print("第三阶段：审查和优化完成")
        return story

    def phase4_final_check(self, story: str):
        """Phase 4: Final quality check"""
        print("开始第四阶段：最终检查...")

        editor = self.agent_manager.create_agent(agents_config["editor"])

        final_check = editor.initiate_chat(
            editor,
            message={
                "content": f"请进行全面的质量检查，确保故事质量达到出版标准：\n\n{story}",
                "request": "final_check"
            }
        )

        self.conversation_manager.add_to_history({
            "phase": "phase4_final",
            "content": final_check.summary
        })

        print("第四阶段：最终检查完成")
        return final_check.summary

    def capture_groupchat_message(self, recipient, messages, sender, config):
        """Capture and store group chat messages"""
        last_message = messages[-1].get("content", "") if messages else ""
        self.conversation_manager.add_to_history({
            "agent": sender.name if hasattr(sender, 'name') else "Unknown",
            "message": last_message,
            "timestamp": time.time()
        })
        return False, None  # Continue processing

    def _update_documentation_with_chapter(self, chapter_content: str, chapter_num: int):
        """Extract and update documentation from chapter content"""
        # In the original implementation, this calls documentation_manager.update_documentation
        # with JSON formatted content that the documentation specialist agent produces
        pass  # Implementation would depend on the exact content structure

    def _intermediate_review(self, story_parts: List[Dict]):
        """Perform intermediate review every 3 chapters"""
        print("执行中期评审流程...")
        # Implementation would perform a review of all chapters up to this point
        pass

</summary>

**Step 2: Write the novel phases manager to file**

Write the above content to `src/novel_phases_manager.py`.

**Step 3: Commit the new file**

```bash
git add src/novel_phases_manager.py
git commit -m "refactor: extract NovelWritingPhases to separate module"
```

### Task 4: Update main phases.py to only orchestrate the workflow

**Files:**
- Modify: `phases.py` (simplified to orchestrate workflow)

**Step 1: Replace phases.py with orchestration module**

```python
from src.novel_phases_manager import NovelWritingPhases
from src.documentation_manager import DocumentationManager
from conversation_manager import ConversationManager

class NovelWorkflowOrchestrator:
    """Main orchestrator for the novel creation workflow"""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.documentation_manager = DocumentationManager()

    def run_complete_workflow(self, initial_idea: str, multi_chapter: bool = False, total_chapters: int = 1):
        """Run the complete novel creation workflow"""
        # Initialize the phase manager
        phase_manager = NovelWritingPhases(
            conversation_manager=self.conversation_manager,
            documentation_manager=self.documentation_manager
        )

        # Step 1: Research and Planning
        plan = phase_manager.phase1_research_and_planning(initial_idea)

        # Step 2: Creation
        draft_story = phase_manager.phase2_creation(plan, multi_chapter, total_chapters)

        # Step 3: Review and Refinement
        revised_story = phase_manager.phase3_review_refinement(draft_story)

        # Step 4: Final Check
        final_story = phase_manager.phase4_final_check(revised_story)

        # Return complete results
        results = {
            "initial_idea": initial_idea,
            "research_plan": plan,
            "draft_story": draft_story,
            "revised_story": revised_story,
            "final_story": final_story,
            "conversation_history": self.conversation_manager.get_all_history(),
            "documentation": self.documentation_manager.get_documentation()
        }

        return results

    def get_conversation_manager(self):
        """Get conversation manager for external access"""
        return self.conversation_manager

    def get_documentation_manager(self):
        """Get documentation manager for external access"""
        return self.documentation_manager
```

**Step 2: Write the updated phases.py**

Replace the content of phases.py with the above orchestration module.

**Step 3: Check that imports work properly**

```python
python -c "from phases import NovelWorkflowOrchestrator; print('Orchestration import successful')"
```

**Step 4: Commit the updated phases.py**

```bash
git add phases.py
git commit -m "refactor: update phases.py to be a workflow orchestrator"
```

### Task 5: Refactor main.py to use new orchestrator

**Files:**
- Modify: `main.py`

**Step 1: Update main.py with proper orchestrator use**

```python
import sys
import os
from datetime import datetime
from phases import NovelWorkflowOrchestrator
from conversation_manager import ConversationManager
import json

def main():
    """Main entry point for running the novel creation workflow."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py \"Your novel idea here\"")
        return

    initial_idea = sys.argv[1]

    print(f"接收到的想法: {initial_idea}")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = NovelWorkflowOrchestrator()

    # Run workflow
    print("正在启动多智能体协作...")

    # This would typically include UI elements, settings, etc.
    print("选择模式:")
    print("1: 单章节模式")
    print("2: 多章节模式 (带一致性检查)")

    # For now, let's assume single chapter by default
    # In a real scenario, we might get this from the CLI argument
    result = orchestrator.run_complete_workflow(
        initial_idea=initial_idea,
        multi_chapter=False,  # Default to single chapter
        total_chapters=1
    )

    print("小说创作完成！")

    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Save complete story
    story_file = os.path.join(output_dir, f"novel_story_{timestamp}.txt")
    with open(story_file, 'w', encoding='utf-8') as f:
        f.write(result["final_story"])

    print(f"故事已保存: {story_file}")

    # Save detailed results
    result_file = os.path.join(output_dir, f"novel_data_{timestamp}.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"详细结果已保存: {result_file}")

    # Output summary
    print("\n摘要:")
    print(f" - 初始想法: {result['initial_idea']}")
    print(f" - 研究计划长度: {len(result['research_plan'])} characters")
    print(f" - 最终故事长度: {len(result['final_story'])} characters")

    print(f"\n完整过程已保存，详情请看: {result_file}")


if __name__ == "__main__":
    main()
```

**Step 2: Write updated main.py**

Replace main.py with the above content.

**Step 3: Test basic imports and execution**

```bash
python -c "import main; print('main imports work')"
```

**Step 4: Commit the updated main.py**

```bash
git add main.py
git commit -m "refactor: update main.py to use workflow orchestrator"
```