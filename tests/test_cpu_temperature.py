import contextlib
import json
import queue
import time

import pytest

from monitor35.cpu_temperature import CpuTemperature


def test_missing_cpu_library_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.prefix", str(tmp_path))
    probe = CpuTemperature()
    value, warning = probe.sample()
    assert value is None and warning
    probe.close()


@pytest.mark.parametrize("value", [65.5, None, 999, "invalid"])
def test_cpu_process_values_validation_and_shutdown(tmp_path, monkeypatch, value):
    library = tmp_path / "hardware/LibreHardwareMonitor/LibreHardwareMonitorLib.dll"
    library.parent.mkdir(parents=True)
    library.touch()
    monkeypatch.setattr("sys.prefix", str(tmp_path))
    monkeypatch.setattr("winreg.OpenKey", lambda *a: contextlib.nullcontext())
    messages = queue.Queue()

    class Stream:
        def __iter__(self):
            return self

        def __next__(self):
            line = messages.get(timeout=3)
            if line is None:
                raise StopIteration
            return line

        def close(self):
            pass

    class Process:
        stdout = Stream()
        stopped = False

        def poll(self):
            return 0 if self.stopped else None

        def terminate(self):
            self.stopped = True
            messages.put(None)

        def wait(self, timeout):
            return 0

    process = Process()
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: process)
    probe = CpuTemperature()
    try:
        messages.put(json.dumps({"temperature": value}) + "\n")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and probe.sample()[1] == "CPU 온도 준비 중":
            time.sleep(0.01)
        actual, warning = probe.sample()
        if value == 65.5:
            assert actual == 65.5 and not warning
            future = time.monotonic() + 10
            monkeypatch.setattr("monitor35.cpu_temperature.time.monotonic", lambda: future)
            assert probe.sample()[0] is None
        else:
            assert actual is None and warning
    finally:
        probe.close()
    assert process.stopped
    assert probe.sample()[0] is None
