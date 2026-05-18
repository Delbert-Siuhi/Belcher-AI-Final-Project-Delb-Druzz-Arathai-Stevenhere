from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: dict[str, float] | None = None
    raw: str = ""
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "box": self.box,
            "raw": self.raw,
        }


@dataclass(frozen=True)
class Event:
    message: str
    detections: tuple[Detection, ...]
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "message": self.message,
            "detections": [d.to_dict() for d in self.detections],
        }
