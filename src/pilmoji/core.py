import asyncio
from io import BytesIO
from typing import TypeVar
from collections.abc import Awaitable

from PIL import Image, ImageDraw

from . import helper
from .helper import FontT, NodeType
from .source import BaseSource, EmojiCDNSource, HTTPBasedSource

T = TypeVar("T")
PILImage = Image.Image
PILDraw = ImageDraw.ImageDraw
ColorT = int | str | tuple[int, int, int] | tuple[int, int, int, int]


class Pilmoji:
    """The emoji rendering interface."""

    def __init__(
        self,
        *,
        source: BaseSource = EmojiCDNSource(),
        cache: bool = True,
        enable_tqdm: bool = False,
    ) -> None:
        self._cache: bool = cache
        self._source: BaseSource = source
        self._emoji_cache: dict[str, BytesIO] = {}
        self._discord_emoji_cache: dict[int, BytesIO] = {}

        self.__tqdm = None
        if enable_tqdm:
            try:
                from tqdm.asyncio import tqdm

                self.__tqdm = tqdm
            except ImportError:
                pass

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

        return None

    async def _get_discord_emoji(self, id: int) -> BytesIO | None:
        if self._cache and id in self._discord_emoji_cache:
            return self._discord_emoji_cache[id]

        if bytesio := await self._source.get_discord_emoji(id):
            if self._cache:
                self._discord_emoji_cache[id] = bytesio
            return bytesio

        return None

    def _resize_emoji(self, bytesio: BytesIO, size: float) -> PILImage:
        """Resize emoji to fit the font size"""
        bytesio.seek(0)
        with Image.open(bytesio).convert("RGBA") as emoji_img:
            emoji_size = int(size) - 1
            aspect_ratio = emoji_img.height / emoji_img.width
            return emoji_img.resize(
                (emoji_size, int(emoji_size * aspect_ratio)),
                Image.Resampling.LANCZOS,
            )

    async def text(
        self,
        image: PILImage,
        xy: tuple[int, int],
        lines: list[str],
        font: FontT,
        *,
        fill: ColorT | None = None,
        line_height: int | None = None,
        support_ds_emj: bool = False,
    ) -> None:
        """Text rendering method with Unicode and optional Discord emoji support.

        Parameters
        ----------
        image: PILImage
            The image to render onto
        xy: tuple[int, int]
            Rendering position (x, y)
        text: str | list[str]
            The text to render (supports single or multiple lines)
        font: FontT
            The font to use
        fill: ColorT | None
            Text color, defaults to black
        line_height: int | None
            Line height, defaults to font height
        support_discord_emoji: bool
            Whether to support Discord emoji parsing, defaults to False
        """
        if not lines:
            return

        x, y = xy
        draw = ImageDraw.Draw(image)
        line_height = line_height or helper.get_font_height(font)

        # Check if lines has emoji
        if not helper.contains_emoji(lines, support_ds_emj):
            for line in lines:
                draw.text((x, y), line, font=font, fill=fill)
                y += line_height
            return
        # Parse lines into nodes
        nodes_lst = helper.to_nodes(lines, support_ds_emj)

        # Collect all unique emojis to download
        emj_set = {
            node.content
            for line in nodes_lst
            for node in line
            if node.type is NodeType.EMOJI
        }

        # Collect Discord emojis if needed
        ds_emj_set: set[int] = set()
        if support_ds_emj:
            ds_emj_set = {
                int(node.content)
                for line in nodes_lst
                for node in line
                if node.type is NodeType.DISCORD_EMOJI
            }

        # Download all emojis concurrently
        tasks = [self._get_emoji(emoji) for emoji in emj_set]
        if support_ds_emj:
            tasks.extend([self._get_discord_emoji(eid) for eid in ds_emj_set])

        emjios = await self._gather(*tasks)

        # Build emoji mappings
        emj_num = len(emj_set)
        emj_map = dict(zip(emj_set, emjios[:emj_num]))
        ds_emj_map: dict[int, BytesIO | None] = {}
        if support_ds_emj:
            ds_emj_map = dict(zip(ds_emj_set, emjios[emj_num:]))

        # Render each line
        font_size = helper.get_font_size(font)
        y_diff = int((line_height - font_size) / 2)

        # Pre-resize emojis
        resized_emjs = {
            emoji: self._resize_emoji(bytesio, font_size)
            for emoji, bytesio in emj_map.items()
            if bytesio
        }
        resized_ds_emjs: dict[int, PILImage] = {}
        if support_ds_emj:
            resized_ds_emjs = {
                eid: self._resize_emoji(bytesio, font_size)
                for eid, bytesio in ds_emj_map.items()
                if bytesio
            }

        for line in nodes_lst:
            cur_x = x

            for node in line:
                if node.type is NodeType.EMOJI:
                    emj_img = resized_emjs.get(node.content)
                elif support_ds_emj and node.type is NodeType.DISCORD_EMOJI:
                    emj_img = resized_ds_emjs.get(int(node.content))
                else:
                    emj_img = None

                # Render emoji or text
                if emj_img is not None:
                    image.paste(emj_img, (cur_x, y + y_diff), emj_img)
                    cur_x += int(font_size)
                else:
                    draw.text((cur_x, y), node.content, font=font, fill=fill)
                    cur_x += int(font.getlength(node.content))

            y += line_height

    async def _gather(self, *tasks: Awaitable[T]) -> list[T]:
        if self.__tqdm is None:
            return await asyncio.gather(*tasks)

        return await self.__tqdm.gather(
            *tasks,
            desc="Fetching Emojis",
            colour="green",
            bar_format="{desc} |{bar}| {n_fmt}/{total_fmt}",
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"<Pilmoji source={self._source} cache={self._cache}>"
