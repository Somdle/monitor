from dataclasses import replace

from monitor35.render import render
from monitor35.sensors import Point, Telemetry, Volume
from monitor35.theme import default_theme


def test_history_changes_chart_and_volume_pages_cover_all_drives():
    theme = default_theme()
    data = Telemetry(
        at=60,
        cpu=50,
        memory_percent=40,
        volumes=tuple(Volume(name, 100, 500) for name in ("C:", "D:", "E:")),
    )
    plain = render(theme, data)
    history = tuple(Point(at, at, 40, 1024, 512, 2048, 1024) for at in range(61))
    graph = render(theme, replace(data, history=history))
    assert plain.crop((16, 39, 225, 112)).tobytes() != graph.crop((16, 39, 225, 112)).tobytes()
    page_two = render(theme, replace(data, at=66))
    # Only the disk card changes when paging; no CPU/memory or network contamination.
    assert plain.crop((6, 164, 236, 314)).tobytes() != page_two.crop((6, 164, 236, 314)).tobytes()
    assert plain.crop((0, 0, 480, 156)).tobytes() == page_two.crop((0, 0, 480, 156)).tobytes()
    assert (
        plain.crop((244, 164, 474, 314)).tobytes() == page_two.crop((244, 164, 474, 314)).tobytes()
    )


def test_unavailable_and_long_names_stay_inside_cards():
    theme = default_theme()
    data = Telemetry(
        interface="Very long adapter name " * 50,
        volumes=(Volume("Mounted volume " * 50, None, None),),
    )
    image = render(theme, data)
    assert image.size == (480, 320)
    assert image.crop((236, 0, 244, 320)).getcolors() == [(8 * 320, (25, 25, 25))]
