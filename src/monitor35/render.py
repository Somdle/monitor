"""Pillow rendering shared by desktop preview and the physical display."""

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from monitor35.theme import HEIGHT, WIDTH, Theme

LABELS = {"cpu": "CPU", "memory": "MEMORY", "disk": "DISK", "clock": "LOCAL TIME"}
BACKGROUND = "#101923"


@lru_cache(maxsize=32)
def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("segoeui.ttf", size)


def render(theme: Theme, values: dict[str, float | str]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((28, 19), "SYSTEM / 35", fill="#e5edf7", font=font(18))
    draw.text((331, 23), "LIVE MONITOR", fill="#7790a6", font=font(11))
    draw.line((28, 55, 452, 55), fill="#2b3a49")
    for widget in theme.widgets:
        x, y = widget.x, widget.y
        draw.text((x, y), LABELS[widget.metric], fill="#97a9bb", font=font(12))
        value = values.get(widget.metric)
        text = f"{value:.0f}%" if isinstance(value, (int, float)) else str(value or "—")
        draw.text((x, y + 18), text, fill=widget.color, font=font(widget.size))
        if isinstance(value, (int, float)):
            draw.rounded_rectangle((x, y + 73, x + 150, y + 78), radius=2, fill="#293746")
            length = round(150 * max(0, min(100, value)) / 100)
            if length:
                draw.rounded_rectangle((x, y + 73, x + length, y + 78), radius=2, fill=widget.color)
    return image
