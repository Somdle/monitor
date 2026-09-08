"""Session-wide single instance and activation using Windows kernel objects."""

import ctypes
from ctypes import wintypes


class SingleInstance:
    def __init__(self, name: str = "Local\\Monitor35.Desktop.v1"):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.api.CreateMutexW.restype = wintypes.HANDLE
        self.api.CreateEventW.argtypes = [
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        self.api.CreateEventW.restype = wintypes.HANDLE
        self.api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.api.WaitForSingleObject.restype = wintypes.DWORD
        for method in ("SetEvent", "ReleaseMutex", "CloseHandle"):
            function = getattr(self.api, method)
            function.argtypes = [wintypes.HANDLE]
            function.restype = wintypes.BOOL
        self.event = None
        self.mutex = None
        self.owner = False
        try:
            # Create the event first so activation during startup is retained.
            self.event = self.api.CreateEventW(None, False, False, name + ".activate")
            if not self.event:
                raise ctypes.WinError(ctypes.get_last_error())
            self.mutex = self.api.CreateMutexW(None, False, name)
            if not self.mutex:
                raise ctypes.WinError(ctypes.get_last_error())
            result = self.api.WaitForSingleObject(self.mutex, 0)
            if result in (0, 0x80):  # Acquired, including a crashed previous owner.
                self.owner = True
            elif result == 0x102:
                if not self.api.SetEvent(self.event):
                    raise ctypes.WinError(ctypes.get_last_error())
            else:
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise

    def activation_requested(self) -> bool:
        result = self.api.WaitForSingleObject(self.event, 0)
        if result == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        return result == 0

    def close(self):
        if self.mutex:
            if self.owner:
                self.api.ReleaseMutex(self.mutex)
            self.api.CloseHandle(self.mutex)
            self.mutex = None
        if self.event:
            self.api.CloseHandle(self.event)
            self.event = None
