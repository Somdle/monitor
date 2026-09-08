"""Upright Task Manager style cards shared by preview and device output."""

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from monitor35.sensors import HISTORY_SECONDS, Telemetry
from monitor35.theme import CARD_HEIGHT, CARD_WIDTH, HEIGHT, WIDTH, Theme

BACKGROUND = "#191919"
CARD = "#242424"
GRID = "#3b3b3b"
TEXT = "#f2f2f2"
MUTED = "#b9b9b9"
SECONDARY = "#e5e5e5"
CHART_BOX = (10, 84, 219, 132)
BYTES_PER_MB = 1_000_000
LABELS = {"cpu": "CPU / GPU", "memory": "Memory", "disk": "Disk I/O", "network": "Network"}


@lru_cache(maxsize=32)
def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("malgun.ttf", size)


def format_speed(value: float | None) -> str:
    if value is None:
        return "-- MB/s"
    amount = value / BYTES_PER_MB
    precision = 2 if amount < 100 else 1 if amount < 1000 else 0
    return f"{amount:.{precision}f} MB/s"


def fit_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    width: int,
    size: int = 11,
    fill: str = MUTED,
) -> None:
    original = text
    while text and draw.textlength(text, font=font(size)) > width:
        original = original[:-1]
        text = original + "…"
    draw.text(xy, text, fill=fill, font=font(size))


def chart(
    draw: ImageDraw.ImageDraw,
    data: Telemetry,
    keys: tuple[str, ...],
    box: tuple[int, int, int, int],
    color: str,
    percent: bool = False,
) -> None:
    x0, y0, x1, y1 = box
    series = [[(point.at, getattr(point, key)) for point in data.history] for key in keys]
    maximum = (
        100.0
        if percent
        else max(
            [1024.0, *(value for points in series for _, value in points if value is not None)]
        )
    )
    if not percent:
        divisor = BYTES_PER_MB
        maximum = divisor * 2 ** math.ceil(math.log2(max(1, maximum / divisor)))
    draw.rectangle(box, outline=GRID)
    for step in range(1, 4):
        x = x0 + (x1 - x0) * step // 4
        y = y0 + (y1 - y0) * step // 4
        draw.line((x, y0, x, y1), fill=GRID)
        draw.line((x0, y, x1, y), fill=GRID)
    for index, points in enumerate(series):
        previous = None
        for at, value in points:
            if value is None or at < data.at - HISTORY_SECONDS:
                previous = None
                continue
            x = x1 - round((data.at - at) / HISTORY_SECONDS * (x1 - x0))
            y = y1 - round(min(1, max(0, value / maximum)) * (y1 - y0))
            if previous is not None:
                draw.line((*previous, x, y), fill=color if index == 0 else SECONDARY, width=2)
            else:
                draw.point((x, y), fill=color if index == 0 else SECONDARY)
            previous = (x, y)
    draw.text((x0, y1 + 1), "60 s", font=font(9), fill=MUTED)
    scale = "100%" if percent else format_speed(maximum)
    draw.text((x1, y1 + 1), scale, anchor="ra", font=font(9), fill=MUTED)


def render(theme: Theme, data: Telemetry) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    for widget in theme.widgets:
        # Rendering into a card clips custom font sizes and long adapter names.
        card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), CARD)
        draw = ImageDraw.Draw(card)
        color = widget.color
        draw.line((0, 0, 0, CARD_HEIGHT - 1), fill=color, width=2)
        draw.text((10, 4), LABELS[widget.metric], fill=TEXT, font=font(14))
        metric = widget.metric
        keys: tuple[str, ...]
        if metric == "cpu":
            keys = ("cpu", "gpu")
            for x, label, value, temperature, ink in (
                (10, "CPU", data.cpu, data.cpu_temperature, color),
                (118, "GPU", data.gpu.percent, data.gpu.temperature, SECONDARY),
            ):
                draw.text((x, 24), label, font=font(11), fill=ink, anchor="lt")
                draw.text(
                    (x, 39),
                    f"{value:.0f}%" if value is not None else "--",
                    font=font(widget.size),
                    fill=ink,
                    anchor="lt",
                )
                detail = f"{temperature:.0f}°C" if temperature is not None else "--°C"
                draw.text((x, 62), detail, font=font(22), fill=ink, anchor="lt")
        elif metric == "memory":
            keys = ("memory",)
            percent = f"{data.memory_percent:.0f}%" if data.memory_percent is not None else "--"
            draw.text((10, 24), "Utilization", font=font(11), fill=color, anchor="lt")
            draw.text((10, 39), percent, font=font(widget.size), fill=color, anchor="lt")
            divisor = 1024**3 if data.memory_total < 1024**4 else 1024**4
            unit = "GiB" if divisor == 1024**3 else "TiB"
            precision = 1 if data.memory_total / divisor < 100 else 0
            capacity = (
                f"{data.memory_used / divisor:.{precision}f} / "
                f"{data.memory_total / divisor:.{precision}f} {unit} in use"
                if data.memory_percent is not None
                else "Capacity --"
            )
            fit_text(draw, (10, 65), capacity, 209, size=11)
        else:
            disk = metric == "disk"
            if disk:
                draw.text((219, 7), "All disks", anchor="ra", font=font(11), fill=MUTED)
            else:
                fit_text(draw, (90, 7), data.interface or "Disconnected", 129, size=10)
            keys = ("read", "write") if disk else ("receive", "send")
            labels = ("R · Read", "W · Write") if disk else ("↓ Receive", "↑ Send")
            for x, key, label, ink in zip((10, 118), keys, labels, (color, SECONDARY), strict=True):
                speed = format_speed(getattr(data, key))
                number, _, unit = speed.partition(" ")
                draw.text(
                    (x, 24),
                    label,
                    font=font(11),
                    fill=ink,
                    anchor="lt",
                )
                draw.text((x, 39), number, font=font(widget.size), fill=ink, anchor="lt")
                draw.text((x, 67), unit, font=font(11), fill=MUTED, anchor="lt")
        chart(
            draw,
            data,
            keys,
            CHART_BOX,
            color,
            percent=metric in ("cpu", "memory"),
        )
        image.paste(card, (widget.x, widget.y))
    return image
