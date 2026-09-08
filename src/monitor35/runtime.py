"""Worker boundary: sampling/rendering/serial I/O never run on the Tk thread."""

import logging
import queue
import threading
import time
from dataclasses import dataclass

from PIL import Image

from monitor35.device import TuringDisplay
from monitor35.render import render
from monitor35.sensors import Sampler, Telemetry
from monitor35.session import DisplaySession, Status
from monitor35.theme import HEIGHT, WIDTH, Theme

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Snapshot:
    image: Image.Image
    values: Telemetry
    status: Status


class MonitorWorker(threading.Thread):
    def __init__(self, theme: Theme):
        super().__init__(name="display-worker", daemon=True)
        self.lock = threading.Lock()
        self.theme = theme
        self.enabled = threading.Event()
        self.stop_requested = threading.Event()
        self.reconnect_requested = threading.Event()
        self.suspend_requested = threading.Event()
        self.suspend_complete = threading.Event()
        self.wake_requested = threading.Event()
        self.cancel_connect = threading.Event()
        self.screen_off_succeeded = False
        self.snapshots: queue.Queue[Snapshot] = queue.Queue(maxsize=1)
        self.session = DisplaySession(self._open)

    def _open(self) -> TuringDisplay:
        with self.lock:
            reset = self.theme.reset_on_connect
        return TuringDisplay(reset, self.cancel_connect.wait)

    def request_reconnect(self) -> None:
        self.reconnect_requested.set()
        self.wake_requested.set()

    def request_resume(self) -> None:
        self.suspend_requested.clear()
        self.cancel_connect.clear()
        self.request_reconnect()

    def request_suspend(self) -> None:
        self.suspend_complete.clear()
        self.suspend_requested.set()
        self.cancel_connect.set()
        self.wake_requested.set()
        # Windows allows about two seconds for PBT_APMSUSPEND. USB stays owned
        # by the worker; the window callback only waits for a bounded completion.
        if not self.suspend_complete.wait(1.5):
            logger.warning("suspend_deadline_exceeded")

    def request_stop(self) -> None:
        self.stop_requested.set()
        self.cancel_connect.set()
        self.wake_requested.set()

    def set_theme(self, theme: Theme) -> None:
        with self.lock:
            self.theme = theme

    def publish(self, snapshot: Snapshot) -> None:
        try:
            self.snapshots.get_nowait()
        except queue.Empty:
            pass  # Bounded latest-value mailbox may already have been consumed by UI.
        self.snapshots.put_nowait(snapshot)

    def run(self) -> None:
        sampler: Sampler | None = None
        values = Telemetry()
        frame = Image.new("RGB", (WIDTH, HEIGHT))
        try:
            sampler = Sampler()
            while not self.stop_requested.is_set():
                started = time.monotonic()
                if self.suspend_requested.is_set():
                    if not self.suspend_complete.is_set():
                        self.screen_off_succeeded = (
                            self.session.suspend() if self.enabled.is_set() else True
                        )
                        self.publish(
                            Snapshot(
                                frame,
                                values,
                                Status(
                                    "절전 대기",
                                    "화면 끄기 완료"
                                    if self.screen_off_succeeded
                                    else "화면 끄기 실패 · 로그를 확인해 주세요.",
                                ),
                            )
                        )
                        self.suspend_complete.set()
                    self.wake_requested.wait(0.1)
                    self.wake_requested.clear()
                    continue
                with self.lock:
                    theme = self.theme
                values = sampler.sample(theme.network_interface)
                frame = render(theme, values)
                if self.reconnect_requested.is_set():
                    self.reconnect_requested.clear()
                    self.session.reconnect()
                if self.enabled.is_set():
                    output = (
                        frame.transpose(Image.Transpose.ROTATE_180) if theme.rotate_180 else frame
                    )
                    status = self.session.tick(output, theme.brightness, time.time())
                else:
                    self.session.disconnect()
                    status = Status()
                self.publish(Snapshot(frame, values, status))
                self.wake_requested.wait(max(0.05, 1 - (time.monotonic() - started)))
                self.wake_requested.clear()
        except Exception as exc:
            logger.exception("worker_failed")
            self.publish(
                Snapshot(
                    frame,
                    values,
                    Status("오류", f"작업이 중지되었습니다: {exc}"),
                )
            )
        finally:
            self.session.disconnect()
            if sampler is not None:
                sampler.close()
