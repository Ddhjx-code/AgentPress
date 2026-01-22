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