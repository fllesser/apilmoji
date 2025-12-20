from enum import Enum
from typing import Final, NamedTuple

from emoji import EMOJI_DATA, emoji_list

# Build emoji language pack mapping English names to emoji characters
UNICODE_EMOJI_SET: Final[set[str]] = {
    emj for emj, data in EMOJI_DATA.items() if data["status"] <= 2
}


class NodeType(Enum):
    TEXT = 0
    EMOJI = 1
    DSEMOJI = 2


class Node(NamedTuple):
    type: NodeType
    content: str


def contains_emoji(lines: list[str]) -> bool:
    """Check if a string contains any Unicode emoji characters"""
    for line in lines:
        for char in line:
            if char in UNICODE_EMOJI_SET:
                return True
    return False


def parse_lines(lines: list[str]) -> list[list[Node]]:
    """Parse lines containing Unicode emojis"""
    return [_parse_line(line) for line in lines]


def _parse_line(line: str) -> list[Node]:
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
