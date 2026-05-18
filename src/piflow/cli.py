from __future__ import annotations

import argparse
import signal
import sys
from typing import Iterable

from .config import load_config
from .doctor import check, format_rows
from .gpio import GpioPulse
from .logic import MonitorConfig, EventFilter
from .output import ConsoleOutput, CsvLogger, JsonlLogger, MultiOutput, Speaker
from .parser import normalize_label
from .providers import CameraSourceConfig, camera_detections, demo_detections


def parse_labels(value: str | None) -> set[str] | None:
    if not value:
        return None
    labels = {normalize_label(part) for part in value.split(",") if part.strip()}
    return labels or None


def apply_overrides(config: MonitorConfig, args: argparse.Namespace) -> MonitorConfig:
    if args.min_confidence is not None:
        config.min_confidence = args.min_confidence
    if args.cooldown is not None:
        config.cooldown_seconds = args.cooldown
    labels = parse_labels(args.watch)
    if labels:
        config.watch_labels = labels
    config.__post_init__()
    return config


def build_outputs(args: argparse.Namespace) -> tuple[MultiOutput, list[object]]:
    outputs: list[object] = []
    cleanup: list[object] = []
    if not args.no_console:
        outputs.append(ConsoleOutput())
    if args.csv:
        outputs.append(CsvLogger(args.csv))
    if args.jsonl:
        outputs.append(JsonlLogger(args.jsonl))
    if args.speak:
        speaker = Speaker()
        outputs.append(speaker)
        if not speaker.available():
            print("Speech requested, but no espeak-ng/espeak/spd-say command was found.", file=sys.stderr)
    if args.gpio_led is not None or args.gpio_buzzer is not None:
        gpio = GpioPulse(led_pin=args.gpio_led, buzzer_pin=args.gpio_buzzer)
        outputs.append(gpio)
        cleanup.append(gpio)
        if not gpio.ready:
            print(f"GPIO requested, but unavailable: {gpio.error or 'no pins configured'}", file=sys.stderr)
    if not outputs:
        outputs.append(ConsoleOutput())
    return MultiOutput(outputs), cleanup


def run(args: argparse.Namespace) -> int:
    config = apply_overrides(load_config(args.config), args)
    event_filter = EventFilter(config)
    output, cleanup = build_outputs(args)
    stop = False

    def handle_signal(signum: int, frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if args.source == "demo":
        stream = demo_detections(interval_seconds=args.interval, duration_seconds=args.duration)
    else:
        camera_config = CameraSourceConfig(
            model=args.model,
            duration_seconds=args.duration,
            framerate=args.framerate,
            no_preview=args.no_preview,
        )
        stream = camera_detections(camera_config, allowed_labels=config.watch_labels)

    try:
        for detections in stream:
            if stop:
                break
            event = event_filter.make_event(detections)
            if event:
                output.write(event)
    finally:
        for item in cleanup:
            close = getattr(item, "close", None)
            if callable(close):
                close()
    return 0


def doctor(args: argparse.Namespace) -> int:
    rows = check()
    print(format_rows(rows))
    return 0 if all(ok or name in {"Text to speech", "gpiozero"} for name, ok, _ in rows) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="piflow", description="Local Raspberry Pi AI HAT+ vision monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run the monitor")
    run_parser.add_argument("--source", choices=["camera", "demo"], default="camera")
    run_parser.add_argument("--duration", type=int, default=0, help="seconds, 0 means forever")
    run_parser.add_argument("--config", default=None, help="path to JSON config")
    run_parser.add_argument("--min-confidence", type=float, default=None)
    run_parser.add_argument("--cooldown", type=float, default=None, help="seconds between repeated alerts per label")
    run_parser.add_argument("--watch", default=None, help="comma-separated labels to watch")
    run_parser.add_argument("--csv", default="logs/detections.csv")
    run_parser.add_argument("--jsonl", default="logs/events.jsonl")
    run_parser.add_argument("--no-console", action="store_true")
    run_parser.add_argument("--speak", action="store_true")
    run_parser.add_argument("--gpio-led", type=int, default=None)
    run_parser.add_argument("--gpio-buzzer", type=int, default=None)
    run_parser.add_argument("--interval", type=float, default=1.0, help="demo source interval")
    run_parser.add_argument("--model", choices=["yolov8", "yolov6", "yolov5", "yolox"], default="yolov8")
    run_parser.add_argument("--framerate", type=int, default=15)
    run_parser.add_argument("--preview", dest="no_preview", action="store_false", help="show camera preview window")
    run_parser.set_defaults(func=run)

    doctor_parser = sub.add_parser("doctor", help="check Pi/Hailo dependencies")
    doctor_parser.set_defaults(func=doctor)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
