from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field

from .models import Detection, Event
from .parser import normalize_label


DEFAULT_WATCH_LABELS = {
    "person", "backpack", "cell phone", "laptop", "book", "bottle", "chair",
    "sports ball", "car", "dog", "cat",
}


@dataclass
class MonitorConfig:
    min_confidence: float = 0.55
    cooldown_seconds: float = 4.0
    watch_labels: set[str] = field(default_factory=lambda: set(DEFAULT_WATCH_LABELS))

    def __post_init__(self) -> None:
        self.watch_labels = {normalize_label(label) for label in self.watch_labels}
        if not 0 <= self.min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be nonnegative")


class EventFilter:
    def __init__(self, config: MonitorConfig) -> None:
        self.config = config
        self._last_event_by_label: dict[str, float] = {}

    def make_event(self, detections: list[Detection]) -> Event | None:
        now = time.monotonic()
        strong = [
            d for d in detections
            if d.confidence >= self.config.min_confidence and d.label in self.config.watch_labels
        ]
        if not strong:
            return None

        fresh = [d for d in strong if now - self._last_event_by_label.get(d.label, -1e9) >= self.config.cooldown_seconds]
        if not fresh:
            return None

        for det in fresh:
            self._last_event_by_label[det.label] = now

        message = summarize(fresh)
        return Event(message=message, detections=tuple(fresh))


def summarize(detections: list[Detection]) -> str:
    counts = Counter(d.label for d in detections)
    pieces = []
    for label, count in sorted(counts.items()):
        if count == 1:
            pieces.append(article(label) + " " + label)
        else:
            pieces.append(f"{count} {pluralize(label)}")
    return "Detected " + join_english(pieces) + "."


def article(label: str) -> str:
    return "an" if label[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def pluralize(label: str) -> str:
    if label.endswith("s"):
        return label
    if label.endswith("y") and label[-2:-1] not in {"a", "e", "i", "o", "u"}:
        return label[:-1] + "ies"
    return label + "s"


def join_english(items: list[str]) -> str:
    if not items:
        return "nothing"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]
