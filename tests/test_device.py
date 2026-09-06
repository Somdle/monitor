import time

import pytest
import serial

from monitor35.device import BoundedRevA


class FakeSerial:
    def __init__(self, outcome):
        self.outcome = outcome

    def write(self, data):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    def close(self):
        return None


@pytest.mark.parametrize(
    "outcome", [2, serial.SerialTimeoutException("timeout"), serial.SerialException("unplugged")]
)
def test_transport_never_swallows_partial_write_or_timeout(outcome):
    driver = object.__new__(BoundedRevA)
    driver.lcd_serial = FakeSerial(outcome)
    driver.deadline = time.monotonic() + 4
    with pytest.raises(serial.SerialException):
        driver.write_line(b"1234")


def test_whole_frame_deadline_is_bounded():
    driver = object.__new__(BoundedRevA)
    driver.lcd_serial = FakeSerial(4)
    driver.deadline = time.monotonic() - 1
    with pytest.raises(serial.SerialTimeoutException):
        driver.write_line(b"1234")
