"""User-controlled Windows login registration, independent of theme settings."""

import subprocess
import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Monitor35"


class Startup:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()

    def enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, VALUE_NAME)
            return True
        except FileNotFoundError:
            return False

    def set_enabled(self, enabled: bool):
        if enabled:
            executable = Path(sys.executable).with_name("pythonw.exe")
            if not executable.is_file():
                raise FileNotFoundError(f"실행 파일을 찾을 수 없습니다: {executable}")
            command = subprocess.list2cmdline(
                [
                    str(executable),
                    "-m",
                    "monitor35",
                    "--background",
                    "--connect",
                    "--data-dir",
                    str(self.data_dir),
                ]
            )
            if len(command) > 260:
                raise ValueError("시작프로그램 경로가 너무 깁니다. 더 짧은 설치 경로를 사용하세요.")
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                return  # Already unregistered, including removal in Windows settings.
