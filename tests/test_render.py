from dataclasses import replace

import pytest

from monitor35.gpu import GpuSample
from monitor35.render import format_speed, render
from monitor35.sensors import Point, Telemetry
from monitor35.theme import default_theme


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "-- MB/s"),
        (0, "0.00 MB/s"),
        (10000, "0.01 MB/s"),
        (1000000, "1.00 MB/s"),
        (100000000, "100.0 MB/s"),
        (1000000000, "1000 MB/s"),
        (10000000000, "10000 MB/s"),
    ],
)
def test_speed_always_uses_decimal_megabytes(value, expected):
    assert format_speed(value) == expected


def test_history_changes_chart_and_time_does_not_page_disk():
    theme = default_theme()
    data = Telemetry(at=60, cpu=50, memory_percent=40, read=1024, write=2048)
    plain = render(theme, data)
    history = tuple(Point(at, at, 40, 1024, 512, 2048, 1024) for at in range(61))
    graph = render(theme, replace(data, history=history))
    assert plain.crop((16, 39, 225, 112)).tobytes() != graph.crop((16, 39, 225, 112)).tobytes()
    assert plain.tobytes() == render(theme, replace(data, at=66)).tobytes()


def test_unavailable_and_long_names_stay_inside_cards():
    theme = default_theme()
    data = Telemetry(
        interface="Very long adapter name " * 50,
    )
    image = render(theme, data)
    assert image.size == (480, 320)
    assert image.crop((236, 0, 244, 320)).getcolors() == [(8 * 320, (25, 25, 25))]


def test_number_size_changes_disk_and_network_readouts():
    theme = default_theme()
    data = Telemetry(read=123 * 1024, write=456 * 1024, receive=123 * 1024, send=456 * 1024)
    normal = render(theme, data)
    large = render(replace(theme, widgets=tuple(replace(w, size=28) for w in theme.widgets)), data)
    for x in (6, 244):
        box = (x + 10, 164 + 39, x + 104, 164 + 65)
        assert normal.crop(box).tobytes() != large.crop(box).tobytes()


def test_all_four_charts_match_disk_size_and_stay_below_information():
    theme = default_theme()
    empty = render(theme, Telemetry())
    disk_chart = empty.crop((16, 248, 226, 297))
    assert disk_chart.getpixel((0, 0)) == (59, 59, 59)
    for widget in theme.widgets:
        box = (widget.x + 10, widget.y + 84, widget.x + 220, widget.y + 133)
        assert empty.crop(box).tobytes() == disk_chart.tobytes()
    populated = render(
        theme,
        Telemetry(
            cpu=50,
            cpu_temperature=65,
            gpu=GpuSample("RTX", 72, 62),
            memory_percent=40,
            memory_used=20 * 1024**3,
            memory_total=32 * 1024**3,
            read=1024,
            write=2048,
            receive=4096,
            send=8192,
            received_total=10**9,
            sent_total=10**8,
        ),
    )
    for widget in theme.widgets:
        top = (widget.x + 2, widget.y, widget.x + 230, widget.y + 84)
        bottom = (widget.x + 2, widget.y + 84, widget.x + 230, widget.y + 150)
        assert empty.crop(top).tobytes() != populated.crop(top).tobytes()
        assert empty.crop(bottom).tobytes() == populated.crop(bottom).tobytes()


def test_disk_and_network_use_identical_megabyte_scale():
    theme = default_theme()
    theme = replace(theme, widgets=tuple(replace(w, color="#ffffff") for w in theme.widgets))
    data = Telemetry(
        at=60,
        read=1000000,
        write=1000000000,
        receive=1000000,
        send=1000000000,
        history=(Point(60, 0, 0, 1000000, 1000000000, 1000000, 1000000000),),
    )
    frame = render(theme, data)
    for left, top, right, bottom in ((10, 39, 220, 150),):
        disk = frame.crop((6 + left, 164 + top, 6 + right, 164 + bottom))
        network = frame.crop((244 + left, 164 + top, 244 + right, 164 + bottom))
        assert disk.tobytes() == network.tobytes()


@pytest.mark.parametrize(
    "value, expected", [(None, "-- MB/s"), (1000000, "1.00 MB/s"), (1000000000, "1000 MB/s")]
)
def test_disk_speed_is_fixed_decimal_megabytes(value, expected):
    assert format_speed(value) == expected


def test_memory_primary_value_tracks_percent_and_capacity_is_secondary():
    theme = default_theme()
    data = Telemetry(memory_percent=50, memory_used=16 * 1024**3, memory_total=32 * 1024**3)
    original = render(theme, data)
    percent_changed = render(theme, replace(data, memory_percent=75))
    capacity_changed = render(theme, replace(data, memory_used=24 * 1024**3))
    primary = (254, 45, 463, 71)
    secondary = (254, 71, 463, 90)
    assert original.crop(primary).tobytes() != percent_changed.crop(primary).tobytes()
    assert original.crop(primary).tobytes() == capacity_changed.crop(primary).tobytes()
    assert original.crop(secondary).tobytes() != capacity_changed.crop(secondary).tobytes()
