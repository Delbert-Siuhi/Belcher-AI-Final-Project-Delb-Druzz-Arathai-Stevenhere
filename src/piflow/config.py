from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .logic import DEFAULT_WATCH_LABELS, MonitorConfig


def load_config(path: str | Path | None) -> MonitorConfig:
    if not path:
        return MonitorConfig()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return MonitorConfig(
        min_confidence=float(data.get("min_confidence", 0.55)),
        cooldown_seconds=float(data.get("cooldown_seconds", 4.0)),
        watch_labels=set(data.get("watch_labels", sorted(DEFAULT_WATCH_LABELS))),
    )


def save_example(path: str | Path) -> None:
    data: dict[str, Any] = {
        "min_confidence": 0.55,
        "cooldown_seconds": 4.0,
        "watch_labels": sorted(DEFAULT_WATCH_LABELS),
    }
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
