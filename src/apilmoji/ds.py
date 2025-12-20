import re
from typing import Final

from .helper import UNICODE_EMOJI_SET, Node, NodeType
from .helper import contains_emoji as contains_unicode_emoji

# Regex patterns for matching emojis
_UNICODE_EMOJI_REGEX: Final[str] = "|".join(
    map(re.escape, sorted(UNICODE_EMOJI_SET, key=len, reverse=True))
)
_DISCORD_EMOJI_REGEX: Final[str] = r"<a?:[a-zA-Z0-9_]{1,32}:(?P<id>[0-9]{17,22})>"
DISCORD_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(_DISCORD_EMOJI_REGEX)
ALL_EMOJI_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"{_UNICODE_EMOJI_REGEX}|{_DISCORD_EMOJI_REGEX}"
)


def contains_discord_emoji(lines: list[str]) -> bool:
    """Check if a string contains any Discord emoji"""
    return bool(DISCORD_EMOJI_PATTERN.search("\n".join(lines)))


def contains_emoji(lines: list[str]) -> bool:
    """Check if a string contains any emoji (Unicode or Discord)"""
    return contains_unicode_emoji(lines) or contains_discord_emoji(lines)


def parse_lines(lines: list[str]) -> list[list[Node]]:
    """Parse lines containing both Unicode and Discord emojis"""
    return [_parse_line(line) for line in lines]


def _parse_line(line: str) -> list[Node]:
    """Parse a line of text, identifying Unicode emojis and Discord emojis."""
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
