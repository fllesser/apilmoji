from __future__ import annotations

from enum import Enum
from typing import TypeVar, overload
from asyncio import Semaphore, gather
from pathlib import Path
from collections.abc import Callable, Awaitable

from httpx import Limits, Timeout, AsyncClient
from aiofiles import open as aopen

ELK_SH_CDN = "https://emojicdn.elk.sh"
MQRIO_DEV_CDN = "https://emoji-cdn.mqrio.dev"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4098.3 Safari/537.36"
    )
}

T = TypeVar("T")


class EmojiStyle(str, Enum):
    LG = "lg"
    HTC = "htc"
    SONY = "sony"
    SKYPE = "skype"
    APPLE = "apple"
    MOZILLA = "mozilla"
    GOOGLE = "google"
    DOCOMO = "docomo"
    HUAWEI = "huawei"
    ICONS8 = "icons8"
    TWITTER = "twitter"
    OPENMOJI = "openmoji"
    SAMSUNG = "samsung"
    SOFTBANK = "softbank"
    AU_KDDI = "au-kddi"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"
    MESSENGER = "messenger"
    EMOJIDEX = "emojidex"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    TOSS_FACE = "toss-face"
    JOYPIXELS = "joypixels"
    NOTO_EMOJI = "noto-emoji"
    SERNITYOS = "serenityos"
    MICROSOFT_TEAMS = "microsoft-teams"
    JOYPIXELS_ANIMATIONS = "joypixels-animations"
    MICROSOFT_3D_FLUENT = "microsoft-3D-fluent"
    TWITTER_EMOJI_STICKERS = "twitter-emoji-stickers"
    ANIMATED_NOTO_COLOR_EMOJI = "animated-noto-color-emoji"

    def __str__(self) -> str:
        return self.value


class EmojiCDNSource:
    """Emoji source that downloads from CDN with concurrent download support."""

    def __init__(
        self,
        base_url: str = ELK_SH_CDN,
        style: EmojiStyle | str = EmojiStyle.APPLE,
        *,
        cache_dir: Path | None = None,
        show_progress: bool = False,
        max_concurrent: int = 50,
    ) -> None:
        self.base_url: str = base_url
        self.style: str = str(style)

        self._max_concurrent: int = max_concurrent
        self._semaphore: Semaphore = Semaphore(max_concurrent)

        # Setup cache directories
        self._cache_dir: Path = cache_dir or (Path.home() / ".cache" / "apilmoji")
        self._emj_dir: Path = self._cache_dir / self.style
        self._ds_dir: Path = self._cache_dir / "discord"
        self.show_progress = show_progress

    def _get_emoji_path(self, emoji: str, is_discord: bool = False) -> Path:
        """获取表情路径"""
        return (self._ds_dir if is_discord else self._emj_dir) / f"{emoji}.png"

    async def _download_emoji(
        self,
        emoji: str,
        is_discord: bool = False,
        client: AsyncClient | None = None,
    ) -> Path | None:
        """Download emoji"""
        if is_discord:
            file_name = f"{emoji}.png"
            file_path = self._ds_dir / file_name
            url = f"https://cdn.discordapp.com/emojis/{file_name}"
        else:
            file_path = self._emj_dir / f"{emoji}.png"
            url = f"{self.base_url}/{emoji}?style={self.style}"

        file_path.parent.mkdir(parents=True, exist_ok=True)

        async def download_with_stream(_client: AsyncClient) -> Path | None:
            try:
                async with _client.stream("GET", url) as response:
                    if response.status_code != 200:
                        return None

                    async with aopen(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            await f.write(chunk)

            except Exception:
                file_path.unlink(missing_ok=True)
                return None
            return file_path

        if client is None:
            async with AsyncClient(headers=HEADERS) as client:
                return await download_with_stream(client)

        return await download_with_stream(client)

    async def get_emoji(self, emoji: str) -> Path | None:
        """Get a single emoji image."""
        path = self._get_emoji_path(emoji)
        return path if path.exists() else await self._download_emoji(emoji)

    async def get_discord_emoji(self, id: str) -> Path | None:
        """Get a single Discord emoji image."""
        path = self._get_emoji_path(id, True)
        return path if path.exists() else await self._download_emoji(id, True)

    async def _fetch_with_semaphore(
        self,
        emoji: str,
        is_discord: bool = False,
        client: AsyncClient | None = None,
    ) -> Path | None:
        """Fetch a single emoji with semaphore-based concurrency control."""
        async with self._semaphore:
            return await self._download_emoji(
                emoji,
                client=client,
                is_discord=is_discord,
            )

    async def __gather_emojis(
        self, *tasks: Awaitable[Path | None]
    ) -> list[Path | None]:
        """Gather emoji download tasks with optional rich progress bar."""
        if not self.show_progress:
            return await gather(*tasks)

        completed_count = 0
        total_count = len(tasks)

        async def track_task(
            task: Awaitable[Path | None], progress, task_id
        ) -> Path | None:
            nonlocal completed_count
            result = await task
            progress.update(task_id, advance=1)
            return result

        from rich.progress import (
            Progress,
            BarColumn,
            TextColumn,
            TimeRemainingColumn,
        )

        with Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("{task.completed}/{task.total}"),
            "•",
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("Fetching Emojis", total=total_count)
            # Wrap all tasks to update progress
            tracked_tasks = [track_task(t, progress, task_id) for t in tasks]
            return await gather(*tracked_tasks)

    @overload
    async def fetch_emojis(
        self,
        emojis: set[str],
        discord_emojis: set[str] | None = None,
    ) -> dict[str, Path | None]: ...

    @overload
    async def fetch_emojis(
        self,
        emojis: set[str],
        discord_emojis: set[str] | None = None,
        *,
        post_process: Callable[[Path], T],
    ) -> dict[str, T | None]: ...

    async def fetch_emojis(
        self,
        emojis: set[str],
        discord_emojis: set[str] | None = None,
        *,
        post_process: Callable[[Path], T] | None = None,
    ):
        """Fetch multiple emojis concurrently."""
        discord_emojis = discord_emojis or set()

        emoji_map: dict[str, Path | None] = {}
        emoji_list: list[str] = []
        discord_emoji_list: list[str] = []

        for emoji in emojis:
            path = self._get_emoji_path(emoji)
            if path.exists():
                emoji_map[emoji] = path
            else:
                emoji_list.append(emoji)

        for eid in discord_emojis:
            path = self._get_emoji_path(eid, True)
            if path.exists():
                emoji_map[eid] = path
            else:
                discord_emoji_list.append(eid)

        if not emoji_list and not discord_emoji_list:
            if not post_process:
                return emoji_map
        else:
            # Create shared HTTP client for all downloads
            async with AsyncClient(
                headers=HEADERS,
                timeout=Timeout(connect=5, read=20, write=15, pool=15),
                limits=Limits(
                    max_connections=self._max_concurrent + 10,
                    max_keepalive_connections=self._max_concurrent,
                ),
            ) as client:
                # Create download tasks using the same list order
                tasks = [
                    self._fetch_with_semaphore(emoji, client=client)
                    for emoji in emoji_list
                ]
                ds_tasks = [
                    self._fetch_with_semaphore(eid, True, client)
                    for eid in discord_emoji_list
                ]
                tasks.extend(ds_tasks)

                # Download all concurrently
                download_results = await self.__gather_emojis(*tasks)

            # Combine all emojis into a single dict using the same list order
            emoji_map.update(zip(emoji_list + discord_emoji_list, download_results))

        if post_process:
            return {
                k: post_process(v) if v is not None else None
                for k, v in emoji_map.items()
            }
        return emoji_map
