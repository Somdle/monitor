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
    number = f"{value:.1f}" if index else f"{value:.0f}"
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
        # Rendering into a card clips custom font sizes and long adapter/volume names.
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
                detail = (
                    f"{data.memory_used / 1024**3:.1f} / "
                    f"{data.memory_total / 1024**3:.1f} GiB in use"
                )
            else:
                detail = "Utilization · all logical processors"
            fit_text(draw, (10, 128), detail if value is not None else "Waiting for sensors…", 210)
        elif metric == "disk":
            pages = max(1, math.ceil(len(data.volumes) / 2))
            page = int(data.at // 6) % pages
            draw.text(
                (219, 7), f"All disks · {page + 1}/{pages}", anchor="ra", font=font(10), fill=MUTED
            )
            fit_text(draw, (10, 26), "R " + quantity(data.read, True), 103, fill=color)
            fit_text(draw, (118, 26), "W " + quantity(data.write, True), 103, fill=SECONDARY)
            chart(draw, data, ("read", "write"), (10, 44, 219, 83), color)
            visible = data.volumes[page * 2 : page * 2 + 2]
            if not visible:
                draw.text((10, 111), "No mounted local volumes", font=font(11), fill=MUTED)
            for index, volume in enumerate(visible):
                y = 103 + index * 23
                detail = "unavailable"
                fraction = 0.0
                if volume.total and volume.used is not None:
                    fraction = min(1, volume.used / volume.total)
                    detail = (
                        f"{volume.used / 1024**3:.0f}/{volume.total / 1024**3:.0f} GiB"
                        f"  {fraction:.0%}"
                    )
                fit_text(draw, (10, y), f"{volume.name}  {detail}", 209, fill=TEXT)
                draw.rectangle((10, y + 17, 219, y + 19), fill=GRID)
                if fraction:
                    draw.rectangle((10, y + 17, 10 + round(209 * fraction), y + 19), fill=color)
        else:
            fit_text(draw, (90, 7), data.interface or "Disconnected", 129, size=10)
            fit_text(draw, (10, 26), "↓ " + quantity(data.receive, True), 103, fill=color)
            fit_text(draw, (118, 26), "↑ " + quantity(data.send, True), 103, fill=SECONDARY)
            chart(draw, data, ("receive", "send"), (10, 44, 219, 92), color)
            draw.text((10, 109), "Measured since app / adapter start", font=font(10), fill=MUTED)
            fit_text(draw, (10, 128), "↓ " + quantity(data.received_total), 103, fill=color)
            fit_text(draw, (118, 128), "↑ " + quantity(data.sent_total), 103, fill=SECONDARY)
        image.paste(card, (widget.x, widget.y))
    return image
