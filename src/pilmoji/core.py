from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from io import BytesIO
import math
from typing import TYPE_CHECKING, SupportsInt

from PIL import Image, ImageDraw, ImageFont

from .helpers import NodeType, get_font_size, to_nodes
from .source import BaseSource, EmojiCDNSource, HTTPBasedSource

if TYPE_CHECKING:
    FontT = ImageFont.FreeTypeFont | ImageFont.TransposedFont
    ColorT = int | tuple[int, int, int] | tuple[int, int, int, int] | str

__all__ = ("Pilmoji",)


class Pilmoji:
    """The main emoji rendering interface.

    .. note::
        This should be used in an async context manager.

    .. note::
        Requires Pillow 11.0.0 or higher.

    Parameters
    ----------
    image: :class:`PIL.Image.Image`
        The Pillow image to render on.
    source: Union[:class:`~.BaseSource`, Type[:class:`~.BaseSource`]]
        The emoji image source to use.
        This defaults to :class:`~.TwitterEmojiSource`.
    cache: bool
        Whether or not to cache emojis given from source.
        Enabling this is recommended and by default.
    draw: :class:`PIL.ImageDraw.ImageDraw`
        The drawing instance to use. If left unfilled,
        a new drawing instance will be created.
    render_discord_emoji: bool
        Whether or not to render Discord emoji. Defaults to `True`
    emoji_scale_factor: float
        The default rescaling factor for emojis. Defaults to `1`
    emoji_position_offset: Tuple[int, int]
        A 2-tuple representing the x and y offset for emojis when rendering,
        respectively. Defaults to `(0, 0)`
    """

    def __init__(
        self,
        *,
        source: BaseSource = EmojiCDNSource(),
        cache: bool = True,
        render_discord_emoji: bool = True,
        emoji_scale_factor: float = 1.0,
        emoji_position_offset: tuple[int, int] = (0, 0),
    ) -> None:
        self.source: BaseSource = source
        self._cache: bool = cache
        self._closed: bool = False
        self._new_draw: bool = False

        self._render_discord_emoji: bool = render_discord_emoji
        self._default_emoji_scale_factor: float = emoji_scale_factor
        self._default_emoji_position_offset: tuple[int, int] = emoji_position_offset

        self._emoji_cache: dict[str, BytesIO] = {}
        self._discord_emoji_cache: dict[int, BytesIO] = {}

    def close(self) -> None:
        if self._closed:
            raise ValueError("Pilmoji has already been closed.")

        if self._cache:
            for stream in self._emoji_cache.values():
                stream.close()

            for stream in self._discord_emoji_cache.values():
                stream.close()

            self._emoji_cache = {}
            self._discord_emoji_cache = {}

        self._closed = True

    async def aclose(self) -> None:
        if not self._closed:
            self.close()

        if isinstance(self.source, HTTPBasedSource):
            await self.source.aclose()

    async def _get_emoji(self, emoji: str) -> BytesIO | None:
        if self._cache and emoji in self._emoji_cache:
            entry = self._emoji_cache[emoji]
            entry.seek(0)
            return entry

        if stream := await self.source.get_emoji(emoji):
            if self._cache:
                self._emoji_cache[emoji] = stream

            stream.seek(0)
            return stream

    async def _get_discord_emoji(self, id: SupportsInt) -> BytesIO | None:
        id = int(id)

        if self._cache and id in self._discord_emoji_cache:
            entry = self._discord_emoji_cache[id]
            entry.seek(0)
            return entry

        if stream := await self.source.get_discord_emoji(id):
            if self._cache:
                self._discord_emoji_cache[id] = stream

            stream.seek(0)
            return stream

    def _render_text_node(
        self, draw: ImageDraw.ImageDraw, pos: tuple[int, int], content: str, font: FontT, fill: ColorT | None
    ) -> int:
        """渲染文本节点，返回占用的宽度"""
        draw.text(pos, content, font=font, fill=fill)
        return int(font.getlength(content))

    def _render_emoji_node(self, image: Image.Image, pos: tuple[int, int], stream: BytesIO, font_size: float) -> int:
        """渲染 emoji 节点，返回占用的宽度"""
        stream.seek(0)
        with Image.open(stream).convert("RGBA") as emoji_img:
            emoji_size = int(font_size)
            aspect_ratio = emoji_img.height / emoji_img.width
            resized = emoji_img.resize((emoji_size, int(emoji_size * aspect_ratio)), Image.Resampling.LANCZOS)
            image.paste(resized, pos, resized)
            return emoji_size

    async def text(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
    ) -> None:
        """简化版的文本渲染方法，支持 emoji。

        这个方法提供了更简单直接的实现，去掉了复杂的排版参数。
        适合大多数简单场景使用。

        Parameters
        ----------
        image: Image.Image
            要渲染到的图像
        xy: tuple[int, int]
            渲染位置 (x, y)
        text: str
            要渲染的文本（支持单行或多行）
        font: FontT
            字体
        fill: ColorT | None
            文本颜色，默认为黑色
        """
        draw = ImageDraw.Draw(image)
        x, y = xy

        # 解析文本为节点
        lines = to_nodes(text)

        # 收集所有需要下载的 emoji（去重）
        emoji_set: dict[str, None] = {}
        discord_emoji_set: dict[int, None] = {}

        for line in lines:
            for node in line:
                if node.type is NodeType.emoji:
                    emoji_set[node.content] = None
                elif self._render_discord_emoji and node.type is NodeType.discord_emoji:
                    discord_emoji_set[int(node.content)] = None

        # 并发下载所有 emoji
        emoji_tasks = [self._get_emoji(emoji) for emoji in emoji_set.keys()]
        discord_tasks = [self._get_discord_emoji(eid) for eid in discord_emoji_set.keys()]

        emoji_results = []
        if emoji_tasks or discord_tasks:
            results = await asyncio.gather(*emoji_tasks, *discord_tasks)
            emoji_results = results[: len(emoji_tasks)]
            discord_results = results[len(emoji_tasks) :]

            # 建立映射
            emoji_map = dict(zip(emoji_set.keys(), emoji_results))
            discord_map = dict(zip(discord_emoji_set.keys(), discord_results))
        else:
            emoji_map = {}
            discord_map = {}

        # 渲染每一行
        font_size = get_font_size(font)
        line_height = int(font_size * 1.2)  # 行高为字体大小的 1.2 倍

        for line in lines:
            current_x = x

            for node in line:
                if node.type is NodeType.text:
                    current_x += self._render_text_node(draw, (current_x, y), node.content, font, fill)

                elif node.type is NodeType.emoji:
                    stream = emoji_map.get(node.content)
                    if stream:
                        current_x += self._render_emoji_node(image, (current_x, y), stream, font_size)
                    else:
                        current_x += self._render_text_node(draw, (current_x, y), node.content, font, fill)

                elif self._render_discord_emoji and node.type is NodeType.discord_emoji:
                    stream = discord_map.get(int(node.content))
                    if stream:
                        current_x += self._render_emoji_node(image, (current_x, y), stream, font_size)
                    else:
                        placeholder = f"[:{node.content}:]"
                        current_x += self._render_text_node(draw, (current_x, y), placeholder, font, fill)

            y += line_height

    async def text_old(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
        anchor: str | None = None,
        draw: ImageDraw.ImageDraw | None = None,
        spacing: int = 4,
        node_spacing: int = 0,
        align: str = "left",
        direction: str | None = None,
        features: list[str] | None = None,
        language: str | None = None,
        stroke_width: int = 0,
        stroke_fill: ColorT | None = None,
        embedded_color: bool = False,
        emoji_scale_factor: float | None = None,
        emoji_position_offset: tuple[int, int] | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Draws the string at the given position, with emoji rendering support.
        This method supports multiline text.

        .. note::
            Some parameters have not been implemented yet.

        .. note::
            The signature of this function is a superset of the signature of Pillow's `ImageDraw.text`.

        .. note::
            Not all parameters are listed here.

        Parameters
        ----------
        xy: Tuple[int, int]
            The position to render the text at.
        text: str
            The text to render.
        fill
            The fill color of the text.
        font
            The font to render the text with.
        spacing: int
            How many pixels there should be between lines. Defaults to `4`
        node_spacing: int
            How many pixels there should be between nodes (text/unicode_emojis/custom_emojis). Defaults to `0`
        emoji_scale_factor: float
            The rescaling factor for emojis. This can be used for fine adjustments.
            Defaults to the factor given in the class constructor, or `1`.
        emoji_position_offset: Tuple[int, int]
            The emoji position offset for emojis. This can be used for fine adjustments.
            Defaults to the offset given in the class constructor, or `(0, 0)`.
        """

        if emoji_scale_factor is None:
            emoji_scale_factor = self._default_emoji_scale_factor

        if emoji_position_offset is None:
            emoji_position_offset = self._default_emoji_position_offset

        # first we need to test the anchor
        # because we want to make the exact same positions transformations than the "ImageDraw"."text" function in PIL
        # https://github.com/python-pillow/Pillow/blob/66c244af3233b1cc6cc2c424e9714420aca109ad/src/PIL/ImageDraw.py#L449

        # also we are note using the "ImageDraw"."multiline_text" since when we are cuting the text in nodes
        # a lot of code could be simplify this way
        # https://github.com/python-pillow/Pillow/blob/66c244af3233b1cc6cc2c424e9714420aca109ad/src/PIL/ImageDraw.py#L567

        if anchor is None:
            anchor = "la"
        elif len(anchor) != 2:
            msg = "anchor must be a 2 character string"
            raise ValueError(msg)
        elif anchor[1] in "tb" and "\n" in text:
            msg = "anchor not supported for multiline text"
            raise ValueError(msg)

        # need to be checked here because we are not using the real "ImageDraw"."multiline_text"
        if direction == "ttb" and "\n" in text:
            msg = "ttb direction is unsupported for multiline text"
            raise ValueError(msg)

        if draw is None:
            draw = ImageDraw.Draw(image)

        def getink(fill):
            ink, fill = draw._getink(fill)
            if ink is None:
                return fill
            return ink

        x, y = xy
        original_x = x
        nodes = to_nodes(text)
        # get the distance between lines ( will be add to y between each line )
        # font is guaranteed to be FontT at this point (not None)
        assert font is not None, "Font should not be None at this point"
        line_spacing = draw.textbbox((0, 0), "A", font, stroke_width=stroke_width)[3] + stroke_width + spacing

        # I change a part of the logic of text writing because it couldn't work "the same as PIL" if I didn't
        nodes_line_to_print = []
        widths = []
        max_width = 0
        streams: dict[int, dict[int, BytesIO]] = {}
        fetch_lookup: dict[tuple[NodeType, str | int], Awaitable[BytesIO | None]] = {}
        slot_lookup: dict[tuple[int, int], tuple[NodeType, str | int]] = {}
        mode = draw.fontmode
        if stroke_width == 0 and embedded_color:
            mode = "RGBA"
        ink = getink(fill)
        # we get the size taken by a " " to be drawn with the given options
        space_text_length = draw.textlength(
            " ", font, direction=direction, features=features, language=language, embedded_color=embedded_color
        )

        for node_id, line in enumerate(nodes):
            streams[node_id] = {}
            for line_id, node in enumerate(line):
                if node.type is NodeType.emoji:
                    key = (NodeType.emoji, node.content)
                    slot_lookup[(node_id, line_id)] = key
                    if key not in fetch_lookup:
                        fetch_lookup[key] = self._get_emoji(node.content)
                elif self._render_discord_emoji and node.type is NodeType.discord_emoji:
                    emoji_id = int(node.content)
                    key = (NodeType.discord_emoji, emoji_id)
                    slot_lookup[(node_id, line_id)] = key
                    if key not in fetch_lookup:
                        fetch_lookup[key] = self._get_discord_emoji(emoji_id)

        if fetch_lookup:
            keys = list(fetch_lookup.keys())
            results = await asyncio.gather(*(fetch_lookup[key] for key in keys))
            resolved_streams: dict[tuple[NodeType, str | int], BytesIO] = {}
            for key, stream in zip(keys, results):
                if stream:
                    resolved_streams[key] = stream

            for (node_id, line_id), key in slot_lookup.items():
                stream = resolved_streams.get(key)
                if stream:
                    streams[node_id][line_id] = stream

        for node_id, line in enumerate(nodes):
            text_line = ""
            for line_id, node in enumerate(line):
                if node.type is NodeType.text or line_id not in streams[node_id]:
                    # each text in the same line are concatenate
                    text_line += node.content
                    continue

                # font is guaranteed to be FontT at this point (not None)
                assert font is not None, "Font should not be None at this point"
                width = round(emoji_scale_factor * get_font_size(font))
                ox, oy = emoji_position_offset
                size = round(width + ox + (node_spacing * 2))
                # for every emoji we calculate the space needed to display it in the current text
                space_to_had = round(size / space_text_length)
                # we had the equivalent space as " " character in the line text
                text_line += "".join(" " for x in range(space_to_had))

            # saving each line with the place to display emoji at the right place
            nodes_line_to_print.append(text_line)
            line_width = draw.textlength(text_line, font, direction=direction, features=features, language=language)
            widths.append(line_width)
            max_width = max(max_width, line_width)

        # taking into account the anchor to place the text in the right place
        if anchor[1] == "m":
            y -= (len(nodes) - 1) * line_spacing / 2.0
        elif anchor[1] == "d":
            y -= (len(nodes) - 1) * line_spacing

        for node_id, line in enumerate(nodes):
            # restore the original x wanted for each line
            x = original_x
            # some transformations should not be applied to y
            line_y = y
            width_difference = max_width - widths[node_id]

            # first align left by anchor
            if anchor[0] == "m":
                x -= width_difference / 2.0
            elif anchor[0] == "r":
                x -= width_difference

            # then align by align parameter
            if align == "left":
                pass
            elif align == "center":
                x += width_difference / 2.0
            elif align == "right":
                x += width_difference
            else:
                msg = 'align must be "left", "center" or "right"'
                raise ValueError(msg)

            # if this line hase text to display then we draw it all at once ( one time only per line )
            if len(nodes_line_to_print[node_id]) > 0:
                draw.text(
                    (x, line_y),
                    nodes_line_to_print[node_id],
                    fill=fill,
                    font=font,
                    anchor=anchor,
                    spacing=spacing,
                    align=align,
                    direction=direction,
                    features=features,
                    language=language,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill,
                    embedded_color=embedded_color,
                    *args,
                    **kwargs,
                )

            coord = (x, y)
            start = (math.modf((x, y)[0])[0], math.modf((x, y)[1])[0])
            # respecting the way parameters are used in PIL to find the good x and y
            if ink is not None:
                stroke_ink = None
                if stroke_width:
                    stroke_ink = getink(stroke_fill) if stroke_fill is not None else ink

                if stroke_ink is not None:
                    ink = stroke_ink
                    stroke_width = 0
                try:
                    _font = font if isinstance(font, ImageFont.FreeTypeFont) else font.font
                    assert isinstance(_font, ImageFont.FreeTypeFont), "font should be a FreeTypeFont"
                    _, offset = _font.getmask2(
                        nodes_line_to_print[node_id],
                        mode,
                        direction=direction,
                        features=features,
                        language=language,
                        stroke_width=stroke_width,
                        anchor=anchor,
                        ink=ink,
                        start=start,
                        *args,
                        **kwargs,
                    )
                    coord = coord[0] + offset[0], coord[1] + offset[1]
                except AttributeError:
                    pass
                x, line_y = coord

            for line_id, node in enumerate(line):
                content = node.content

                # if node is text then we decale our x
                # but since the text line as already be drawn we do not need to draw text here anymore
                if node.type is NodeType.text or line_id not in streams[node_id]:
                    width = int(font.getlength(content, direction=direction, features=features, language=language))
                    x += node_spacing + width
                    continue

                if line_id in streams[node_id]:
                    stream = streams[node_id][line_id]
                    stream.seek(0)
                    with Image.open(stream).convert("RGBA") as asset:
                        # font is guaranteed to be FontT at this point (not None)
                        assert font is not None, "Font should not be None at this point"
                        width = round(emoji_scale_factor * get_font_size(font))
                        size = width, round(math.ceil(asset.height / asset.width * width))
                        asset = asset.resize(size, Image.Resampling.LANCZOS)
                        ox, oy = emoji_position_offset

                        image.paste(asset, (round(x + ox), round(line_y + oy)), asset)
                        x += node_spacing + width
                    stream.seek(0)
                    continue
            y += line_spacing

    async def __aenter__(self: "Pilmoji") -> "Pilmoji":
        if isinstance(self.source, HTTPBasedSource):
            await self.source.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"<Pilmoji source={self.source} cache={self._cache}>"
