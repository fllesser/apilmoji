from pathlib import Path

import pytest

cache_dir = Path() / ".cache"
font_path = Path(__file__).parent / "resource" / "HYSongYunLangHeiW-1.ttf"


def clean_dir(path: Path):
    if not path.exists():
        return
    for fd in path.glob("*"):
        if fd.is_dir():
            clean_dir(fd)
            fd.rmdir()
        else:
            fd.unlink()


# 执行前清除缓存
@pytest.fixture(autouse=True)
def clean_cache_dir():
    cache_dir.mkdir(parents=True, exist_ok=True)
    clean_dir(cache_dir)


@pytest.mark.asyncio
async def test_get_emoji_from_cdn():
    from pilmoji import EmojiCDNSource

    emoji_str = "👍 😎 😊 😍 😘 😗 😙 😚 😋"
    emoji_list = emoji_str.split(" ")

    async with EmojiCDNSource(cache_dir=cache_dir) as source:
        for emoji in emoji_list:
            image = await source.get_emoji(emoji)
            assert image is not None
        # test cache
        for emoji in emoji_list:
            image = await source.get_emoji(emoji)
            assert image is not None


@pytest.mark.asyncio
async def test_get_discord_emoji_from_cdn():
    from pilmoji import EmojiCDNSource

    discord_emoji_id = 596576798351949847
    async with EmojiCDNSource(cache_dir=cache_dir) as source:
        image = await source.get_discord_emoji(discord_emoji_id)
        assert image is not None
        # test cache
        image = await source.get_discord_emoji(discord_emoji_id)
        assert image is not None


@pytest.mark.asyncio
async def test_all_style():
    from pilmoji import EmojiCDNSource, EmojiStyle

    emoji_str = "👍"
    for style in EmojiStyle:
        async with EmojiCDNSource(cache_dir=cache_dir, style=style) as source:
            image = await source.get_emoji(emoji_str)
            assert image is not None


@pytest.mark.asyncio
async def test_pilmoji():
    from PIL import Image, ImageFont

    from pilmoji import EmojiCDNSource, Pilmoji

    font = ImageFont.truetype(font_path, 24)
    async with Pilmoji(source=EmojiCDNSource(cache_dir=cache_dir)) as pilmoji:
        image = Image.new("RGB", (300, 200), (255, 255, 255))
        for y in range(10, 170, 30):
            await pilmoji.text(image, (10, y), "Hello 👍 world 😎", font, (0, 0, 0))

        assert image is not None
        image.save(cache_dir / "test_pilmoji.png")


@pytest.mark.asyncio
async def test_pilmoji_multiline():
    from PIL import Image, ImageFont

    from pilmoji import EmojiCDNSource, Pilmoji

    my_string = (
        "Hello, world! 👋 Here are some emojis: 🎨 🌊 😎\nI also support Discord emoji: <:rooThink:596576798351949847>"
    )

    font = ImageFont.truetype(font_path, 24)
    async with Pilmoji(source=EmojiCDNSource(cache_dir=cache_dir)) as pilmoji:
        image = Image.new("RGB", (500, 200), (255, 255, 255))
        await pilmoji.text(image, (10, 10), my_string, font, (0, 0, 0))
        assert image is not None
        image.save(cache_dir / "test_pilmoji_multiline.png")


@pytest.mark.asyncio
async def test_source_without_context_manager():
    from pilmoji import EmojiCDNSource

    source = EmojiCDNSource(cache_dir=cache_dir)

    try:
        image = await source.get_emoji("👍")
        assert image is not None
    finally:
        await source.aclose()


@pytest.mark.asyncio
async def test_pilmoji_without_context_manager():
    from PIL import Image, ImageFont

    from pilmoji import EmojiCDNSource, Pilmoji

    font = ImageFont.truetype(font_path, 24)
    source = EmojiCDNSource(cache_dir=cache_dir)
    pilmoji = Pilmoji(source=source)

    try:
        image = Image.new("RGB", (300, 200), (255, 255, 255))
        for y in range(10, 170, 30):
            await pilmoji.text(image, (10, y), "Hello 👍 world 😎", font, (0, 0, 0))

        assert image is not None
    finally:
        await pilmoji.aclose()
