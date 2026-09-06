import ctypes
import gc
import threading
import tkinter as tk
from ctypes import wintypes
from types import SimpleNamespace

import pytest

from monitor35.app import MonitorApp
from monitor35.power import SUSPEND_EVENT, WM_POWERBROADCAST, PowerListener
from monitor35.theme import default_theme, load_theme


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
        app.undo()
        assert app.theme.network_interface == ""
        app.selection.current(2)
        app.select()
        assert str(app.size_input.cget("state")) == "disabled"
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
