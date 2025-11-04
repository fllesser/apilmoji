from pathlib import Path


def test_dummy():
    assert True


cache_dir = Path() / ".cache"


async def test_get_emoji_from_cdn():
    from pilmoji import EmojiCDNSource

    source = EmojiCDNSource(cache_dir=cache_dir / "emoji")

    emoji = "👍"
    image = await source.get_emoji(emoji)
    assert image is not None


async def test_pilmoji():
    from PIL import Image, ImageFont

    from pilmoji import Pilmoji

    image = Image.new("RGB", (100, 100), (255, 255, 255))
    font = ImageFont.load_default()

    async with Pilmoji(image) as pilmoji:
        assert isinstance(font, ImageFont.FreeTypeFont)
        await pilmoji.text((10, 10), "Hello, world 👍 😎 !", font, (0, 0, 0))

    assert image is not None
    image.save(cache_dir / "test_pilmoji.png")
