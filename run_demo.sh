#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p logs
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
  piflow run --source demo --duration 15 --cooldown 1 --csv logs/detections.csv --jsonl logs/events.jsonl
else
  PYTHONPATH=src python3 -m piflow run --source demo --duration 15 --cooldown 1 --csv logs/detections.csv --jsonl logs/events.jsonl
fi
