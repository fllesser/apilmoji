import re
from enum import Enum
from typing import Final, NamedTuple

import emoji
from PIL import ImageFont

FontT = ImageFont.FreeTypeFont | ImageFont.TransposedFont
ColorT = int | tuple[int, int, int] | tuple[int, int, int, int] | str

language_pack: dict[str, str] = {
    data["en"]: emj
    for emj, data in emoji.EMOJI_DATA.items()
    if "en" in data and data["status"] <= emoji.STATUS["fully_qualified"]
}
_UNICODE_EMOJI_REGEX = "|".join(map(re.escape, sorted(language_pack.values(), key=len, reverse=True)))
_DISCORD_EMOJI_REGEX = "<a?:[a-zA-Z0-9_]{1,32}:[0-9]{17,22}>"

EMOJI_REGEX: Final[re.Pattern[str]] = re.compile(f"({_UNICODE_EMOJI_REGEX}|{_DISCORD_EMOJI_REGEX})")
UNICODE_EMOJI_REGEX: Final[re.Pattern[str]] = re.compile(_UNICODE_EMOJI_REGEX)


class NodeType(Enum):
    text = 0
    emoji = 1
    discord_emoji = 2


class Node(NamedTuple):
    """Represents a parsed node inside of a string."""

    type: NodeType
    content: str

    def __repr__(self) -> str:
        return f"<Node type={self.type.name!r} content={self.content!r}>"


def _parse_line(line: str, unicode_only: bool = True) -> list[Node]:
    """解析一行文本，识别 Unicode emoji 和 Discord emoji"""
    if not line:
        return []

    last_end = 0
    nodes: list[Node] = []
    regex = UNICODE_EMOJI_REGEX if unicode_only else EMOJI_REGEX

    for match in regex.finditer(line):
        start, end = match.span()

        # 添加 emoji 之前的文本
        if start > last_end:
            nodes.append(Node(NodeType.text, line[last_end:start]))

        # 添加 emoji 节点
        emoji_text = match.group()
        if len(emoji_text) > 18:  # Discord emoji
            emoji_id = emoji_text.split(":")[-1][:-1]
            nodes.append(Node(NodeType.discord_emoji, emoji_id))
        else:  # Unicode emoji
            nodes.append(Node(NodeType.emoji, emoji_text))

        last_end = end

    # 添加最后剩余的文本
    if last_end < len(line):
        nodes.append(Node(NodeType.text, line[last_end:]))

    return nodes


def to_nodes(text: str, unicode_only: bool = True) -> list[list[Node]]:
    return [_parse_line(line, unicode_only) for line in text.splitlines()]


def get_font_size(font: FontT) -> float:
    """Get the size of a font, handling both FreeTypeFont and TransposedFont."""
    if isinstance(font, ImageFont.TransposedFont):
        assert not isinstance(font.font, ImageFont.ImageFont), "font.font should not be an ImageFont"
        return font.font.size
    return font.size


def getsize(
    text: str,
    font: FontT,
    *,
    spacing: int = 4,
    emoji_scale_factor: float = 1,
) -> tuple[int, float]:
    """Return the width and height of the text when rendered.
    This method supports multiline text.

    Parameters
    ----------
    text: str
        The text to use.
    font
        The font of the text.
    spacing: int
        The spacing between lines, in pixels.
        Defaults to `4`.
    emoji_scale_factor: float
        The rescaling factor for emojis.
        Defaults to `1`.
    """

    x, y = 0, 0
    nodes = to_nodes(text)

    for line in nodes:
        this_x = 0
        for node in line:
            content = node.content

            if node.type is not NodeType.text:
                width = int(emoji_scale_factor * get_font_size(font))
            else:
                width = int(font.getlength(content))

            this_x += width

        y += spacing + get_font_size(font)

        if this_x > x:
            x = this_x

    return x, y - spacing
