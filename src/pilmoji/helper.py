import re
from enum import Enum
from typing import Final, NamedTuple

from PIL import ImageFont
from emoji import STATUS, EMOJI_DATA

# Type aliases for font and color specifications
FontT = ImageFont.FreeTypeFont | ImageFont.TransposedFont

# Build emoji language pack mapping English names to emoji characters
UNICODE_EMOJI_SET: Final[set[str]] = {
    emj
    for emj, data in EMOJI_DATA.items()
    if data["status"] <= STATUS["fully_qualified"]
}

# Regex patterns for matching emojis
_UNICODE_EMOJI_REGEX: Final[str] = "|".join(
    map(re.escape, sorted(UNICODE_EMOJI_SET, key=len, reverse=True))
)
_DISCORD_EMOJI_REGEX: Final[str] = r"<a?:[a-zA-Z0-9_]{1,32}:[0-9]{17,22}>"

UNICODE_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(_UNICODE_EMOJI_REGEX)
DISCORD_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(_DISCORD_EMOJI_REGEX)
EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"({_UNICODE_EMOJI_REGEX}|{_DISCORD_EMOJI_REGEX})"
)


class NodeType(Enum):
    TEXT = 0
    EMOJI = 1
    DISCORD_EMOJI = 2


class Node(NamedTuple):
    """Represents a parsed node inside of a string."""

    type: NodeType
    content: str


def contains_emoji(lines: list[str], support_ds_emj: bool = False) -> bool:
    """Check if a string contains any emoji characters using a fast regex pattern.
    Parameters
    ----------
    text : str | list[str]
        The text to check
    unicode_only : bool, default=True
        If True, only match Unicode emojis; if False, also match Discord emojis

    Returns
    -------
    bool
        True if the text contains any emoji characters, False otherwise
    """
    for line in lines:
        for char in line:
            if char in UNICODE_EMOJI_SET:
                return True

    return support_ds_emj and bool(DISCORD_EMOJI_PATTERN.search("\n".join(lines)))


def to_nodes(lines: list[str], support_ds_emj: bool = False) -> list[list[Node]]:
    return [_parse_line(line, support_ds_emj) for line in lines]


def _parse_line(line: str, support_ds_emj: bool = False) -> list[Node]:
    """Parse a line of text, identifying Unicode emojis and Discord emojis.

    Parameters
    ----------
    line : str
        The text line to parse
    unicode_only : bool, default=True
        If True, only match Unicode emojis; if False, also match Discord emojis

    Returns
    -------
    list[Node]
        A list of parsed nodes representing text and emoji segments
    """
    last_end = 0
    nodes: list[Node] = []
    pattern = EMOJI_PATTERN if support_ds_emj else UNICODE_EMOJI_PATTERN

    for match in pattern.finditer(line):
        start, end = match.span()

        # Add text before the emoji
        if start > last_end:
            nodes.append(Node(NodeType.TEXT, line[last_end:start]))

        # Add emoji node
        emoji_text = match.group()
        if len(emoji_text) > 18:  # Discord emoji
            emoji_id = emoji_text.split(":")[-1][:-1]
            nodes.append(Node(NodeType.DISCORD_EMOJI, emoji_id))
        else:  # Unicode emoji
            nodes.append(Node(NodeType.EMOJI, emoji_text))

        last_end = end

    # Add remaining text after the last emoji
    if last_end < len(line):
        nodes.append(Node(NodeType.TEXT, line[last_end:]))

    return nodes


def get_font_size(font: FontT) -> float:
    """Get the size of a font, handling both FreeTypeFont and TransposedFont.

    Parameters
    ----------
    font : FontT
        The font object to get the size from

    Returns
    -------
    float
        The font size in points
    """
    if isinstance(font, ImageFont.TransposedFont):
        assert not isinstance(font.font, ImageFont.ImageFont), (
            "font.font should not be an ImageFont"
        )
        return font.font.size
    return font.size


def get_font_height(font: FontT) -> int:
    """Get the line height of a font.

    Parameters
    ----------
    font : FontT
        The font object to get the height from

    Returns
    -------
    int
        The line height in pixels
    """
    if isinstance(font, ImageFont.FreeTypeFont):
        ascent, descent = font.getmetrics()
        return ascent + descent
    return int(get_font_size(font) * 1.2)
