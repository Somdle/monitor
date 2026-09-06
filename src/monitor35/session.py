"""Single owner of reconnection, retry pacing and last successful frame."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from PIL import Image, ImageChops

logger = logging.getLogger(__name__)
FULL_REFRESH_SECONDS = 30
RESUME_GAP_SECONDS = 5


class Display(Protocol):
    port: str

    def paint(self, image: Image.Image, pos: tuple[int, int] = (0, 0)) -> None: ...
    def brightness(self, value: int) -> None: ...
    def screen_off(self) -> None: ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class Status:
    state: str = "미리보기"
    detail: str = "화면 연결을 누르면 장치로 전송합니다."
    frames: int = 0
    failures: int = 0
    connections: int = 0
    last_sent: float | None = None
    retry_at: float = 0


class DisplaySession:
    def __init__(self, factory: Callable[[], Display]):
        self.factory = factory
        self.link: Display | None = None
        self.status = Status()
        self.previous: Image.Image | None = None
        self.last_tick: float | None = None
        self.last_full = 0.0
        self.applied_brightness: int | None = None
        self.retry_delay = 1.0

    def disconnect(self) -> None:
        if self.link:
            try:
                self.link.close()
            finally:
                self.link = None
        self.previous = None
        self.applied_brightness = None

    def reconnect(self) -> None:
        self.disconnect()
        self.status = Status(
            frames=self.status.frames,
            failures=self.status.failures,
            connections=self.status.connections,
        )
        self.retry_delay = 1.0
        self.last_tick = None
        logger.info("reconnect_requested")

    def suspend(self) -> bool:
        """Finish any current transaction, turn off the LCD, then release USB."""
        try:
            if self.link is None:
                logger.warning("screen_off_unavailable", extra={"reason": "no open connection"})
                return False
            self.link.screen_off()
            logger.info("screen_off_sent")
            return True
        except OSError as exc:
            logger.warning("screen_off_failed", extra={"reason": str(exc)})
            return False
        finally:
            self.disconnect()

    def tick(self, frame: Image.Image, brightness: int, now: float) -> Status:
        started = time.monotonic()
        if self.last_tick is not None and (
            now - self.last_tick > RESUME_GAP_SECONDS or now < self.last_tick
        ):
            logger.info("resume_gap_detected")
            self.reconnect()
        self.last_tick = now
        if now < self.status.retry_at:
            return self.status
        try:
            if self.link is None:
                self.link = self.factory()
                self.status = Status(
                    "연결 중",
                    self.link.port,
                    self.status.frames,
                    self.status.failures,
                    self.status.connections + 1,
                )
                logger.info("device_opened", extra={"port": self.link.port})
            if brightness != self.applied_brightness:
                self.link.brightness(brightness)
                self.applied_brightness = brightness
            full = self.previous is None or now - self.last_full >= FULL_REFRESH_SECONDS
            bounds = None
            if not full and self.previous is not None:
                bounds = ImageChops.difference(frame, self.previous).getbbox()
            if full:
                self.link.paint(frame)
                self.last_full = now + time.monotonic() - started
            elif bounds:
                self.link.paint(frame.crop(bounds), bounds[:2])
            if full or bounds:
                self.previous = frame.copy()
                self.status = Status(
                    "전송 중",
                    self.link.port,
                    self.status.frames + 1,
                    self.status.failures,
                    self.status.connections,
                    now + time.monotonic() - started,
                )
                self.retry_delay = 1.0
            return self.status
        except OSError as exc:
            self.disconnect()
            self.status = Status(
                "재연결 대기",
                str(exc),
                self.status.frames,
                self.status.failures + 1,
                self.status.connections,
                self.status.last_sent,
                now + time.monotonic() - started + self.retry_delay,
            )
            logger.warning(
                "device_retry", extra={"reason": str(exc), "retry_seconds": self.retry_delay}
            )
            self.retry_delay = min(15, self.retry_delay * 2)
            return self.status
        finally:
            # Exclude our own blocking USB transaction from resume-gap detection.
            self.last_tick = now + time.monotonic() - started
