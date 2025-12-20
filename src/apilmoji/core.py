import asyncio
from pathlib import Path

from PIL import Image, ImageDraw
from PIL.ImageFont import ImageFont, FreeTypeFont, TransposedFont

from .helper import NodeType, parse_lines, contains_emoji
from .source import EmojiCDNSource

PILImage = Image.Image
PILDraw = ImageDraw.ImageDraw
FontT = ImageFont | FreeTypeFont | TransposedFont
ColorT = int | str | tuple[int, int, int] | tuple[int, int, int, int]


async def text(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[str] | str,
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    source: EmojiCDNSource | None = None,
) -> None:
    """Text rendering method with Unicode emoji support.

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
    source: EmojiCDNSource | None
        The emoji source to use, defaults to EmojiCDNSource()
    """
    if not lines:
        return

    x, y = xy
    draw = ImageDraw.Draw(image)
    line_height = line_height or get_font_height(font)
    source = source or EmojiCDNSource()

    if isinstance(lines, str):
        lines = lines.splitlines()

    # Check if lines has emoji
    if not contains_emoji(lines):
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        return

    # Parse lines into nodes
    nodes_lst = parse_lines(lines)

    emj_set: set[str] = set()
    for nodes in nodes_lst:
        for node in nodes:
            if node.type is NodeType.EMOJI:
                emj_set.add(node.content)

    # Download all emojis concurrently using source
    emj_map = await source.fetch_emojis(emj_set, set())

    # Render each line
    font_size = get_font_size(font)
    y_diff = int((line_height - font_size) / 2)

    # Pre-resize emojis
    resize_tasks = [
        _aresize_emoji(emoji, path, font_size)
        for emoji, path in emj_map.items()
        if path is not None
    ]
    resize_results = await asyncio.gather(*resize_tasks)
    resized_emj_map = dict(resize_results)

    for line in nodes_lst:
        cur_x = x

        for node in line:
            content = node.content
            if node.type is NodeType.EMOJI:
                if emj_img := resized_emj_map.get(content):
                    image.paste(emj_img, (cur_x + 1, y + y_diff), emj_img)
                else:
                    # 忽略组合表情的修饰符，只渲染第一个字符
                    draw.text((cur_x, y), content[0], font=font, fill=fill)
                cur_x += int(font_size)
            else:
                draw.text((cur_x, y), content, font=font, fill=fill)
                cur_x += int(font.getlength(content))

        y += line_height


async def text_with_discord(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[str] | str,
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    source: EmojiCDNSource | None = None,
) -> None:
    """Text rendering method with Unicode and Discord emoji support.

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
    source: EmojiCDNSource | None
        The emoji source to use, defaults to EmojiCDNSource()
    """
    from . import ds

    if not lines:
        return

    x, y = xy
    draw = ImageDraw.Draw(image)
    line_height = line_height or get_font_height(font)
    source = source or EmojiCDNSource()

    if isinstance(lines, str):
        lines = lines.splitlines()

    # Check if lines has emoji
    if not ds.contains_emoji(lines):
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        return

    # Parse lines into nodes
    nodes_lst = ds.parse_lines(lines)

    emj_set: set[str] = set()
    ds_emj_set: set[str] = set()
    for nodes in nodes_lst:
        for node in nodes:
            if node.type is NodeType.EMOJI:
                emj_set.add(node.content)
            elif node.type is NodeType.DSEMOJI:
                ds_emj_set.add(node.content)

    # Download all emojis concurrently using source
    emj_map = await source.fetch_emojis(
        emj_set,
        ds_emj_set,
    )

    # Render each line
    font_size = get_font_size(font)
    y_diff = int((line_height - font_size) / 2)

    # Pre-resize emojis
    resize_tasks = [
        _aresize_emoji(emoji, path, font_size)
        for emoji, path in emj_map.items()
        if path is not None
    ]
    resize_results = await asyncio.gather(*resize_tasks)
    resized_emj_map = dict(resize_results)

    for line in nodes_lst:
        cur_x = x

        for node in line:
            content = node.content
            if node.type is NodeType.EMOJI or node.type is NodeType.DSEMOJI:
                if emj_img := resized_emj_map.get(content):
                    image.paste(emj_img, (cur_x + 1, y + y_diff), emj_img)
                else:
                    # 忽略组合表情的修饰符，只渲染第一个字符
                    draw.text((cur_x, y), content[0], font=font, fill=fill)
                cur_x += int(font_size)
            else:
                draw.text((cur_x, y), content, font=font, fill=fill)
                cur_x += int(font.getlength(content))
        y += line_height


def get_font_size(font: FontT) -> float:
    match font:
        case FreeTypeFont():
            return font.size
        case TransposedFont():
            return get_font_size(font.font)
        case ImageFont():
            raise ValueError("Not support ImageFont")


def get_font_height(font: FontT) -> int:
    match font:
        case FreeTypeFont():
            ascent, descent = font.getmetrics()
            return ascent + descent
        case TransposedFont():
            return get_font_height(font.font)
        case ImageFont():
            raise ValueError("Not support ImageFont")


async def _aresize_emoji(
    emoji: str, path: Path, size: float
) -> tuple[str, PILImage | None]:
    def resize_emoji() -> PILImage:
        with Image.open(path).convert("RGBA") as emoji_img:
            emoji_size = int(size) - 2
            aspect_ratio = emoji_img.height / emoji_img.width
            return emoji_img.resize(
                (emoji_size, int(emoji_size * aspect_ratio)),
                Image.Resampling.LANCZOS,
            )

    try:
        img = await asyncio.to_thread(resize_emoji)
        return emoji, img
    except Exception:
        path.unlink(True)
        return emoji, None
