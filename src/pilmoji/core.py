import asyncio
from io import BytesIO
from typing import SupportsInt

from PIL import Image, ImageDraw

from .source import BaseSource, EmojiCDNSource, HTTPBasedSource
from .helpers import FontT, ColorT, NodeType, to_nodes, get_font_size, get_font_height


class Pilmoji:
    """The emoji rendering interface."""

    EMOJI_PADDING = 1

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

    def close(self) -> None:
        if self._cache:
            for stream in self._emoji_cache.values():
                stream.close()

            for stream in self._discord_emoji_cache.values():
                stream.close()

            self._emoji_cache = {}
            self._discord_emoji_cache = {}

    async def aclose(self) -> None:
        if isinstance(self._source, HTTPBasedSource):
            await self._source.aclose()

    async def _get_emoji(self, emoji: str) -> BytesIO | None:
        if self._cache and emoji in self._emoji_cache:
            bytesio = self._emoji_cache[emoji]
            return bytesio

        if bytesio := await self._source.get_emoji(emoji):
            if self._cache:
                self._emoji_cache[emoji] = bytesio
            return bytesio

    async def _get_discord_emoji(self, id: SupportsInt) -> BytesIO | None:
        id = int(id)

        if self._cache and id in self._discord_emoji_cache:
            bytesio = self._discord_emoji_cache[id]
            return bytesio

        if bytesio := await self._source.get_discord_emoji(id):
            if self._cache:
                self._discord_emoji_cache[id] = bytesio
            return bytesio

    def _render_text(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int],
        content: str,
        font: FontT,
        fill: ColorT | None,
    ) -> int:
        """Render a text node and return its width."""
        draw.text(xy, content, font=font, fill=fill)
        return int(font.getlength(content))

    def _render_emoji(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        bytesio: BytesIO,
        size: float,
    ) -> int:
        """Render an emoji node and return its width."""
        bytesio.seek(0)
        with Image.open(bytesio).convert("RGBA") as emoji_img:
            emoji_size = int(size) - self.EMOJI_PADDING
            aspect_ratio = emoji_img.height / emoji_img.width
            resized = emoji_img.resize(
                (emoji_size, int(emoji_size * aspect_ratio)),
                Image.Resampling.LANCZOS,
            )
            image.paste(resized, xy, resized)
            return emoji_size

    async def text(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
    ) -> None:
        """Simplified text rendering method with Unicode emoji support.

        This method provides a straightforward implementation without complex layout parameters.
        Suitable for most simple use cases.

        Parameters
        ----------
        image: Image.Image
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
        draw = ImageDraw.Draw(image)
        x, y = xy

        # Parse text into nodes (Unicode emoji only)
        lines = to_nodes(text)

        # Collect all unique Unicode emojis to download
        emoji_set = {node.content for line in lines for node in line if node.type is NodeType.EMOJI}

        # Download all emojis concurrently
        emoji_tasks = [self._get_emoji(emoji) for emoji in emoji_set]

        if emoji_tasks:
            emoji_results = await asyncio.gather(*emoji_tasks)
            emoji_map = dict(zip(emoji_set, emoji_results))
        else:
            emoji_map = {}

        # Render each line
        font_size = get_font_size(font)
        line_height = get_font_height(font)
        y_diff = int((line_height - font_size) / 2)

        for line in lines:
            cur_x = x

            for node in line:
                if node.type is NodeType.EMOJI:
                    if bytesio := emoji_map.get(node.content):
                        cur_x += self._render_emoji(image, (cur_x, y + y_diff), bytesio, font_size)
                    else:
                        cur_x += self._render_text(draw, (cur_x, y), node.content, font, fill)
                else:
                    # Text node or Discord emoji (rendered as text)
                    cur_x += self._render_text(draw, (cur_x, y), node.content, font, fill)

            y += line_height

    async def text_with_discord_emoji(
        self,
        image: Image.Image,
        xy: tuple[int, int],
        text: str,
        font: FontT,
        fill: ColorT | None = None,
    ) -> None:
        """Simplified text rendering method with Unicode and Discord emoji support.

        This method provides a straightforward implementation without complex layout parameters.
        Suitable for scenarios requiring Discord emoji rendering.

        Parameters
        ----------
        image: Image.Image
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
        draw = ImageDraw.Draw(image)
        x, y = xy

        # Parse text into nodes
        lines = to_nodes(text, False)

        # Collect all unique emojis to download
        emoji_set = {node.content for line in lines for node in line if node.type is NodeType.EMOJI}

        discord_emoji_set = {
            int(node.content) for line in lines for node in line if node.type is NodeType.DISCORD_EMOJI
        }

        # Download all emojis concurrently
        emoji_tasks = [self._get_emoji(emoji) for emoji in emoji_set]
        discord_tasks = [self._get_discord_emoji(eid) for eid in discord_emoji_set]

        if emoji_tasks or discord_tasks:
            results = await asyncio.gather(*emoji_tasks, *discord_tasks)
            emoji_results = results[: len(emoji_tasks)]
            discord_results = results[len(emoji_tasks) :]

            # Build emoji mappings
            emoji_map = dict(zip(emoji_set, emoji_results))
            discord_map = dict(zip(discord_emoji_set, discord_results))
        else:
            emoji_map = {}
            discord_map = {}

        # Render each line
        font_size = get_font_size(font)
        line_height = get_font_height(font)
        y_diff = int((line_height - font_size) / 2)

        for line in lines:
            cur_x = x

            for node in line:
                stream = None
                fallback_text = node.content

                if node.type is NodeType.EMOJI:
                    stream = emoji_map.get(node.content)
                elif node.type is NodeType.DISCORD_EMOJI:
                    stream = discord_map.get(int(node.content))
                    if not stream:
                        fallback_text = f"[:{node.content}:]"

                # Render emoji or text
                if stream:
                    cur_x += self._render_emoji(image, (cur_x, y + y_diff), stream, font_size)
                else:
                    cur_x += self._render_text(draw, (cur_x, y), fallback_text, font, fill)

            y += line_height

    async def __aenter__(self):
        if isinstance(self._source, HTTPBasedSource):
            await self._source.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"<Pilmoji source={self._source} cache={self._cache}>"
