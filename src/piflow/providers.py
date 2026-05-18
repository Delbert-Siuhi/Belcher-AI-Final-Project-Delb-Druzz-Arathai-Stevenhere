from __future__ import annotations

import itertools
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .models import Detection
from .parser import parse_line

MODEL_FILES = {
    "yolov8": "/usr/share/rpi-camera-assets/hailo_yolov8_inference.json",
    "yolov6": "/usr/share/rpi-camera-assets/hailo_yolov6_inference.json",
    "yolov5": "/usr/share/rpi-camera-assets/hailo_yolov5_inference.json",
    "yolox": "/usr/share/rpi-camera-assets/hailo_yolox_inference.json",
}


@dataclass(frozen=True)
class CameraSourceConfig:
    model: str = "yolov8"
    duration_seconds: int = 0
    framerate: int = 15
    no_preview: bool = True
    extra_args: tuple[str, ...] = ()


def build_rpicam_command(config: CameraSourceConfig) -> list[str]:
    model_file = MODEL_FILES.get(config.model)
    if not model_file:
        raise ValueError(f"Unknown model {config.model!r}. Choose one of: {', '.join(sorted(MODEL_FILES))}")

    duration_ms = "0" if config.duration_seconds <= 0 else str(int(config.duration_seconds * 1000))
    command = [
        "rpicam-hello",
        "-t", duration_ms,
        "--post-process-file", model_file,
        "--framerate", str(config.framerate),
        "-v", "2",
    ]
    if config.no_preview:
        command.append("-n")
    command.extend(config.extra_args)
    return command


def camera_detections(config: CameraSourceConfig, allowed_labels: set[str] | None = None) -> Iterator[list[Detection]]:
    if shutil.which("rpicam-hello") is None:
        raise RuntimeError("rpicam-hello was not found. Install rpicam-apps on Raspberry Pi OS.")

    command = build_rpicam_command(config)
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            detections = parse_line(line, allowed_labels=allowed_labels)
            if detections:
                yield detections
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


def demo_detections(interval_seconds: float = 1.0, duration_seconds: int = 10) -> Iterator[list[Detection]]:
    frames = [
        [Detection(label="person", confidence=0.91, raw="demo frame 1")],
        [Detection(label="person", confidence=0.88, raw="demo frame 2"), Detection(label="backpack", confidence=0.72, raw="demo frame 2")],
        [Detection(label="cell phone", confidence=0.83, raw="demo frame 3")],
        [Detection(label="chair", confidence=0.64, raw="demo frame 4"), Detection(label="book", confidence=0.60, raw="demo frame 4")],
        [Detection(label="dog", confidence=0.87, raw="demo frame 5")],
    ]
    started = time.monotonic()
    for frame in itertools.cycle(frames):
        if duration_seconds > 0 and time.monotonic() - started >= duration_seconds:
            return
        yield frame
        time.sleep(max(interval_seconds, 0))


def model_file_status() -> dict[str, bool]:
    return {name: Path(path).exists() for name, path in MODEL_FILES.items()}
