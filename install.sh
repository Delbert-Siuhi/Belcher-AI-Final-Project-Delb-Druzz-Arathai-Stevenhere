#!/usr/bin/env bash
set -u

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "Installing PiFlow system packages."
sudo apt update
sudo apt install -y python3-venv python3-pip rpicam-apps hailo-all espeak-ng

if [ ! -d ".venv" ]; then
  python3 -m venv .venv --system-site-packages
fi

. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

mkdir -p logs

echo "Running PiFlow doctor. Missing camera/Hailo items are expected if this is not the Raspberry Pi."
piflow doctor || true

echo "Install complete. Run ./run_demo.sh first, then ./run_camera.sh on the Pi."
