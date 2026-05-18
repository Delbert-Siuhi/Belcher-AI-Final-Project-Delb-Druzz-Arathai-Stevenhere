from __future__ import annotations

import time
from typing import Any

from .models import Event


class GpioPulse:
    def __init__(self, led_pin: int | None = None, buzzer_pin: int | None = None, pulse_seconds: float = 0.18) -> None:
        self.led_pin = led_pin
        self.buzzer_pin = buzzer_pin
        self.pulse_seconds = pulse_seconds
        self._devices: list[Any] = []
        self._ready = False
        self._error: str | None = None
        self._setup()

    def _setup(self) -> None:
        pins = [pin for pin in [self.led_pin, self.buzzer_pin] if pin is not None]
        if not pins:
            self._ready = False
            return
        try:
            from gpiozero import LED  # type: ignore
        except Exception as exc:  # pragma: no cover, hardware dependent
            self._error = f"gpiozero unavailable: {exc}"
            self._ready = False
            return
        try:
            self._devices = [LED(pin) for pin in pins]
            self._ready = True
        except Exception as exc:  # pragma: no cover, hardware dependent
            self._error = f"GPIO setup failed: {exc}"
            self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def error(self) -> str | None:
        return self._error

    def write(self, event: Event) -> None:
        if not self._ready:
            return
        for device in self._devices:
            device.on()
        time.sleep(self.pulse_seconds)
        for device in self._devices:
            device.off()

    def close(self) -> None:
        for device in self._devices:
            close = getattr(device, "close", None)
            if callable(close):
                close()
