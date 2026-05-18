from __future__ import annotations

import platform
import shutil
from pathlib import Path

from .providers import MODEL_FILES, model_file_status


def check() -> list[tuple[str, bool, str]]:
    rows: list[tuple[str, bool, str]] = []
    rows.append(("Python", True, platform.python_version()))
    rows.append(("rpicam-hello", shutil.which("rpicam-hello") is not None, shutil.which("rpicam-hello") or "missing"))
    rows.append(("Hailo device", Path("/dev/hailo0").exists(), "/dev/hailo0" if Path("/dev/hailo0").exists() else "missing"))
    rows.append(("Text to speech", (shutil.which("espeak-ng") or shutil.which("espeak") or shutil.which("spd-say")) is not None, shutil.which("espeak-ng") or shutil.which("espeak") or shutil.which("spd-say") or "optional"))

    try:
        import gpiozero  # type: ignore  # noqa: F401
        rows.append(("gpiozero", True, "available"))
    except Exception:
        rows.append(("gpiozero", False, "optional, needed only for LED/buzzer"))

    for name, exists in model_file_status().items():
        rows.append((f"Model config {name}", exists, MODEL_FILES[name]))
    return rows


def format_rows(rows: list[tuple[str, bool, str]]) -> str:
    width = max(len(name) for name, _, _ in rows)
    lines = []
    for name, ok, detail in rows:
        status = "OK" if ok else "MISS"
        lines.append(f"{name:<{width}}  {status:<4}  {detail}")
    return "\n".join(lines)
