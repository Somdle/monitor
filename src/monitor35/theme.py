"""Validated, immutable layout model; the only owner of the saved theme format."""

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

WIDTH, HEIGHT = 480, 320
CARD_WIDTH, CARD_HEIGHT = 230, 150
METRICS = ("cpu", "memory", "disk", "network")


@dataclass(frozen=True)
class Widget:
    metric: str
    x: int
    y: int
    size: int = 24
    color: str = "#55b6e8"

    def __post_init__(self):
        if self.metric not in METRICS:
            raise ValueError("지원하지 않는 표시 항목입니다.")
        if any(type(value) is not int for value in (self.x, self.y, self.size)):
            raise ValueError("위치와 글자 크기는 정수여야 합니다.")
        if not (0 <= self.x <= WIDTH - CARD_WIDTH and 0 <= self.y <= HEIGHT - CARD_HEIGHT):
            raise ValueError("항목 위치가 화면 범위를 벗어났습니다.")
        if not 16 <= self.size <= 28:
            raise ValueError("글자 크기는 16~28 사이여야 합니다.")
        if not isinstance(self.color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", self.color):
            raise ValueError("색상은 #RRGGBB 형식이어야 합니다.")


@dataclass(frozen=True)
class Theme:
    widgets: tuple[Widget, ...]
    brightness: int = 25
    reset_on_connect: bool = True
    version: int = 2
    rotate_180: bool = False
    network_interface: str = ""

    def __post_init__(self):
        if type(self.version) is not int or self.version != 2:
            raise ValueError("지원하지 않는 테마 버전입니다.")
        if len(self.widgets) != len(METRICS) or {w.metric for w in self.widgets} != set(METRICS):
            raise ValueError("CPU, 메모리, 디스크, 네트워크를 각각 하나씩 배치해야 합니다.")
        if type(self.brightness) is not int or not 0 <= self.brightness <= 50:
            raise ValueError("밝기는 0~50 사이여야 합니다.")
        if type(self.reset_on_connect) is not bool:
            raise ValueError("재연결 시 초기화 설정은 참/거짓이어야 합니다.")
        if type(self.rotate_180) is not bool:
            raise ValueError("화면 180도 회전 설정은 참/거짓이어야 합니다.")
        if not isinstance(self.network_interface, str) or len(self.network_interface) > 256:
            raise ValueError("네트워크 어댑터 이름이 올바르지 않습니다.")


def default_theme() -> Theme:
    return Theme(
        (
            Widget("cpu", 6, 6, color="#55b6e8"),
            Widget("memory", 244, 6, color="#bd8de0"),
            Widget("disk", 6, 164, color="#8cc66a"),
            Widget("network", 244, 164, color="#e2a65e"),
        )
    )


def load_theme(path: Path) -> Theme:
    raw = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "version",
        "widgets",
        "brightness",
        "reset_on_connect",
    }
    if (
        not isinstance(raw, dict)
        or not required <= set(raw)
        or set(raw) - required - {"rotate_180", "network_interface"}
    ):
        raise ValueError("테마 파일의 필드 구성이 올바르지 않습니다.")
    if not isinstance(raw["widgets"], list):
        raise ValueError("테마 항목은 목록이어야 합니다.")
    try:
        if type(raw["version"]) is int and raw["version"] == 1:
            return migrate_v1(raw)
        return Theme(**{**raw, "widgets": tuple(Widget(**item) for item in raw["widgets"])})
    except TypeError as exc:
        raise ValueError("테마 항목의 필드 구성이 올바르지 않습니다.") from exc


def migrate_v1(raw: dict) -> Theme:
    """One-way import into the four-card layout; no legacy rendering path remains."""
    if "network_interface" in raw:
        raise ValueError("이전 테마의 필드 구성이 올바르지 않습니다.")
    old = raw["widgets"]
    if len(old) != 4 or any(not isinstance(item, dict) for item in old):
        raise ValueError("이전 테마의 항목 구성이 올바르지 않습니다.")
    if {item.get("metric") for item in old} != {"cpu", "memory", "disk", "clock"}:
        raise ValueError("이전 테마의 항목 구성이 올바르지 않습니다.")
    for item in old:
        if set(item) != {"metric", "x", "y", "size", "color"}:
            raise ValueError("이전 테마의 필드 구성이 올바르지 않습니다.")
        if any(type(item[key]) is not int for key in ("x", "y", "size")) or not (
            0 <= item["x"] <= 330 and 0 <= item["y"] <= 228 and 16 <= item["size"] <= 42
        ):
            raise ValueError("이전 테마의 위치 또는 크기가 올바르지 않습니다.")
        if not isinstance(item["color"], str) or not re.fullmatch(
            r"#[0-9a-fA-F]{6}", item["color"]
        ):
            raise ValueError("이전 테마의 색상이 올바르지 않습니다.")
    return replace(
        default_theme(),
        brightness=raw["brightness"],
        reset_on_connect=raw["reset_on_connect"],
        rotate_180=raw.get("rotate_180", False),
    )


def save_theme(path: Path, theme: Theme) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        load_theme(path)  # Do not overwrite a corrupt or unsupported user file.
        previous = path.read_bytes()
        if json.loads(previous).get("version") == 1:
            backup = path.with_suffix(".v1.json")
            if not backup.exists():
                backup_staging = backup.with_suffix(".writing")
                backup_staging.write_bytes(previous)
                backup_staging.replace(backup)
    staging = path.with_suffix(".writing")
    staging.write_text(json.dumps(asdict(theme), indent=2) + "\n", encoding="utf-8")
    staging.replace(path)
