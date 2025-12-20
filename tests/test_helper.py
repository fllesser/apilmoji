def test_parse_line_common():
    from apilmoji.helper import Node, NodeType, _parse_line

    line = "Hello👋Hello"
    nodes = _parse_line(line)
    assert nodes == [
        Node(NodeType.TEXT, "Hello"),
        Node(NodeType.EMOJI, "👋"),
        Node(NodeType.TEXT, "Hello"),
    ]


def test_parse_line_contains_combo_emoji():
    from apilmoji.helper import Node, NodeType, _parse_line

    line = "👍🏻|👍🏼|👍🏽|👍🏾|👍🏿"
    nodes = _parse_line(line)
    assert nodes == [
        Node(NodeType.EMOJI, "👍🏻"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏼"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏽"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏾"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏿"),
    ]


def test_parse_line_contains_ds_emoji():
    from apilmoji.regex import Node, NodeType, _parse_line_all

    line = "👍🏻|👍🏼|👍🏽|<:rooThink:596576798351949847>|👍🏾|👍🏿"
    nodes = _parse_line_all(line)
    assert nodes == [
        Node(NodeType.EMOJI, "👍🏻"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏼"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏽"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.DSEMOJI, "596576798351949847"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏾"),
        Node(NodeType.TEXT, "|"),
        Node(NodeType.EMOJI, "👍🏿"),
    ]
