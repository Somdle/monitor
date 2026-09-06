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
LABELS = {"cpu": "CPU", "memory": "Memory", "disk": "Disk I/O", "network": "Network"}


@lru_cache(maxsize=32)
def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("malgun.ttf", size)


def quantity(value: float | None, rate: bool = False) -> str:
    if value is None:
        return "--"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    number = f"{value:.1f}" if index and value < 100 else f"{value:.0f}"
    return f"{number} {units[index]}" + ("/s" if rate else "")


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
        maximum = 2 ** math.ceil(math.log2(maximum))
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
    scale = "100%" if percent else quantity(maximum, rate=True)
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
        if metric in ("cpu", "memory"):
            value = data.cpu if metric == "cpu" else data.memory_percent
            draw.text(
                (CARD_WIDTH - 10, 0),
                f"{value:.0f}%" if value is not None else "--",
                fill=TEXT,
                font=font(widget.size),
                anchor="ra",
            )
            chart(draw, data, (metric,), (10, 33, 219, 106), color, percent=True)
            if metric == "memory":
                divisor = 1024**3 if data.memory_total < 1024**4 else 1024**4
                unit = "GiB" if divisor == 1024**3 else "TiB"
                precision = 1 if data.memory_total / divisor < 100 else 0
                amount = (
                    (
                        f"{data.memory_used / divisor:.{precision}f}/"
                        f"{data.memory_total / divisor:.{precision}f}"
                    )
                    if value is not None
                    else "--"
                )
                draw.text((10, 122), amount, font=font(widget.size), fill=TEXT, anchor="lt")
                draw.text((219, 136), unit, anchor="ra", font=font(11), fill=MUTED)
        else:
            disk = metric == "disk"
            if disk:
                draw.text((219, 7), "All disks", anchor="ra", font=font(11), fill=MUTED)
            else:
                fit_text(draw, (90, 7), data.interface or "Disconnected", 129, size=10)
            keys = ("read", "write") if disk else ("receive", "send")
            labels = ("R · Read", "W · Write") if disk else ("↓ Receive", "↑ Send")
            for x, key, label, ink in zip((10, 118), keys, labels, (color, SECONDARY), strict=True):
                draw.text((x, 24), label, font=font(11), fill=ink, anchor="lt")
                number, _, unit = quantity(getattr(data, key), rate=True).partition(" ")
                draw.text((x, 39), number, font=font(widget.size), fill=ink, anchor="lt")
                draw.text((x, 67), unit, font=font(11), fill=MUTED, anchor="lt")
            chart(draw, data, keys, (10, 84, 219, 132 if disk else 99), color)
            if not disk:
                for x, value, ink in (
                    (10, data.received_total, color),
                    (118, data.sent_total, SECONDARY),
                ):
                    number, _, unit = quantity(value).partition(" ")
                    draw.text((x, 114), number, font=font(widget.size), fill=ink, anchor="lt")
                    draw.text((x, 139), unit + " total", font=font(10), fill=MUTED, anchor="lt")
        image.paste(card, (widget.x, widget.y))
    return image
