from dataclasses import replace

from monitor35.render import render
from monitor35.sensors import Point, Telemetry
from monitor35.theme import default_theme


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
