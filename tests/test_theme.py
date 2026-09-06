import json
from dataclasses import replace

import pytest

from monitor35.render import render
from monitor35.sensors import Telemetry
from monitor35.theme import Widget, default_theme, load_theme, save_theme


def test_save_load_roundtrip_and_atomic_replacement(tmp_path):
    path = tmp_path / "theme.json"
    theme = default_theme()
    save_theme(path, theme)
    updated = replace(theme, brightness=40)
    save_theme(path, updated)
    assert load_theme(path) == updated
    assert not path.with_suffix(".writing").exists()


@pytest.mark.parametrize(
    "change",
    [
        dict(x=-1),
        dict(y=229),
        dict(size=100),
        dict(color="red"),
        dict(metric="unknown"),
        dict(x=True),
    ],
)
def test_invalid_widget_rejected(change):
    with pytest.raises(ValueError):
        replace(Widget("cpu", 10, 10), **change)


def test_invalid_file_is_not_overwritten(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text('{"version": 99}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_theme(path)
    assert json.loads(path.read_text()) == {"version": 99}


def test_preview_renders_changes_and_stays_inside_display():
    theme = default_theme()
    values = Telemetry(cpu=10, memory_percent=22)
    original = render(theme, values)
    widgets = list(theme.widgets)
    widgets[0] = replace(widgets[0], x=80, color="#ff0000")
    changed = render(replace(theme, widgets=tuple(widgets)), values)
    assert original.size == changed.size == (480, 320)
    assert original.tobytes() != changed.tobytes()


def test_preview_stays_upright_and_rotation_persists(tmp_path):
    theme = default_theme()
    values = Telemetry(cpu=42)
    rotated = replace(theme, rotate_180=True)
    assert render(rotated, values).tobytes() == render(theme, values).tobytes()
    path = tmp_path / "theme.json"
    save_theme(path, rotated)
    assert load_theme(path) == rotated


def test_existing_theme_without_optional_rotation_preserves_orientation(tmp_path):
    path = tmp_path / "theme.json"
    save_theme(path, default_theme())
    raw = json.loads(path.read_text())
    raw.pop("rotate_180")
    path.write_text(json.dumps(raw))
    assert load_theme(path) == default_theme()


def test_rotation_requires_boolean():
    with pytest.raises(ValueError):
        replace(default_theme(), rotate_180="true")


def test_v1_migration_preserves_device_settings_and_archives_original(tmp_path):
    path = tmp_path / "theme.json"
    raw = {
        "version": 1,
        "brightness": 37,
        "reset_on_connect": False,
        "rotate_180": True,
        "widgets": [
            {"metric": metric, "x": x, "y": y, "size": 30, "color": "#ffffff"}
            for metric, x, y in (
                ("cpu", 28, 74),
                ("memory", 262, 74),
                ("disk", 28, 194),
                ("clock", 262, 194),
            )
        ],
    }
    original = json.dumps(raw).encode()
    path.write_bytes(original)
    migrated = load_theme(path)
    assert migrated.version == 2
    assert (migrated.brightness, migrated.reset_on_connect, migrated.rotate_180) == (
        37,
        False,
        True,
    )
    assert {w.metric for w in migrated.widgets} == {"cpu", "memory", "disk", "network"}
    assert path.read_bytes() == original
    save_theme(path, migrated)
    assert path.with_suffix(".v1.json").read_bytes() == original
    assert load_theme(path) == migrated
    save_theme(path, replace(migrated, network_interface="Ethernet"))
    assert load_theme(path).network_interface == "Ethernet"
    assert path.with_suffix(".v1.json").read_bytes() == original


def test_save_does_not_overwrite_invalid_existing_theme(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text("broken", encoding="utf-8")
    with pytest.raises(ValueError):
        save_theme(path, default_theme())
    assert path.read_text() == "broken"
