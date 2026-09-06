"""Bounded serial transport, reusing smartscreen-driver's Rev A encoding.

The upstream driver's timeout swallowing and in-place retry are deliberately
overridden: the session owns recovery of the whole display transaction.
"""

import time
from collections.abc import Callable

import serial
from PIL import Image
from serial.tools.list_ports import comports
from smartscreen_driver.lcd_comm import Orientation
from smartscreen_driver.lcd_comm_rev_a import Command, LcdCommRevA

SUPPORTED_IDS = {"USB35INCHIPS", "USB35INCHIPSV2"}


def devices() -> list[dict[str, str]]:
    return [
        {"port": p.device, "model": p.serial_number or "", "description": p.description}
        for p in comports()
        if p.serial_number in SUPPORTED_IDS
    ]


def detect_port() -> str:
    matches = devices()
    if len(matches) != 1:
        raise OSError(f"Turing 3.5 장치 {len(matches)}개 감지됨. 장치 한 대를 연결해 주세요.")
    return matches[0]["port"]


class BoundedRevA(LcdCommRevA):
    """Vendor adapter extension; no implicit retry or unbounded serial writes."""

    deadline = float("inf")

    def open_serial(self):
        self.lcd_serial = serial.Serial(
            self.com_port, 115200, timeout=0.3, write_timeout=1, rtscts=True
        )

    def serial_write(self, data: bytes):
        if time.monotonic() > self.deadline:
            raise serial.SerialTimeoutException("화면 전송 제한 시간(4초)을 초과했습니다.")
        if self.lcd_serial.write(data) != len(data):
            raise serial.SerialTimeoutException("화면 데이터가 일부만 전송되었습니다.")

    def write_line(self, line: bytes):
        self.serial_write(line)

    def read_data(self, size: int):
        return self.serial_read(size)


class TuringDisplay:
    def __init__(self, reset: bool, wait: Callable[[float], bool]):
        self.driver: BoundedRevA | None = None
        self.port = detect_port()
        try:
            self.driver = BoundedRevA(com_port=self.port)
            if reset:
                self.driver.send_command(Command.RESET, 0, 0, 0, 0)
                self.close()
                if wait(3):
                    raise OSError("연결이 취소되었습니다.")
                # A reset or Windows resume may change the COM number.
                self.port = detect_port()
                self.driver = BoundedRevA(com_port=self.port)
            self.driver.initialize_comm()
            self.driver.set_orientation(Orientation.LANDSCAPE)
            self.driver.screen_on()
        except Exception:
            self.close()
            raise

    def brightness(self, value: int) -> None:
        assert self.driver is not None
        self.driver.deadline = time.monotonic() + 4
        self.driver.set_brightness(value)

    def paint(self, image: Image.Image, pos: tuple[int, int] = (0, 0)) -> None:
        assert self.driver is not None
        self.driver.deadline = time.monotonic() + 4
        self.driver.paint(image, pos)

    def screen_off(self) -> None:
        assert self.driver is not None
        self.driver.deadline = time.monotonic() + 1
        self.driver.screen_off()

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close_serial()
            self.driver = None
