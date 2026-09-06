import queue
import time

from PIL import Image

from monitor35.runtime import MonitorWorker, Snapshot, disk_root
from monitor35.session import DisplaySession, Status
from monitor35.theme import default_theme


def test_invalid_sensor_path_reports_error_and_worker_stops(tmp_path):
    worker = MonitorWorker(default_theme(), str(tmp_path / "missing"))
    worker.start()
    try:
        snapshot = worker.snapshots.get(timeout=3)
    finally:
        worker.request_stop()
        worker.join(timeout=3)
    assert snapshot.status.state == "오류"
    assert not worker.is_alive()


def test_latest_value_mailbox_drops_stale_snapshots():
    worker = MonitorWorker(default_theme(), disk_root())
    image = Image.new("RGB", (480, 320))
    for value in range(100):
        worker.publish(Snapshot(image, {"cpu": value}, Status()))
    assert worker.snapshots.get_nowait().values["cpu"] == 99
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

    worker = MonitorWorker(default_theme(), disk_root())
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
