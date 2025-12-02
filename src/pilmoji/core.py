import asyncio
from io import BytesIO
from typing import SupportsInt

from PIL import Image, ImageDraw

from .source import BaseSource, EmojiCDNSource, HTTPBasedSource
from .helpers import FontT, ColorT, NodeType, to_nodes, get_font_size

__all__ = ("Pilmoji",)


class Pilmoji:
    """The emoji rendering interface."""

    def __init__(
        self,
        *,
        source: BaseSource = EmojiCDNSource(),
        cache: bool = True,
        emoji_scale_factor: float = 1.0,
        emoji_position_offset: tuple[int, int] = (0, 0),
    ) -> None:
        self._cache: bool = cache
        self._closed: bool = False
        self._new_draw: bool = False
        self.source: BaseSource = source

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

    def _render_text(
        self,
        draw: ImageDraw.ImageDraw,
        pos: tuple[int, int],
        content: str,
        font: FontT,
        fill: ColorT | None,
    ) -> int:
        """渲染文本节点，返回占用的宽度"""
        draw.text(pos, content, font=font, fill=fill)
        return int(font.getlength(content))

    def _render_emoji(
        self,
        image: Image.Image,
        pos: tuple[int, int],
        stream: BytesIO,
        font_size: float,
    ) -> int:
        """渲染 emoji 节点，返回占用的宽度"""
        stream.seek(0)
        with Image.open(stream).convert("RGBA") as emoji_img:
            emoji_size = int(font_size)
            aspect_ratio = emoji_img.height / emoji_img.width
            resized = emoji_img.resize(
                (emoji_size, int(emoji_size * aspect_ratio)),
                Image.Resampling.LANCZOS,
            )
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
        """简化版的文本渲染方法，支持 Unicode emoji。

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

        # 解析文本为节点（只识别 Unicode emoji）
        lines = to_nodes(text)

        # 收集所有需要下载的 Unicode emoji（去重）
        emoji_set = {node.content for line in lines for node in line if node.type is NodeType.emoji}

        # 并发下载所有 emoji
        emoji_tasks = [self._get_emoji(emoji) for emoji in emoji_set]

        if emoji_tasks:
            emoji_results = await asyncio.gather(*emoji_tasks)
            emoji_map = dict(zip(emoji_set, emoji_results))
        else:
            emoji_map = {}

        # 渲染每一行
        font_size = get_font_size(font)
        line_height = int(font_size * 1.2)  # 行高为字体大小的 1.2 倍

        for line in lines:
            cur_x = x

            for node in line:
                if node.type is NodeType.emoji:
                    stream = emoji_map.get(node.content)
                    if stream:
                        cur_x += self._render_emoji(image, (cur_x, y), stream, font_size)
                    else:
                        cur_x += self._render_text(draw, (cur_x, y), node.content, font, fill)
                else:
                    # 文本节点或 Discord emoji（作为文本渲染）
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
        """简化版的文本渲染方法，支持 Unicode emoji 和 Discord emoji。

        这个方法提供了更简单直接的实现，去掉了复杂的排版参数。
        适合需要渲染 Discord emoji 的场景使用。

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
        lines = to_nodes(text, False)

        # 收集所有需要下载的 emoji（去重）
        emoji_set = {node.content for line in lines for node in line if node.type is NodeType.emoji}

        discord_emoji_set = {
            int(node.content) for line in lines for node in line if node.type is NodeType.discord_emoji
        }

        # 并发下载所有 emoji
        emoji_tasks = [self._get_emoji(emoji) for emoji in emoji_set]
        discord_tasks = [self._get_discord_emoji(eid) for eid in discord_emoji_set]

        if emoji_tasks or discord_tasks:
            results = await asyncio.gather(*emoji_tasks, *discord_tasks)
            emoji_results = results[: len(emoji_tasks)]
            discord_results = results[len(emoji_tasks) :]

            # 建立映射
            emoji_map = dict(zip(emoji_set, emoji_results))
            discord_map = dict(zip(discord_emoji_set, discord_results))
        else:
            emoji_map = {}
            discord_map = {}

        # 渲染每一行
        font_size = get_font_size(font)
        line_height = int(font_size * 1.2)  # 行高为字体大小的 1.2 倍

        for line in lines:
            cur_x = x

            for node in line:
                stream = None
                fallback_text = node.content

                if node.type is NodeType.emoji:
                    stream = emoji_map.get(node.content)
                elif node.type is NodeType.discord_emoji:
                    stream = discord_map.get(int(node.content))
                    if not stream:
                        fallback_text = f"[:{node.content}:]"

                # 渲染 emoji 或文本
                if stream:
                    cur_x += self._render_emoji(image, (cur_x, y), stream, font_size)
                else:
                    cur_x += self._render_text(draw, (cur_x, y), fallback_text, font, fill)

            y += line_height

    async def __aenter__(self):
        if isinstance(self.source, HTTPBasedSource):
            await self.source.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return f"<Pilmoji source={self.source} cache={self._cache}>"
