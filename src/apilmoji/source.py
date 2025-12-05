from io import BytesIO
from enum import Enum
from asyncio import Semaphore, gather, create_task
from pathlib import Path
from collections.abc import Awaitable

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
        enable_discord: bool = False,
        max_concurrent: int = 50,
        enable_tqdm: bool = False,
    ) -> None:
        self.base_url = base_url
        self.style = str(style)
        self._max_concurrent = max_concurrent
        self._semaphore = Semaphore(max_concurrent)

        # Setup cache directories
        self._cache_dir: Path = cache_dir or (Path.home() / ".cache" / "apilmoji")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self._emj_dir = self._cache_dir / self.style
        self._emj_dir.mkdir(parents=True, exist_ok=True)

        self._ds_dir = self._cache_dir / "discord"
        if enable_discord:
            self._ds_dir.mkdir(parents=True, exist_ok=True)

        # Setup tqdm if enabled
        self.__tqdm = None
        if enable_tqdm:
            try:
                from tqdm.asyncio import tqdm

                self.__tqdm = tqdm
            except ImportError:
                pass

    async def _download_emoji(
        self,
        emoji: str,
        *,
        is_discord: bool = False,
        client: AsyncClient | None = None,
    ) -> BytesIO | None:
        """内部下载方法"""
        if is_discord:
            file_name = f"{emoji}.png"
            file_path = self._ds_dir / file_name
            url = f"https://cdn.discordapp.com/emojis/{file_name}"
        else:
            file_path = self._emj_dir / f"{emoji}.png"
            url = f"{self.base_url}/{emoji}?style={self.style}"

        # 检查缓存
        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        async def download_with_stream(_client: AsyncClient) -> BytesIO | None:
            async with _client.stream("GET", url) as response:
                if response.status_code != 200:
                    return None

                buffer = BytesIO()
                async with aopen(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)
                        buffer.write(chunk)

                buffer.seek(0)
                return buffer

        if client is None:
            async with AsyncClient(headers=HEADERS) as client:
                return await download_with_stream(client)

        return await download_with_stream(client)

    async def get_emoji(self, emoji: str) -> BytesIO | None:
        """Get a single emoji image.

        Args:
            emoji: The emoji character to retrieve

        Returns:
            BytesIO containing the emoji image, or None if download fails
        """

        return await self._download_emoji(emoji)

    async def get_discord_emoji(self, id: str) -> BytesIO | None:
        """Get a single Discord emoji image.

        Args:
            id: The Discord emoji ID

        Returns:
            BytesIO containing the emoji image, or None if download fails
        """
        return await self._download_emoji(id, is_discord=True)

    async def _fetch_with_semaphore(
        self,
        emoji: str,
        *,
        is_discord: bool = False,
        client: AsyncClient,
    ) -> BytesIO | None:
        """Fetch a single emoji with semaphore-based concurrency control."""
        async with self._semaphore:
            try:
                return await self._download_emoji(
                    emoji,
                    client=client,
                    is_discord=is_discord,
                )
            except Exception:
                return None

    async def __gather_emojis(
        self, *tasks: Awaitable[BytesIO | None]
    ) -> list[BytesIO | None]:
        """Gather emoji download tasks with optional tqdm progress bar."""
        if self.__tqdm is None:
            return await gather(*tasks)

        return await self.__tqdm.gather(
            *tasks,
            desc="Fetching Emojis",
            colour="green",
            dynamic_ncols=True,
        )

    async def fetch_emojis(
        self,
        emojis: set[str],
        discord_emojis: set[str] | None = None,
    ) -> dict[str, BytesIO | None]:
        """Fetch multiple emojis concurrently.

        Args:
            emojis: Set of emoji characters to download
            discord_emojis: Optional set of Discord emoji IDs to download

        Returns:
            Dictionary mapping emoji/id -> BytesIO or None
        """
        discord_emojis = discord_emojis or set()

        # Convert sets to lists once to maintain consistent ordering
        emoji_list = list(emojis)
        discord_emoji_list = list(discord_emojis)

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
                create_task(self._fetch_with_semaphore(emoji, client=client))
                for emoji in emoji_list
            ]
            tasks.extend(
                [
                    create_task(
                        self._fetch_with_semaphore(eid, is_discord=True, client=client)
                    )
                    for eid in discord_emoji_list
                ]
            )

            # Download all concurrently
            results = await self.__gather_emojis(*tasks)

        # Combine all emojis into a single dict using the same list order
        all_emojis = emoji_list + discord_emoji_list
        return dict(zip(all_emojis, results))

    def __repr__(self) -> str:
        return f"<EmojiCDNSource style={self.style}>"
