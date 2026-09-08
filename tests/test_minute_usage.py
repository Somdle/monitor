import pytest

from monitor35.sensors import Point, Telemetry


def test_rolling_usage_clips_boundary_and_omits_missing_intervals():
    data = Telemetry(
        at=100,
        history=(
            Point(40, 0, 0, 999, 999, 999, 999, interval_seconds=2),
            Point(41, 0, 0, 10, 20, 30, 40, interval_seconds=2),
            Point(44, 0, 0, 10, 20, None, 40, interval_seconds=3),
            Point(100, 0, 0, None, None, None, None),
        ),
    )
    assert data.minute_bytes("read") == 40
    assert data.minute_bytes("write") == 80
    assert data.minute_bytes("receive") == 30
    assert data.minute_bytes("send") == 160


@pytest.mark.parametrize("rate, expected", [(None, None), (0, 0), (123.5, 247)])
def test_initial_and_idle_usage_are_distinct(rate, expected):
    data = Telemetry(at=2, history=(Point(2, 0, 0, rate, 0, 0, 0, interval_seconds=2),))
    assert data.minute_bytes("read") == expected
    assert Telemetry().minute_bytes("read") is None
