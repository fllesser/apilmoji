import asyncio
from io import BytesIO

from PIL import Image, ImageDraw

from . import helper
from .helper import FontT, ColorT, NodeType
from .source import BaseSource, EmojiCDNSource, HTTPBasedSource

PILImage = Image.Image
PILDraw = ImageDraw.ImageDraw


class Pilmoji:
    """The emoji rendering interface."""

    SIZE_DIFF = 1

    def __init__(
        self,
        *,
        source: BaseSource = EmojiCDNSource(),
        cache: bool = True,
    ) -> None:
        self._cache: bool = cache
        self._source: BaseSource = source
        self._emoji_cache: dict[str, BytesIO] = {}
        self._discord_emoji_cache: dict[int, BytesIO] = {}

    async def aclose(self) -> None:
        if isinstance(self._source, HTTPBasedSource):
            await self._source.aclose()

    async def _get_emoji(self, emoji: str) -> BytesIO | None:
        if self._cache and emoji in self._emoji_cache:
            return self._emoji_cache[emoji]

        if bytesio := await self._source.get_emoji(emoji):
            if self._cache:
                self._emoji_cache[emoji] = bytesio
            return bytesio

    async def _get_discord_emoji(self, id: int) -> BytesIO | None:
        if self._cache and id in self._discord_emoji_cache:
            return self._discord_emoji_cache[id]

        if bytesio := await self._source.get_discord_emoji(id):
            if self._cache:
                self._discord_emoji_cache[id] = bytesio
            return bytesio

    def _render_text(
        self,
        draw: PILDraw,
        xy: tuple[int, int],
        content: str,
        font: FontT,
        fill: ColorT | None,
    ):
        """Render text"""
        draw.text(xy, content, font=font, fill=fill)

    def _render_emoji(
        self,
        image: PILImage,
        xy: tuple[int, int],
        bytesio: BytesIO,
        size: float,
    ):
        """Render emoji"""
        bytesio.seek(0)
        with Image.open(bytesio).convert("RGBA") as emoji_img:
            emoji_size = int(size) - self.SIZE_DIFF
            aspect_ratio = emoji_img.height / emoji_img.width
            resized = emoji_img.resize(
                (emoji_size, int(emoji_size * aspect_ratio)),
                Image.Resampling.LANCZOS,
            )
            image.paste(resized, xy, resized)

    async def text(
        self,
        image: PILImage,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
    ) -> None:
        """Simplified text rendering method with Unicode emoji support.

        Parameters
        ----------
        image: PILImage
            The image to render onto
        xy: tuple[int, int]
            Rendering position (x, y)
        text: str
            The text to render (supports single or multiple lines)
        font: FontT
            The font to use
        fill: ColorT | None
            Text color, defaults to black
        """
        if not text:
            return

        x, y = xy
        draw = ImageDraw.Draw(image)
        line_height = helper.get_font_height(font)

        # check text has emoji
        if not helper.has_emoji(text):
            for line in text.splitlines():
                self._render_text(draw, (x, y), line, font, fill)
                y += line_height
            return

        # Parse text into nodes (Unicode emoji only)
        lines = helper.to_nodes(text)

        # Collect all unique Unicode emojis to download
        emj_set = {
            node.content
            for line in lines
            for node in line
            if node.type is NodeType.EMOJI
        }

        # Download all emojis concurrently
        emjios = await asyncio.gather(
            *[self._get_emoji(emoji) for emoji in emj_set],
        )
        emj_map = dict(zip(emj_set, emjios))

        # Render each line
        font_size = helper.get_font_size(font)
        y_diff = int((line_height - font_size) / 2)

        for line in lines:
            cur_x = x

            for node in line:
                if node.type is NodeType.EMOJI:
                    if bytesio := emj_map.get(node.content):
                        self._render_emoji(
                            image, (cur_x, y + y_diff), bytesio, font_size
                        )
                    else:
                        self._render_text(draw, (cur_x, y), node.content, font, fill)
                    cur_x += int(font_size)
                else:
                    # Text node
                    self._render_text(draw, (cur_x, y), node.content, font, fill)
                    cur_x += int(font.getlength(node.content))

            y += line_height

    async def text_with_discord_emoji(
        self,
        image: PILImage,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
    ) -> None:
        """Simplified text rendering method with Unicode and Discord emoji support.

        Parameters
        ----------
        image: PILImage
            The image to render onto
        xy: tuple[int, int]
            Rendering position (x, y)
        text: str
            The text to render (supports single or multiple lines)
        font: FontT
            The font to use
        fill: ColorT | None
            Text color, defaults to black
        """
        if not text:
            return

        x, y = xy
        draw = ImageDraw.Draw(image)
        line_height = helper.get_font_height(font)

        if not helper.has_emoji(text, False):
            for line in text.splitlines():
                self._render_text(draw, xy, line, font, fill)
            return

        # Parse text into nodes
        lines = helper.to_nodes(text, False)

        # Collect all unique emojis to download
        emj_set = {
            node.content
            for line in lines
            for node in line
            if node.type is NodeType.EMOJI
        }
        ds_emj_set = {
            int(node.content)
            for line in lines
            for node in line
            if node.type is NodeType.DISCORD_EMOJI
        }

        # Download all emojis concurrently
        emjios = await asyncio.gather(
            *[self._get_emoji(emoji) for emoji in emj_set],
            *[self._get_discord_emoji(eid) for eid in ds_emj_set],
        )

        emj_num = len(emj_set)
        emoji_results = emjios[:emj_num]
        discord_results = emjios[emj_num:]

        # Build emoji mappings
        emj_map = dict(zip(emj_set, emoji_results))
        ds_emj_map = dict(zip(ds_emj_set, discord_results))

        # Render each line
        font_size = helper.get_font_size(font)
        y_diff = int((line_height - font_size) / 2)

        for line in lines:
            cur_x = x

            for node in line:
                stream = None
                fallback_text = node.content

                if node.type is NodeType.EMOJI:
                    stream = emj_map.get(node.content)
                elif node.type is NodeType.DISCORD_EMOJI:
                    stream = ds_emj_map.get(int(node.content))
                    if not stream:
                        fallback_text = f"[:{node.content}:]"

                # Render emoji or text
                if stream:
                    self._render_emoji(image, (cur_x, y + y_diff), stream, font_size)
                    cur_x += int(font_size)
                else:
                    self._render_text(draw, (cur_x, y), fallback_text, font, fill)
                    cur_x += int(font.getlength(fallback_text))

            y += line_height

    async def __aenter__(self):
        if isinstance(self._source, HTTPBasedSource):
            await self._source.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"<Pilmoji source={self._source} cache={self._cache}>"
