import ctypes
import gc
import subprocess
import sys
import threading
import time
import tkinter as tk
import uuid
from ctypes import wintypes
from types import SimpleNamespace

import pytest

from monitor35.app import MonitorApp
from monitor35.instance import SingleInstance
from monitor35.power import SUSPEND_EVENT, WM_POWERBROADCAST, PowerListener
from monitor35.theme import default_theme, load_theme


def pump_until(root, predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.02)
    assert predicate()


def test_second_process_restores_hidden_editor(tmp_path, desktop_root):
    name = "Local\\Monitor35.Test." + uuid.uuid4().hex
    instance = SingleInstance(name)
    root = tk.Toplevel(desktop_root)
    app = MonitorApp(
        root, default_theme(), tmp_path / "theme.json", background=True, instance=instance
    )
    try:
        pump_until(root, lambda: root.state() == "withdrawn")
        worker = app.worker
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from monitor35.instance import SingleInstance; "
                "import sys; s=SingleInstance(sys.argv[1]); assert not s.owner; s.close()",
                name,
            ],
            capture_output=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        assert result.returncode == 0, result.stderr
        pump_until(root, lambda: root.state() == "normal")
        assert app.worker is worker and worker.is_alive()
    finally:
        app.close()
        if root.winfo_exists():
            root.wait_window()
        instance.close()


def test_background_keeps_sampling_and_tray_restores_and_quits(tmp_path, desktop_root):
    root = tk.Toplevel(desktop_root)
    app = MonitorApp(root, default_theme(), tmp_path / "theme.json", background=True)
    try:
        pump_until(root, lambda: root.state() == "withdrawn" and app.values.at > 0)
        first = app.values.at
        pump_until(root, lambda: app.values.at > first)
        assert app.worker.is_alive()
        # Invoke the public tray menu from another thread, as Windows does.
        menu = list(app.tray.icon.menu)
        callback = threading.Thread(target=lambda: menu[0](app.tray.icon))
        callback.start()
        callback.join()
        pump_until(root, lambda: root.state() == "normal")
        app.fields["size"].set("28")
        app.apply_fields()
        app.hide()
        assert load_theme(tmp_path / "theme.json") == app.theme
        assert root.state() == "withdrawn"
        # Unexpected native tray shutdown must not leave an inaccessible app.
        app.tray.icon.stop()
        pump_until(root, lambda: root.state() == "normal")
        assert app.worker.is_alive()
        menu[1](app.tray.icon)
        pump_until(root, lambda: app.closing)
    finally:
        app.close()
        if root.winfo_exists():
            root.wait_window()
    assert not app.worker.is_alive()
    assert not app.tray.is_alive()


def test_background_save_failure_keeps_editor_accessible(tmp_path, desktop_root):
    root = tk.Toplevel(desktop_root)
    # A directory cannot be replaced by a saved theme file.
    app = MonitorApp(root, default_theme(), tmp_path)
    try:
        pump_until(root, app.tray.ready.is_set)
        app.fields["size"].set("28")
        app.apply_fields()
        app.hide()
        assert root.state() == "normal"
        assert "저장 실패" in app.notice.get()
        assert app.worker.is_alive()
    finally:
        app.theme_path = tmp_path / "theme.json"
        app.close()
        if root.winfo_exists():
            root.wait_window()


def test_tray_creation_failure_preserves_window(tmp_path, desktop_root, monkeypatch):
    import pystray

    def unavailable(*args, **kwargs):
        raise OSError("tray unavailable")

    monkeypatch.setattr(pystray, "Icon", unavailable)
    root = tk.Toplevel(desktop_root)
    app = MonitorApp(root, default_theme(), tmp_path / "theme.json", background=True)
    try:
        pump_until(root, lambda: not app.background_pending)
        app.hide()
        assert root.state() == "normal"
        assert "트레이" in app.notice.get()
        assert not app.closing
    finally:
        app.close()
        if root.winfo_exists():
            root.wait_window()


@pytest.fixture(autouse=True)
def collect_tk_objects_on_main_thread():
    yield
    # Tk variable/image finalizers must not be collected by a later worker thread.
    gc.collect()


@pytest.fixture(scope="module")
def desktop_root():
    # Like the application, use one Tcl interpreter with independently closed windows.
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_edit_invalid_input_undo_save_and_shutdown(tmp_path, desktop_root):
    root = tk.Toplevel(desktop_root)
    root.withdraw()
    original = default_theme()
    app = MonitorApp(root, original, tmp_path / "theme.json")
    try:
        app.fields["x"].set("-1")
        app.apply_fields()
        assert app.theme == original
        assert "입력을 확인" in app.notice.get()
        assert app.fields["x"].get() == "-1"
        app.fields["x"].set("50")
        app.apply_fields()
        assert app.theme.widgets[0].x == 50
        assert app.save()
        assert load_theme(tmp_path / "theme.json") == app.theme
        app.undo()
        assert app.theme == original
        app.reload()
        assert app.theme.widgets[0].x == 50
        outline = app.canvas.coords(app.outline)
        app.rotation_button.invoke()
        assert app.theme.rotate_180
        assert app.canvas.coords(app.outline) == outline
        # Physical rotation leaves editor hit testing and drag direction upright.
        app.begin_drag(SimpleNamespace(x=60, y=84))
        app.drag(SimpleNamespace(x=80, y=94))
        app.end_drag(None)
        assert (app.theme.widgets[0].x, app.theme.widgets[0].y) == (70, 16)
        app.undo()
        assert (app.theme.widgets[0].x, app.theme.widgets[0].y) == (50, 6)
        assert app.save()
        assert load_theme(tmp_path / "theme.json").rotate_180
        app.rotation_button.invoke()
        assert not app.theme.rotate_180
        app.reload()
        assert app.rotation.get()
        app.network.set("Ethernet")
        app.apply_network()
        assert app.theme.network_interface == "Ethernet"
        app.network.current(0)
        app.apply_network()
        assert app.theme.network_interface == ""
        assert app.save()
        assert load_theme(tmp_path / "theme.json").network_interface == ""
        app.undo()
        assert app.theme.network_interface == "Ethernet"
        app.undo()
        assert app.theme.network_interface == ""
        app.selection.current(2)
        app.select()
        app.fields["size"].set("28")
        app.apply_fields()
        assert app.theme.widgets[2].size == 28
    finally:
        app.close()
        if root.winfo_exists():
            root.wait_window()
    assert not app.worker.is_alive()


def test_native_resume_broadcast_reaches_callback(desktop_root):
    root = tk.Toplevel(desktop_root)
    root.withdraw()
    root.update_idletasks()
    received = threading.Event()
    suspended = threading.Event()
    listener = PowerListener(root.winfo_id(), suspended.set, received.set)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    try:
        user32.SendMessageW(listener.hwnd, WM_POWERBROADCAST, SUSPEND_EVENT, 0)
        assert suspended.is_set()
        assert not received.is_set()
        user32.SendMessageW(listener.hwnd, WM_POWERBROADCAST, 0x0012, 0)
        assert received.is_set()
        received.clear()
        user32.SendMessageW(listener.hwnd, WM_POWERBROADCAST, 0x0007, 0)
        assert not received.is_set()
    finally:
        listener.close()
        root.destroy()
