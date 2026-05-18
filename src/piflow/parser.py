from __future__ import annotations

import json
import re
from typing import Any, Iterable

from .models import Detection

COCO_LABELS = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
    "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush",
}

_SCORE = r"(?P<score>100(?:\.0+)?|\d{1,2}(?:\.\d+)?|0?\.\d+|1(?:\.0+)?)\s*%?"
_LABEL = r"(?P<label>[A-Za-z][A-Za-z0-9 _-]{1,40})"

PATTERNS = [
    re.compile(rf"(?:label|class|name)\s*[:=]\s*['\"]?{_LABEL}['\"]?.*?(?:confidence|conf|score|probability)\s*[:=]\s*{_SCORE}", re.I),
    re.compile(rf"{_LABEL}\s*[,; ]+\s*(?:confidence|conf|score|probability)\s*[:=]\s*{_SCORE}", re.I),
    re.compile(rf"{_LABEL}\s*[:=]\s*{_SCORE}", re.I),
]


def normalize_label(label: str) -> str:
    label = label.strip().strip('"\'').replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).lower()
    return label


def normalize_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0:
        return None
    if score > 1.0 and score <= 100.0:
        score = score / 100.0
    if score > 1.0:
        return None
    return score


def _iter_json_candidates(line: str) -> Iterable[Any]:
    text = line.strip()
    if not text:
        return
    try:
        yield json.loads(text)
    except json.JSONDecodeError:
        pass

    for match in re.finditer(r"\{.*?\}", text):
        try:
            yield json.loads(match.group(0))
        except json.JSONDecodeError:
            continue


def first_present(obj: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in obj:
            return obj[key]
    return None


def _detections_from_json_obj(obj: Any, raw: str) -> list[Detection]:
    found: list[Detection] = []
    if isinstance(obj, dict):
        if "detections" in obj and isinstance(obj["detections"], list):
            for item in obj["detections"]:
                found.extend(_detections_from_json_obj(item, raw))
            return found
        if "objects" in obj and isinstance(obj["objects"], list):
            for item in obj["objects"]:
                found.extend(_detections_from_json_obj(item, raw))
            return found

        label = first_present(obj, ["label", "class", "name"])
        score = first_present(obj, ["confidence", "conf", "score", "probability"])
        norm_score = normalize_score(score)
        if label and norm_score is not None:
            box = obj.get("box") or obj.get("bbox")
            if not isinstance(box, dict):
                box = None
            found.append(Detection(label=normalize_label(str(label)), confidence=norm_score, box=box, raw=raw))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_detections_from_json_obj(item, raw))
    return found


def parse_line(line: str, allowed_labels: set[str] | None = None) -> list[Detection]:
    """Parse a line from rpicam/Hailo output into detections.

    The Raspberry Pi camera stack prints different formats across versions.
    This parser accepts JSON-ish lines and common text lines such as:
      label=person confidence=0.91
      person confidence: 91%
      person:0.91
    """
    raw = line.rstrip("\n")
    allowed = {normalize_label(x) for x in allowed_labels} if allowed_labels else None
    detections: list[Detection] = []

    for obj in _iter_json_candidates(raw):
        detections.extend(_detections_from_json_obj(obj, raw))

    if detections:
        return _filter_allowed(detections, allowed)

    for pattern in PATTERNS:
        for match in pattern.finditer(raw):
            label = normalize_label(match.group("label"))
            score = normalize_score(match.group("score"))
            if score is None:
                continue
            if label not in COCO_LABELS and allowed is None:
                continue
            detections.append(Detection(label=label, confidence=score, raw=raw))

    return _dedupe(_filter_allowed(detections, allowed))


def _filter_allowed(detections: list[Detection], allowed: set[str] | None) -> list[Detection]:
    if not allowed:
        return detections
    return [d for d in detections if d.label in allowed]


def _dedupe(detections: list[Detection]) -> list[Detection]:
    seen: set[tuple[str, float]] = set()
    unique: list[Detection] = []
    for det in detections:
        key = (det.label, round(det.confidence, 3))
        if key in seen:
            continue
        seen.add(key)
        unique.append(det)
    return unique
