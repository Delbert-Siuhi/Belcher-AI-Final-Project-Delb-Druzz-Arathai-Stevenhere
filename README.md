# Title

PiFlow: Local AI Classroom Vision Monitor

# Authors / Programmers

Andreas

Delbert

Arath

Steven

Victor

# Date Due

May 21, 2026

# Date Submitted

May 20, 2026

# Project Overview

## High Concept

PiFlow is a fully local Raspberry Pi 5 camera monitor that uses the AI HAT+ to detect classroom objects and people without sending images to the internet.

It watches for useful labels such as person, backpack, laptop, book, phone, and chair, then prints, logs, and optionally speaks detection events.

## Problem or Purpose

Many AI demos depend on cloud APIs, paid accounts, or laptops with large GPUs. This project explores what a small edge device can do locally with a Raspberry Pi 5 and AI HAT+.

The purpose is to create a privacy-friendly classroom assistant prototype. It can monitor whether useful classroom objects are present, log activity for a demo, and show how local inference differs from cloud AI.

## Target User

Students, teachers, robotics clubs, makers, and anyone testing local computer vision on Raspberry Pi hardware.

# AI System Design

## Model(s) Used

LLM name: NA. This project does not use a large language model because the standard Raspberry Pi AI HAT+ is designed for vision inference, not local LLM inference.

Vision model: YOLOv8 object detection through Raspberry Pi's Hailo post-processing file:

`/usr/share/rpi-camera-assets/hailo\_yolov8\_inference.json`

Optional alternate local vision models:

* YOLOv6: `/usr/share/rpi-camera-assets/hailo\_yolov6\_inference.json`
* YOLOv5: `/usr/share/rpi-camera-assets/hailo\_yolov5\_inference.json`
* YOLOX: `/usr/share/rpi-camera-assets/hailo\_yolox\_inference.json`

Speech tools: optional `espeak-ng`, `espeak`, or `spd-say` for local text-to-speech alerts.

Why these were chosen:

* YOLO models are fast object detectors.
* Raspberry Pi OS already supports Hailo model post-processing through `rpicam-apps`.
* The AI HAT+ accelerates supported vision inference locally.
* The project avoids paid APIs and cloud inference.

## Local Inference Design

What runs on the Pi:

* `rpicam-hello` captures camera frames.
* Raspberry Pi's Hailo post-processing pipeline runs YOLO object detection.
* PiFlow reads detection output, filters important objects, creates events, logs results, and triggers feedback.

Hardware acceleration used:

* Raspberry Pi 5 AI HAT+ Hailo NPU.
* The Hailo NPU runs the supported object detection model locally.

Performance observations:

* Demo mode runs on any computer for testing without hardware.
* Camera mode depends on the Raspberry Pi camera, `rpicam-apps`, Hailo driver, and `/dev/hailo0` being available.
* The default camera mode uses YOLOv8 at 15 FPS.
* Lowering FPS or switching to YOLOX may help if the Pi slows down.

Limitations of local hardware:

* The standard AI HAT+ does not run LLMs well. It is mainly for vision workloads.
* Detection accuracy depends on lighting, camera placement, and the pretrained model labels.
* The Pi must have the Hailo software stack installed.
* The project logs detections, not full video.

## Prompting / Logic / Workflow

Prompts used: NA. This project does not use an LLM prompt.

Memory or context handling:

* The system keeps a short cooldown memory per detected label.
* This prevents repeated alerts for the same object every frame.
* Logs are saved to CSV and JSONL for review.

Decision logic:

1. Read detections from camera mode or demo mode.
2. Normalize labels and confidence scores.
3. Keep only watched labels.
4. Ignore detections below the confidence threshold.
5. Ignore repeated labels during the cooldown period.
6. Create a readable event message.
7. Print, log, speak, or pulse GPIO feedback.

Multi-step pipeline:

Camera frame → local Hailo YOLO inference → parsed detections → confidence filter → watchlist filter → cooldown filter → event output.

## User Interaction

Inputs:

* Raspberry Pi camera feed in camera mode.
* Simulated detections in demo mode.
* Optional command-line controls for model, confidence threshold, watch labels, logging, speech, LED, and buzzer.

Outputs:

* Terminal messages.
* `logs/detections.csv`.
* `logs/events.jsonl`.
* Optional local speech alerts.
* Optional GPIO LED or buzzer pulse.

Interface:

Command-line interface named `piflow`.

Controls:

* `--source camera` or `--source demo`
* `--model yolov8`, `yolov6`, `yolov5`, or `yolox`
* `--min-confidence 0.55`
* `--watch person,backpack,laptop`
* `--speak`
* `--gpio-led 17`
* `--gpio-buzzer 27`

How feedback is given:

The user sees readable detection events in the terminal. If enabled, the Pi also speaks alerts or pulses connected GPIO devices.

# Implementation

## How to Run

### 1\. Copy the project to the Raspberry Pi

Unzip the project on the Pi:

```bash
unzip piflow\_final.zip
cd piflow\_final
```

### 2\. Install Raspberry Pi and Python dependencies

Run:

```bash
chmod +x install.sh run\_demo.sh run\_camera.sh
./install.sh
```

The install script runs:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip rpicam-apps hailo-all espeak-ng
python3 -m venv .venv --system-site-packages
. .venv/bin/activate
pip install -e .
```

Restart the Pi after installing `hailo-all` if `/dev/hailo0` does not appear.

### 3\. Check hardware and software status

Run:

```bash
. .venv/bin/activate
piflow doctor
```

Expected Pi hardware signs:

* `rpicam-hello` shows OK.
* `Hailo device` shows OK.
* At least one Hailo model config shows OK.

### 4\. Run demo mode first

Demo mode does not need a camera or AI HAT+:

```bash
./run\_demo.sh
```

Or:

```bash
. .venv/bin/activate
piflow run --source demo --duration 15 --cooldown 1
```

### 5\. Run camera mode on the Raspberry Pi

```bash
./run\_camera.sh
```

Or:

```bash
. .venv/bin/activate
piflow run --source camera --model yolov8 --min-confidence 0.55
```

### 6\. Optional speech output

```bash
piflow run --source camera --speak
```

### 7\. Optional GPIO feedback

Connect an LED to GPIO 17 or a buzzer to GPIO 27, then run:

```bash
piflow run --source camera --gpio-led 17 --gpio-buzzer 27
```

### 8\. Optional systemd startup

Edit `piflow.service` if your project path is not `/home/pi/piflow\_final`, then install it:

```bash
sudo cp piflow.service /etc/systemd/system/piflow.service
sudo systemctl daemon-reload
sudo systemctl enable piflow.service
sudo systemctl start piflow.service
```

View logs:

```bash
journalctl -u piflow.service -f
```

## Platform / Tools

* Python 3
* Raspberry Pi OS
* Raspberry Pi `rpicam-apps`
* Hailo AI HAT+ software stack through `hailo-all`
* YOLO object detection model through Raspberry Pi camera assets
* Optional `espeak-ng`
* Optional `gpiozero`

## Hardware Used

Required:

* Raspberry Pi 5
* Raspberry Pi AI HAT+
* Raspberry Pi camera module or compatible camera
* microSD card with Raspberry Pi OS
* Power supply

Optional:

* Speaker for speech output
* LED connected to GPIO 17
* Buzzer connected to GPIO 27
* Raspberry Pi Active Cooler

# Evaluation

## What Works Well

* Demo mode runs without Pi hardware, so the project can be tested quickly.
* Camera mode uses local AI inference through the AI HAT+ pipeline.
* The code avoids paid APIs and cloud services.
* The parser accepts multiple detection output formats, including JSON-style lines and text-style lines.
* The system creates useful logs for the presentation.
* Command-line options make the project easy to adjust during a live demo.

## Known Limitations / Issues

* Camera mode must be tested on the actual Raspberry Pi 5 with AI HAT+ hardware.
* The sandbox environment used for development does not have `/dev/hailo0`, a Raspberry Pi camera, or `rpicam-hello`.
* Detection labels are limited to the model's trained classes.
* The system does not store images or video.
* The standard AI HAT+ is not intended for local LLM work.

## Future Improvements

* Add a small web dashboard with live event history.
* Add a button to switch between quiet mode and speech mode.
* Add object-count graphs from the CSV logs.
* Add a photo capture button when an important object appears.
* Add more GPIO controls for robotics demos.
* Add a separate AI HAT+ 2 version with a local LLM or vision-language model.

# Academic Integrity

## Honor Statement

I certify that this project represents our own work. Any outside resources, tools, or assistance are listed in the disclosure and bibliography sections.

Digitally signed:

* Andreas Zhou, May 17, 2026

## AI / Collaboration Disclosure

ChatGPT helped package the project, write Python code, debug tests, and write the README.

No paid AI API or cloud inference is required to run the project.

# References

## Bibliography

* Raspberry Pi Documentation, AI HATs: https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
* Raspberry Pi Documentation, AI software on Raspberry Pi 5: https://www.raspberrypi.com/documentation/computers/ai.html
* Hailo Raspberry Pi 5 examples: https://github.com/hailo-ai/hailo-rpi5-examples
* Raspberry Pi camera software documentation: https://www.raspberrypi.com/documentation/computers/camera\_software.html
* YOLO object detection family, Ultralytics documentation: https://docs.ultralytics.com
* Python documentation: https://docs.python.org/3/

## Resources / Tutors

ChatGPT helped with coding, debugging, packaging, and documentation.

# Reflection

## Andreas Reflection

Approximate total development time: 8 hours.

Biggest challenge encountered: I think that the hardest part was designing a project that runs locally on the Pi but we had to test it without it, which was hard.
How the group solved it: We had two ways, where the first way was a demo way, and that runs with anything, and the other way has a camera way, that used a camera.
What I learned: I learned how powerful AI is as a tool for vibe-coding, but also, we had to be more and more specific with prompts. It was also really cool to expirement
with my first Raspberry PI.

## Arath Reflection
Approximate total development time: 8 hours.

Biggest Challenge: I think that the biggest challenge we had was resolving package and library issues and making sure the rasberry pi was able to use the camera.
How the group solved it: We used several Linux tools to check if the hardware was installed and debugged my isolating the issues to make sure we had the correct packages. 
What I learned: I learned that AI can be powerful, but only if you know what you are doing and are able to figure out what AI is saying. It was also cool to learn how to use a 
raspberry pi as I have never used one before.

rpicam-hello -t 10000 \
--post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json \
--framerate 15 \
-v 2 \
-n 2>&1 | tee hailo_raw.txt

