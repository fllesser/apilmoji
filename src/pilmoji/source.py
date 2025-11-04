from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from pathlib import Path
from urllib.parse import quote_plus

from aiofiles import open as aopen
from emoji import EMOJI_DATA
from httpx import AsyncClient, HTTPError

__all__ = (
    "BaseSource",
    "DiscordEmojiSourceMixin",
    "EmojiCDNSource",
    "HTTPBasedSource",
)


class BaseSource(ABC):
    """The base class for an emoji image source."""

    @abstractmethod
    async def get_emoji(self, emoji: str) -> BytesIO | None:
        """Retrieves a :class:`io.BytesIO` stream for the image of the given emoji.

        Parameters
        ----------
        emoji: str
            The emoji to retrieve.

        Returns
        -------
        :class:`io.BytesIO`
            A bytes stream of the emoji.
        None
            An image for the emoji could not be found.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_discord_emoji(self, id: int) -> BytesIO | None:
        """Retrieves a :class:`io.BytesIO` stream for the image of the given Discord emoji.

        Parameters
        ----------
        id: int
            The snowflake ID of the Discord emoji.

        Returns
        -------
        :class:`io.BytesIO`
            A bytes stream of the emoji.
        None
            An image for the emoji could not be found.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class HTTPBasedSource(BaseSource):
    """Represents an HTTP-based source."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir: Path = cache_dir or (Path.home() / ".cache" / "pilmoji")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = AsyncClient(headers={"User-Agent": "Mozilla/5.0"})

    async def download(self, url: str) -> bytes:
        response = await self.client.get(url)
        response.raise_for_status()
        return response.content


class EmojiStyle(str, Enum):
    APPLE = "apple"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    SAMSUNG = "samsung"
    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    MESSENGER = "messenger"
    JOYPIXELS = "joypixels"
    OPENMOJI = "openmoji"
    EMOJIDEX = "emojidex"
    MOZILLA = "mozilla"
    TWEMOJI = "twemoji"

    def __str__(self) -> str:
        return self.value


class LocalEmojiSource:
    def __init__(self, style: EmojiStyle, cache_dir: Path | None = None) -> None:
        self.style = style.value
        self.cache_dir: Path = cache_dir or Path.home() / ".cache" / "pilmoji"

    async def download_all_emojis(self) -> None:
        from asyncio import create_task, gather

        async def download_emoji(client: AsyncClient, emj: str) -> None:
            file_path = self.cache_dir / self.style / f"{emj}.png"
            if file_path.exists():
                return
            url = f"https://emojicdn.elk.sh/{quote_plus(emj)}?style={self.style}"
            response = await client.get(url)
            response.raise_for_status()
            async with aopen(file_path, "wb") as f:
                await f.write(response.content)

        async with AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
            tasks = [create_task(download_emoji(client, emj)) for emj, _ in EMOJI_DATA.items()]
            await gather(*tasks, return_exceptions=True)

    def get_emoji(self, emoji: str) -> BytesIO | None:
        return BytesIO(open(self.cache_dir / self.style / f"{emoji}.png", "rb").read())

    def get_discord_emoji(self, id: int) -> BytesIO | None:
        return BytesIO(open(self.cache_dir / "discord" / f"{id}.png", "rb").read())


class DiscordEmojiSourceMixin(HTTPBasedSource):
    """A mixin that adds Discord emoji functionality to another source."""

    def __post_init__(self):
        (self.cache_dir / "discord").mkdir(parents=True, exist_ok=True)

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


class EmojiCDNSource(DiscordEmojiSourceMixin):
    """A base source that fetches emojis from https://emojicdn.elk.sh/."""

    def __init__(self, style: EmojiStyle = EmojiStyle.APPLE, cache_dir: Path | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        self.style = style.value

    async def get_emoji(self, emoji: str) -> BytesIO | None:
        file_path = self.cache_dir / self.style / f"{emoji}.png"
        if file_path.exists():
            async with aopen(file_path, "rb") as f:
                return BytesIO(await f.read())

        url = f"https://emojicdn.elk.sh/emoji?style={self.style}"

        try:
            bytes = await self.download(url)
            async with aopen(file_path, "wb") as f:
                await f.write(bytes)
            return BytesIO(bytes)
        except HTTPError:
            return None
