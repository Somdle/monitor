"""Shared Monitor35 artwork, drawn at high resolution for Windows DPI scaling."""

from PIL import Image, ImageDraw


def app_icon(size: int = 64) -> Image.Image:
    image = Image.new("RGBA", (256, 256))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=54, fill="#122539")
    draw.rounded_rectangle((36, 48, 220, 184), radius=20, fill="#42d3ed")
    draw.rounded_rectangle((52, 64, 204, 168), radius=8, fill="#122539")
    draw.line(
        (65, 126, 91, 126, 110, 91, 137, 145, 157, 111, 191, 111),
        fill="#ffffff",
        width=12,
        joint="curve",
    )
    draw.rounded_rectangle((116, 179, 140, 211), radius=4, fill="#42d3ed")
    draw.rounded_rectangle((88, 207, 168, 221), radius=7, fill="#42d3ed")
    return image.resize((size, size), Image.Resampling.LANCZOS)
