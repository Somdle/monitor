"""Isolated LibreHardwareMonitor CPU probe with stale-data rejection."""

import json
import math
import os
import subprocess
import sys
import threading
import time
import winreg
from pathlib import Path


class CpuTemperature:
    def __init__(self):
        self.lock = threading.Lock()
        self.value: float | None = None
        self.updated = 0.0
        self.process: subprocess.Popen[str] | None = None
        self.reader: threading.Thread | None = None
        self.warning = "CPU 온도 준비 중"
        library = Path(sys.prefix) / "hardware/LibreHardwareMonitor/LibreHardwareMonitorLib.dll"
        if not library.exists():
            self.warning = "CPU 온도: LibreHardwareMonitor 센서 라이브러리를 준비해 주세요."
            return
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PawnIO",
            ):
                pass
        except OSError:
            self.warning = "CPU 온도: PawnIO 드라이버 설치가 필요합니다."
            return
        powershell = (
            Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        try:
            self.process = subprocess.Popen(
                [
                    str(powershell),
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(Path(__file__).with_suffix(".ps1")),
                    "-LibraryPath",
                    str(library),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self.reader = threading.Thread(target=self._read, name="cpu-temperature", daemon=True)
            self.reader.start()
        except OSError:
            self.warning = "CPU 온도 센서 프로세스를 실행하지 못했습니다."

    def _read(self):
        assert self.process is not None and self.process.stdout is not None
        try:
            for line in self.process.stdout:
                try:
                    raw = json.loads(line)
                    value = raw["temperature"]
                    if value is not None and (
                        type(value) not in (int, float)
                        or not math.isfinite(value)
                        or not -30 <= value <= 150
                    ):
                        raise ValueError("Invalid CPU temperature")
                    warning = (
                        ""
                        if value is not None
                        else "CPU 온도 읽기 실패 · 관리자 권한을 확인해 주세요."
                    )
                except (ValueError, KeyError, TypeError):
                    value = None
                    warning = "CPU 온도 센서 응답이 올바르지 않습니다."
                with self.lock:
                    self.value, self.warning, self.updated = value, warning, time.monotonic()
        except (OSError, UnicodeError):
            with self.lock:
                self.warning = "CPU 온도 센서 연결을 읽지 못했습니다."
        with self.lock:
            self.value = None
            self.warning = "CPU 온도 센서가 종료되었습니다. 앱을 다시 실행해 주세요."

    def sample(self) -> tuple[float | None, str]:
        with self.lock:
            if self.value is not None and time.monotonic() - self.updated > 5:
                return None, "CPU 온도 센서 갱신이 중단되었습니다."
            return self.value, self.warning

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=1)
            if self.reader is not None:
                self.reader.join(timeout=1)
            if self.process.stdout is not None:
                self.process.stdout.close()
