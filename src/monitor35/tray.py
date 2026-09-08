"""Windows tray lifecycle; callbacks enqueue commands and never touch Tk."""

import logging
import queue
import threading

import pystray

from monitor35.icon import app_icon

logger = logging.getLogger(__name__)


class Tray:
    def __init__(self):
        self.commands: queue.SimpleQueue[str] = queue.SimpleQueue()
        self.ready = threading.Event()
        self.stopping = threading.Event()
        self.icon = None
        self.thread = threading.Thread(target=self.run, name="monitor35-tray", daemon=True)
        try:
            self.icon = pystray.Icon(
                "Monitor35",
                app_icon(),
                "Monitor35 · 백그라운드 모니터링",
                menu=pystray.Menu(
                    pystray.MenuItem(
                        "편집기 열기", lambda: self.commands.put("show"), default=True
                    ),
                    pystray.MenuItem("완전히 종료", lambda: self.commands.put("quit")),
                ),
            )
        except Exception:
            logger.exception("tray_create_failed")
            self.commands.put("failed")
            return
        self.thread.start()

    def setup(self, icon):
        try:
            if self.stopping.is_set():
                icon.stop()
            else:
                icon.visible = True
                self.ready.set()
        except Exception:
            logger.exception("tray_setup_failed")
            self.commands.put("failed")

    def run(self):
        try:
            assert self.icon is not None
            self.icon.run(setup=self.setup)
        except Exception:
            logger.exception("tray_failed")
        finally:
            self.ready.clear()
            if not self.stopping.is_set():
                self.commands.put("failed")

    def close(self):
        self.stopping.set()
        self.ready.clear()
        if self.icon is not None:
            self.icon.stop()

    def is_alive(self) -> bool:
        return self.thread.is_alive()
