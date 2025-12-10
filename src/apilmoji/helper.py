import re
from enum import Enum
from typing import Final, NamedTuple

from emoji import EMOJI_DATA, emoji_list

# Build emoji language pack mapping English names to emoji characters
UNICODE_EMOJI_SET: Final[set[str]] = {
    emj for emj, data in EMOJI_DATA.items() if data["status"] <= 2
}

# Regex patterns for matching emojis
_UNICODE_EMOJI_REGEX: Final[str] = "|".join(
    map(re.escape, sorted(UNICODE_EMOJI_SET, key=len, reverse=True))
)
_DISCORD_EMOJI_REGEX: Final[str] = r"<a?:[a-zA-Z0-9_]{1,32}:(?P<id>[0-9]{17,22})>"
DISCORD_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(_DISCORD_EMOJI_REGEX)
ALL_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{_UNICODE_EMOJI_REGEX}|{_DISCORD_EMOJI_REGEX}"
)


class NodeType(Enum):
    TEXT = 0
    EMOJI = 1
    DSEMOJI = 2


class Node(NamedTuple):
    type: NodeType
    content: str


def contains_emoji(lines: list[str], support_ds_emj: bool = False) -> bool:
    """Check if a string contains any emoji characters using a fast regex pattern"""
    for line in lines:
        for char in line:
            if char in UNICODE_EMOJI_SET:
                return True

    return support_ds_emj and bool(DISCORD_EMOJI_PATTERN.search("\n".join(lines)))


def parse_lines(lines: list[str], support_ds_emj: bool = False) -> list[list[Node]]:
    return [_parse_line(line, support_ds_emj) for line in lines]


def _parse_line(line: str, support_ds_emj: bool = False) -> list[Node]:
    """Parse a line of text, identifying Unicode emojis and Discord emojis."""

    # find unicode emojis
    if not support_ds_emj:
        return _parse_line_unicode_only(line)

    nodes: list[Node] = []
    last_end = 0
    for matched in ALL_EMOJI_PATTERN.finditer(line):
        start, end = matched.span()

        # Add text before the emoji
        if start > last_end:
            nodes.append(Node(NodeType.TEXT, line[last_end:start]))

        # Add emoji node
        if emoji_id := matched.group("id"):
            nodes.append(Node(NodeType.DSEMOJI, emoji_id))
        else:
            nodes.append(Node(NodeType.EMOJI, matched.group(0)))
        last_end = end

    # Add remaining text after the last emoji
    if last_end < len(line):
        nodes.append(Node(NodeType.TEXT, line[last_end:]))

    return nodes


def _parse_line_unicode_only(line: str):
    """Parse a line of text, identifying Unicode emojis including sequences."""
    nodes: list[Node] = []

    # Use emoji_list to get proper emoji sequences
    emoji_positions = emoji_list(line)

    if not emoji_positions:
        # If no emojis found, treat entire line as text
        nodes.append(Node(NodeType.TEXT, line))
        return nodes

    # Track current position in the line
    current_pos = 0

    for emoji_info in emoji_positions:
        emoji_start = emoji_info["match_start"]
        emoji_end = emoji_info["match_end"]
        emoji_char = emoji_info["emoji"]

        # Add text before the emoji (if any)
        if emoji_start > current_pos:
            text_before = line[current_pos:emoji_start]
            nodes.append(Node(NodeType.TEXT, text_before))

        # Add the emoji
        nodes.append(Node(NodeType.EMOJI, emoji_char))

        # Update current position
        current_pos = emoji_end

    # Add remaining text after the last emoji (if any)
    if current_pos < len(line):
        text_after = line[current_pos:]
        nodes.append(Node(NodeType.TEXT, text_after))

    return nodes
