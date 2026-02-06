from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def default_config_path() -> Path:
    config_dir = Path.home() / ".config" / "storyglassy"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "session.json"


@dataclass
class StateStore:
    path: Path = field(default_factory=default_config_path)
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self.data = {}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()
