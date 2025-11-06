from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from pathlib import Path

from aiofiles import open as aopen
from httpx import AsyncClient, HTTPError

__all__ = (
    "BaseSource",
    "EmojiCDNSource",
    "HTTPBasedSource",
)


class BaseSource(ABC):
    """The base class for an emoji image source."""

    @abstractmethod
    async def get_emoji(self, emoji: str) -> BytesIO | None:
        """Retrieves a :class:`io.BytesIO` stream for the image of the given emoji.

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
        """Retrieves a :class:`io.BytesIO` stream for the image of the given Discord emoji.

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

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir: Path = cache_dir or (Path.home() / ".cache" / "pilmoji")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download(self, url: str) -> bytes:
        """Downloads the image from the given URL.

        Args:
            url (str): The URL to download the image from.

        Returns:
            bytes: The image content.
        """
        response = await self._client.get(url)
        response.raise_for_status()
        return response.content

    async def __aenter__(self):
        self._client = AsyncClient(headers={"User-Agent": "Mozilla/5.0"})
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)


class EmojiStyle(str, Enum):
    APPLE = "apple"
    GOOGLE = "google"
    TWITTER = "twitter"
    FACEBOOK = "facebook"

    def __str__(self) -> str:
        return self.value


class EmojiCDNSource(HTTPBasedSource):
    """A base source that fetches emojis from https://emojicdn.elk.sh/."""

    def __init__(self, style: EmojiStyle = EmojiStyle.APPLE, cache_dir: Path | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        self.style = style.value
        (self.cache_dir / self.style).mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "discord").mkdir(parents=True, exist_ok=True)

    async def get_emoji(self, emoji: str) -> BytesIO | None:
        file_path = self.cache_dir / self.style / f"{emoji}.png"
        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        url = f"https://emojicdn.elk.sh/{emoji}?style={self.style}"

        try:
            bytes = await self.download(url)
            async with aopen(file_path, "wb") as f:
                await f.write(bytes)
            return BytesIO(bytes)
        except HTTPError:
            return None

    async def get_discord_emoji(self, id: int) -> BytesIO | None:
        file_name = f"{id}.png"
        file_path = self.cache_dir / "discord" / file_name
        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        url = f"https://cdn.discordapp.com/emojis/{file_name}"

        try:
            bytes = await self.download(url)
            async with aopen(file_path, "wb") as f:
                await f.write(bytes)
            return BytesIO(bytes)
        except HTTPError:
            return None
