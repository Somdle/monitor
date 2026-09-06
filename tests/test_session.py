import pytest
from PIL import Image

from monitor35.session import DisplaySession


class FakeDisplay:
    """Fake only the external display boundary."""

    port = "COM4"

    def __init__(self):
        self.images = []
        self.levels = []
        self.closed = False
        self.fail = False

    def paint(self, image, pos=(0, 0)):
        if self.fail:
            raise OSError("USB disconnected during frame")
        self.images.append((image.copy(), pos))

    def brightness(self, value):
        self.levels.append(value)

    def screen_off(self):
        if self.fail:
            raise OSError("USB disconnected")
        self.levels.append("off")

    def close(self):
        self.closed = True


def test_first_frame_then_only_changed_rectangle():
    display = FakeDisplay()
    session = DisplaySession(lambda: display)
    frame = Image.new("RGB", (480, 320))
    session.tick(frame, 25, 0)
    session.tick(frame, 25, 1)
    changed = frame.copy()
    changed.putpixel((12, 30), (255, 0, 0))
    status = session.tick(changed, 25, 2)
    assert len(display.images) == 2
    assert display.images[0][0].size == (480, 320)
    assert display.images[1][0].size == (1, 1)
    assert display.images[1][1] == (12, 30)
    assert status.frames == 2
    assert display.levels == [25]


def test_failed_frame_closes_and_new_port_receives_full_latest_frame():
    first, replacement = FakeDisplay(), FakeDisplay()
    replacement.port = "COM7"
    ports = iter([first, replacement])
    session = DisplaySession(lambda: next(ports))
    original = Image.new("RGB", (480, 320))
    session.tick(original, 25, 0)
    first.fail = True
    changed = Image.new("RGB", (480, 320), "red")
    assert session.tick(changed, 25, 1).state == "재연결 대기"
    assert first.closed
    session.tick(changed, 25, 1.5)
    assert not replacement.images
    latest = Image.new("RGB", (480, 320), "blue")
    status = session.tick(latest, 25, 2.1)
    assert status.state == "전송 중"
    assert status.detail == "COM7"
    assert replacement.images[0][0].size == (480, 320)
    assert replacement.images[0][0].getpixel((0, 0)) == (0, 0, 255)
    assert replacement.levels == [25]


def test_unavailable_device_has_backoff_not_busy_loop():
    attempts = []

    def unavailable():
        attempts.append(1)
        raise OSError("port busy")

    session = DisplaySession(unavailable)
    frame = Image.new("RGB", (480, 320))
    for now in (0, 0.1, 0.5, 1.1, 1.2, 2, 3.2):
        session.tick(frame, 25, now)
    assert len(attempts) == 3
    assert session.status.retry_at == pytest.approx(7.2, abs=0.05)
    assert session.status.failures == 3


def test_resume_gap_reopens_and_redraws_even_unchanged_frame():
    first, resumed = FakeDisplay(), FakeDisplay()
    ports = iter([first, resumed])
    session = DisplaySession(lambda: next(ports))
    frame = Image.new("RGB", (480, 320))
    session.tick(frame, 25, 1)
    status = session.tick(frame, 25, 60)
    assert first.closed
    assert resumed.images[0][0].size == (480, 320)
    assert status.connections == 2


def test_explicit_resume_event_clears_retry_and_cached_frame():
    first, resumed = FakeDisplay(), FakeDisplay()
    ports = iter([first, resumed])
    session = DisplaySession(lambda: next(ports))
    frame = Image.new("RGB", (480, 320))
    session.tick(frame, 25, 1)
    session.reconnect()
    session.tick(frame, 25, 2)
    assert first.closed
    assert resumed.images[0][0].size == (480, 320)


def test_periodic_full_refresh_and_brightness_change():
    display = FakeDisplay()
    session = DisplaySession(lambda: display)
    frame = Image.new("RGB", (480, 320))
    for now in range(32):
        session.tick(frame, 35 if now > 10 else 25, now)
    assert len(display.images) == 2
    assert all(image.size == (480, 320) for image, _ in display.images)
    assert display.levels == [25, 35]


def test_suspend_turns_screen_off_and_resume_restores_full_frame():
    first, resumed = FakeDisplay(), FakeDisplay()
    ports = iter([first, resumed])
    session = DisplaySession(lambda: next(ports))
    frame = Image.new("RGB", (480, 320))
    session.tick(frame, 25, 1)
    assert session.suspend()
    assert first.levels == [25, "off"]
    assert first.closed
    session.reconnect()
    session.tick(frame, 25, 20)
    assert resumed.levels == [25]
    assert resumed.images[0][0].size == (480, 320)


def test_suspend_reports_failure_but_releases_broken_port():
    display = FakeDisplay()
    session = DisplaySession(lambda: display)
    session.tick(Image.new("RGB", (480, 320)), 25, 1)
    display.fail = True
    assert not session.suspend()
    assert display.closed
