import asyncio
from pathlib import Path

from PIL import Image, ImageDraw

from . import helper
from .helper import FontT, NodeType
from .source import EmojiCDNSource

PILImage = Image.Image
PILDraw = ImageDraw.ImageDraw
ColorT = int | str | tuple[int, int, int] | tuple[int, int, int, int]


def _resize_emoji(emoji_path: Path, size: float) -> PILImage:
    """Resize emoji to fit the font size"""

    with Image.open(emoji_path).convert("RGBA") as emoji_img:
        emoji_size = int(size) - 2
        aspect_ratio = emoji_img.height / emoji_img.width
        return emoji_img.resize(
            (emoji_size, int(emoji_size * aspect_ratio)),
            Image.Resampling.LANCZOS,
        )


async def _aresize_emoji(
    emoji: str, path: Path, size: float
) -> tuple[str, PILImage | None]:
    try:
        # 在线程中执行 CPU 密集型操作
        img = await asyncio.to_thread(_resize_emoji, path, size)
        return emoji, img
    except Exception:
        path.unlink(True)
        return emoji, None


async def text(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[str] | str,
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    support_ds_emj: bool = False,
    source: EmojiCDNSource | None = None,
) -> None:
    """Text rendering method with Unicode and optional Discord emoji support.

    Parameters
    ----------
    image: PILImage
        The image to render onto
    xy: tuple[int, int]
        Rendering position (x, y)
    lines: list[str]
        The text lines to render
    font: FontT
        The font to use
    fill: ColorT | None
        Text color, defaults to black
    line_height: int | None
        Line height, defaults to font height
    support_ds_emj: bool
        Whether to support Discord emoji parsing, defaults to False
    source: EmojiCDNSource | None
        The emoji source to use, defaults to EmojiCDNSource()
    """
    if not lines:
        return

    x, y = xy
    draw = ImageDraw.Draw(image)
    line_height = line_height or helper.get_font_height(font)
    source = source or EmojiCDNSource()

    if isinstance(lines, str):
        lines = lines.splitlines()

    # Check if lines has emoji
    if not helper.contains_emoji(lines, support_ds_emj):
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        return

    # Parse lines into nodes
    nodes_lst = helper.parse_lines(lines, support_ds_emj)

    emj_set: set[str] = set()
    ds_emj_set: set[str] = set()
    for nodes in nodes_lst:
        for node in nodes:
            if node.type is NodeType.EMOJI:
                emj_set.add(node.content)
            elif node.type is NodeType.DISCORD_EMOJI:
                ds_emj_set.add(node.content)

    # Download all emojis concurrently using source
    emj_map = await source.fetch_emojis(
        emj_set,
        ds_emj_set,
    )

    # Render each line
    font_size = helper.get_font_size(font)
    y_diff = int((line_height - font_size) / 2)

    # Pre-resize emojis
    resize_tasks = [
        _aresize_emoji(emoji, path, font_size)
        for emoji, path in emj_map.items()
        if path is not None
    ]
    resize_results = await asyncio.gather(*resize_tasks)
    resized_emjs = {emoji: img for emoji, img in resize_results if img is not None}

    for line in nodes_lst:
        cur_x = x

        for node in line:
            if node.type is NodeType.EMOJI or node.type is NodeType.DISCORD_EMOJI:
                emj_img = resized_emjs.get(node.content)
            else:
                emj_img = None

            # Render emoji or text
            if emj_img is not None:
                image.paste(emj_img, (cur_x + 1, y + y_diff), emj_img)
                cur_x += int(font_size)
            else:
                draw.text((cur_x, y), node.content, font=font, fill=fill)
                cur_x += int(font.getlength(node.content))

        y += line_height
