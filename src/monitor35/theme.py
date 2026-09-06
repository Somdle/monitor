"""Validated, immutable layout model; the only owner of the saved theme format."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

WIDTH, HEIGHT = 480, 320
METRICS = ("cpu", "memory", "disk", "clock")


@dataclass(frozen=True)
class Widget:
    metric: str
    x: int
    y: int
    size: int = 30
    color: str = "#e5edf7"

    def __post_init__(self):
        if self.metric not in METRICS:
            raise ValueError("지원하지 않는 표시 항목입니다.")
        if any(type(value) is not int for value in (self.x, self.y, self.size)):
            raise ValueError("위치와 글자 크기는 정수여야 합니다.")
        if not (0 <= self.x <= WIDTH - 150 and 0 <= self.y <= HEIGHT - 92):
            raise ValueError("항목 위치가 화면 범위를 벗어났습니다.")
        if not 16 <= self.size <= 42:
            raise ValueError("글자 크기는 16~42 사이여야 합니다.")
        if not isinstance(self.color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", self.color):
            raise ValueError("색상은 #RRGGBB 형식이어야 합니다.")


@dataclass(frozen=True)
class Theme:
    widgets: tuple[Widget, ...]
    brightness: int = 25
    reset_on_connect: bool = True
    version: int = 1
    rotate_180: bool = False

    def __post_init__(self):
        if type(self.version) is not int or self.version != 1:
            raise ValueError("지원하지 않는 테마 버전입니다.")
        if len(self.widgets) != len(METRICS) or {w.metric for w in self.widgets} != set(METRICS):
            raise ValueError("CPU, 메모리, 디스크, 시계를 각각 하나씩 배치해야 합니다.")
        if type(self.brightness) is not int or not 0 <= self.brightness <= 50:
            raise ValueError("밝기는 0~50 사이여야 합니다.")
        if type(self.reset_on_connect) is not bool:
            raise ValueError("재연결 시 초기화 설정은 참/거짓이어야 합니다.")
        if type(self.rotate_180) is not bool:
            raise ValueError("화면 180도 회전 설정은 참/거짓이어야 합니다.")


def default_theme() -> Theme:
    return Theme(
        (
            Widget("cpu", 28, 74, color="#58dcc0"),
            Widget("memory", 262, 74, color="#8caeff"),
            Widget("disk", 28, 194, color="#f4c578"),
            Widget("clock", 262, 194),
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
        or set(raw) - required - {"rotate_180"}
    ):
        raise ValueError("테마 파일의 필드 구성이 올바르지 않습니다.")
    if not isinstance(raw["widgets"], list):
        raise ValueError("테마 항목은 목록이어야 합니다.")
    try:
        return Theme(**{**raw, "widgets": tuple(Widget(**item) for item in raw["widgets"])})
    except TypeError as exc:
        raise ValueError("테마 항목의 필드 구성이 올바르지 않습니다.") from exc


def save_theme(path: Path, theme: Theme) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(".writing")
    staging.write_text(json.dumps(asdict(theme), indent=2) + "\n", encoding="utf-8")
    staging.replace(path)
