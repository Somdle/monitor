import queue
import time
from dataclasses import replace

import pytest
from PIL import Image

from monitor35.render import render
from monitor35.runtime import MonitorWorker, Snapshot
from monitor35.sensors import Telemetry
from monitor35.session import DisplaySession, Status
from monitor35.theme import default_theme


@pytest.mark.parametrize("rotated", [False, True])
def test_rotation_only_affects_device_output(rotated):
    frames = []

    class Display:
        port = "COM4"

        def paint(self, image, pos=(0, 0)):
            frames.append(image.copy())

        def brightness(self, value):
            pass

        def close(self):
            pass

    theme = replace(default_theme(), rotate_180=rotated)
    worker = MonitorWorker(theme)
    worker.session = DisplaySession(Display)
    worker.enabled.set()
    worker.start()
    try:
        snapshot = worker.snapshots.get(timeout=3)
    finally:
        worker.request_stop()
        worker.join(timeout=3)
    assert not worker.is_alive()
    assert snapshot.status.state == "전송 중"
    upright = render(default_theme(), snapshot.values)
    assert snapshot.image.tobytes() == upright.tobytes()
    expected = upright.transpose(Image.Transpose.ROTATE_180) if rotated else upright
    assert frames[0].tobytes() == expected.tobytes()


def test_sensor_failure_reports_error_and_worker_stops(monkeypatch):
    def fail():
        raise OSError("sensor unavailable")

    monkeypatch.setattr("psutil.virtual_memory", fail)
    worker = MonitorWorker(default_theme())
    worker.start()
    try:
        snapshot = worker.snapshots.get(timeout=3)
    finally:
        worker.request_stop()
        worker.join(timeout=3)
    assert snapshot.status.state == "오류"
    assert not worker.is_alive()


def test_latest_value_mailbox_drops_stale_snapshots():
    worker = MonitorWorker(default_theme())
    image = Image.new("RGB", (480, 320))
    for value in range(100):
        worker.publish(Snapshot(image, Telemetry(cpu=value), Status()))
    assert worker.snapshots.get_nowait().values.cpu == 99
    try:
        worker.snapshots.get_nowait()
    except queue.Empty:
        return
    raise AssertionError("Stale snapshots remained queued")


def test_worker_suspends_promptly_without_frames_until_resume():
    events = []

    class Display:
        port = "COM4"

        def paint(self, image, pos=(0, 0)):
            events.append("frame")

        def brightness(self, value):
            events.append("brightness")

        def screen_off(self):
            events.append("off")

        def close(self):
            events.append("close")

    worker = MonitorWorker(default_theme())
    worker.session = DisplaySession(Display)
    worker.enabled.set()
    worker.start()
    try:
        assert worker.snapshots.get(timeout=3).status.state == "전송 중"
        worker.request_suspend()
        assert worker.suspend_complete.is_set()
        assert worker.screen_off_succeeded
        assert events[-2:] == ["off", "close"]
        count = len(events)
        time.sleep(0.15)
        assert len(events) == count
        worker.request_resume()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            snapshot = worker.snapshots.get(timeout=1)
            if snapshot.status.state == "전송 중":
                break
        assert events[-2:] == ["brightness", "frame"]
    finally:
        worker.request_stop()
        worker.join(timeout=3)
    assert not worker.is_alive()
