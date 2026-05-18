# PiFlow Demo Script

1. Explain the purpose:

PiFlow is a local AI vision monitor. It uses Raspberry Pi 5 and the AI HAT+ to detect objects locally without cloud APIs.

2. Show demo mode:

```bash
./run_demo.sh
```

Point out terminal alerts and log files.

3. Show doctor check on the Pi:

```bash
piflow doctor
```

Point out `rpicam-hello`, `/dev/hailo0`, and model config status.

4. Show camera mode:

```bash
./run_camera.sh
```

Hold up a backpack, phone, book, or laptop. Explain that YOLO detects objects, PiFlow filters the labels, then logs events.

5. Show logs:

```bash
tail logs/detections.csv
tail logs/events.jsonl
```

6. Explain design choices:

- Local inference protects privacy.
- YOLO is fast enough for live camera use.
- Cooldown logic prevents repeated spam.
- Demo mode makes the project testable without hardware.
