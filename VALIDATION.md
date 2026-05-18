# Validation

Validated in the sandbox:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m compileall -q src
PYTHONPATH=src python -m piflow run --source demo --duration 1 --interval 0.1 --cooldown 0
PYTHONPATH=src python -m piflow doctor
```

Results:

- 9 unit tests passed.
- Python source compiled successfully.
- Demo mode printed detection events and created CSV/JSONL logs.
- Doctor command correctly reported missing Raspberry Pi hardware in the sandbox.

Not validated in the sandbox:

- Camera mode with Raspberry Pi camera.
- Hailo AI HAT+ acceleration through `/dev/hailo0`.
- GPIO LED/buzzer output.

Those require the physical Raspberry Pi 5, AI HAT+, and camera.
