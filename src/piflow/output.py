from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TextIO

from .models import Event


class ConsoleOutput:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout

    def write(self, event: Event) -> None:
        print(f"[{event.timestamp}] {event.message}", file=self.stream, flush=True)


class JsonlLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: Event) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")


class CsvLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "message", "label", "confidence", "raw"])
                writer.writeheader()

    def write(self, event: Event) -> None:
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "message", "label", "confidence", "raw"])
            for det in event.detections:
                writer.writerow({
                    "timestamp": event.timestamp,
                    "message": event.message,
                    "label": det.label,
                    "confidence": f"{det.confidence:.3f}",
                    "raw": det.raw,
                })


class Speaker:
    def __init__(self) -> None:
        self.command = shutil.which("espeak-ng") or shutil.which("espeak") or shutil.which("spd-say")

    def available(self) -> bool:
        return self.command is not None

    def write(self, event: Event) -> None:
        if not self.command:
            return
        try:
            subprocess.Popen([self.command, event.message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            return


class MultiOutput:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = outputs

    def write(self, event: Event) -> None:
        for output in self.outputs:
            write = getattr(output, "write", None)
            if callable(write):
                write(event)
