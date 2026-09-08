import ctypes
import sys
import winreg
from contextlib import nullcontext
from ctypes import wintypes

import pytest

from monitor35.startup import RUN_KEY, VALUE_NAME, Startup


@pytest.fixture
def registry(monkeypatch):
    values = {"OtherApp": "untouched"}

    def open_key(hive, path, *args):
        assert hive == winreg.HKEY_CURRENT_USER and path == RUN_KEY
        return nullcontext(values)

    def query(key, name):
        if name not in key:
            raise FileNotFoundError(name)
        return key[name], winreg.REG_SZ

    def delete(key, name):
        if name not in key:
            raise FileNotFoundError(name)
        del key[name]

    monkeypatch.setattr(winreg, "OpenKey", open_key)
    monkeypatch.setattr(winreg, "CreateKeyEx", open_key)
    monkeypatch.setattr(winreg, "QueryValueEx", query)
    monkeypatch.setattr(winreg, "DeleteValue", delete)
    monkeypatch.setattr(winreg, "SetValueEx", lambda k, n, r, t, v: k.__setitem__(n, v))
    return values


def test_registration_quotes_paths_and_unregisters_only_own_value(tmp_path, registry, monkeypatch):
    folder = tmp_path / "설치 폴더"
    folder.mkdir()
    executable = folder / "pythonw.exe"
    executable.touch()
    monkeypatch.setattr(sys, "executable", str(folder / "python.exe"))
    data = tmp_path / "사용자 설정"
    startup = Startup(data)
    assert not startup.enabled()
    assert registry == {"OtherApp": "untouched"}
    startup.set_enabled(True)
    assert startup.enabled()
    # Parse using the Windows API, independent of the command builder.
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    count = ctypes.c_int()
    argv = shell.CommandLineToArgvW(registry[VALUE_NAME], ctypes.byref(count))
    try:
        assert list(argv[: count.value]) == [
            str(executable),
            "-m",
            "monitor35",
            "--background",
            "--connect",
            "--data-dir",
            str(data.resolve()),
        ]
    finally:
        kernel = ctypes.WinDLL("kernel32")
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree(argv)
    startup.set_enabled(False)
    startup.set_enabled(False)
    assert not startup.enabled()
    assert registry == {"OtherApp": "untouched"}


def test_registration_failure_preserves_existing_values(tmp_path, registry, monkeypatch):
    def denied(*args):
        raise PermissionError("access denied")

    monkeypatch.setattr(winreg, "SetValueEx", denied)
    with pytest.raises(PermissionError):
        Startup(tmp_path).set_enabled(True)
    assert registry == {"OtherApp": "untouched"}


def test_missing_executable_does_not_register(tmp_path, registry, monkeypatch):
    monkeypatch.setattr(sys, "executable", str(tmp_path / "missing" / "python.exe"))
    with pytest.raises(FileNotFoundError):
        Startup(tmp_path).set_enabled(True)
    assert registry == {"OtherApp": "untouched"}
