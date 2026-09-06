"""Receive Windows suspend/resume broadcasts on the existing desktop window."""

import ctypes
import logging
import sys
from collections.abc import Callable
from ctypes import wintypes

logger = logging.getLogger(__name__)
WM_POWERBROADCAST = 0x0218
SUSPEND_EVENT = 0x0004
# RESUMESUSPEND (0x7) follows RESUMEAUTOMATIC on interactive wake. Handling both
# would perform a second reset for the same wake cycle.
RESUME_EVENTS = (0x0006, 0x0012)
GWLP_WNDPROC = -4


class PowerListener:
    def __init__(self, window_id: int, suspended: Callable[[], None], resumed: Callable[[], None]):
        self.old_proc = None
        if sys.platform != "win32":
            return
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetParent.argtypes = [wintypes.HWND]
        self.user32.GetParent.restype = wintypes.HWND
        self.hwnd = self.user32.GetParent(window_id) or window_id
        self.user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        self.user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        self.user32.CallWindowProcW.argtypes = [
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self.user32.CallWindowProcW.restype = ctypes.c_ssize_t
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        def callback(hwnd, message, wparam, lparam):
            if message == WM_POWERBROADCAST and wparam == SUSPEND_EVENT:
                logger.info("windows_suspend_received")
                suspended()
                return 1
            if message == WM_POWERBROADCAST and wparam in RESUME_EVENTS:
                logger.info("windows_resume_received")
                resumed()
                return 1
            return self.user32.CallWindowProcW(self.old_proc, hwnd, message, wparam, lparam)

        self.callback = callback_type(callback)
        self.old_proc = self.user32.SetWindowLongPtrW(self.hwnd, GWLP_WNDPROC, self.callback)
        if not self.old_proc:
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self.old_proc:
            self.user32.SetWindowLongPtrW(self.hwnd, GWLP_WNDPROC, self.old_proc)
            self.old_proc = None
