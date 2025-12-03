from io import BytesIO
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from httpx import HTTPError, AsyncClient
from aiofiles import open as aopen


class BaseSource(ABC):
    """The base class for an emoji image source."""

    @abstractmethod
    async def get_emoji(self, emoji: str) -> BytesIO | None:
        """Get the image of the emoji with the given name.

        Args:
            emoji (str): The emoji to retrieve.

        Raises:
            NotImplementedError: The method is not implemented.

        Returns:
            BytesIO | None: A bytes stream of the emoji.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_discord_emoji(self, id: int) -> BytesIO | None:
        """Get the image of the Discord emoji with the given ID.

        Args:
            id (int): The snowflake ID of the Discord emoji.

        Raises:
            NotImplementedError: The method is not implemented.

        Returns:
            BytesIO | None: A bytes stream of the emoji.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class HTTPBasedSource(BaseSource):
    """Represents an HTTP-based source."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        enable_discord: bool = False,
    ):
        self._cache_dir: Path = cache_dir or (Path.home() / ".cache" / "pilmoji")
        self._client = AsyncClient(headers={"User-Agent": "Mozilla/5.0"})

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._ds_dir = self._cache_dir / "discord"
        if enable_discord:
            self._ds_dir.mkdir(parents=True, exist_ok=True)

    async def download_streaming(self, url: str, file_path: Path) -> BytesIO:
        """Downloads the image from the given URL using streaming,
        writing to both file and BytesIO simultaneously.

        Args:
            url (str): The URL to download the image from.
            file_path (Path): The path to save the file to.

        Returns:
            BytesIO: A bytes stream of the downloaded content.
        """
        async with self._client.stream("GET", url) as response:
            response.raise_for_status()
            buffer = BytesIO()

            async with aopen(file_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    await f.write(chunk)
                    buffer.write(chunk)

            buffer.seek(0)
            return buffer

    async def aclose(self) -> None:
        """Closes the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    async def get_discord_emoji(self, id: int) -> BytesIO | None:
        file_name = f"{id}.png"
        file_path = self._ds_dir / file_name
        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        url = f"https://cdn.discordapp.com/emojis/{file_name}"

        try:
            return await self.download_streaming(url, file_path)
        except HTTPError:
            return None


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


ELK_SH_CDN = "https://emojicdn.elk.sh"
MQRIO_DEV_CDN = "https://emoji-cdn.mqrio.dev"


class EmojiCDNSource(HTTPBasedSource):
    def __init__(
        self,
        base_url: str = ELK_SH_CDN,
        style: EmojiStyle | str = EmojiStyle.APPLE,
        *,
        cache_dir: Path | None = None,
        enable_discord: bool = False,
    ) -> None:
        super().__init__(cache_dir, enable_discord)
        self.base_url = base_url
        self.style = str(style)

        self._emj_dir = self._cache_dir / self.style
        self._emj_dir.mkdir(parents=True, exist_ok=True)

    async def get_emoji(self, emoji: str) -> BytesIO | None:
        file_path = self._emj_dir / f"{emoji}.png"

        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        url = f"{self.base_url}/{emoji}?style={self.style}"

        try:
            return await self.download_streaming(url, file_path)
        except HTTPError:
            return None
