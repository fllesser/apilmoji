import pytest

COMPLEX_TEXT = [
    "Hello World! 👋",
    "This is a complex test text with multiple lines",
    "We have standard emojis: 😂, 🚀, 🐍, 💻.",
    "And some more: 🌟✨🔥💯.",
    "Even some text in between: A B C 1 2 3.",
    "Discord emojis are also supported <:rooThink:596576798351949847>",
]


@pytest.mark.asyncio
async def test_pilmoji(font_path, cache_dir):
    from PIL import Image, ImageFont

    from apilmoji import Apilmoji, EmojiCDNSource

    font = ImageFont.truetype(font_path, 24)
    source = EmojiCDNSource(cache_dir=cache_dir)
    with Image.new("RGB", (300, 200), (255, 255, 255)) as image:
        for y in range(10, 170, 30):
            await Apilmoji.text(
                image,
                (10, y),
                ["Hello👍world😎"],
                font,
                fill=(0, 0, 0),
                source=source,
            )
        image.save(cache_dir / "test_pilmoji.png")


@pytest.mark.asyncio
async def test_text(font_path, cache_dir):
    from PIL import Image, ImageFont

    from apilmoji import Apilmoji, EmojiCDNSource

    font = ImageFont.truetype(font_path, 24)
    source = EmojiCDNSource(cache_dir=cache_dir)
    with Image.new("RGB", (800, 300), (255, 255, 255)) as image:
        await Apilmoji.text(
            image,
            (10, 40),
            COMPLEX_TEXT,
            font,
            fill=(0, 0, 0),
            source=source,
        )
        image.save(cache_dir / "text.png")


@pytest.mark.asyncio
async def test_text_with_discord_emoji(font_path, cache_dir):
    from PIL import Image, ImageFont

    from apilmoji import Apilmoji, EmojiCDNSource

    font = ImageFont.truetype(font_path, 24)
    source = EmojiCDNSource(cache_dir=cache_dir)
    with Image.new("RGB", (600, 300), (255, 255, 255)) as image:
        await Apilmoji.text(
            image,
            (10, 40),
            COMPLEX_TEXT,
            font,
            fill=(0, 0, 0),
            support_ds_emj=True,
            source=source,
        )
        await Apilmoji.text(
            image,
            (10, 10),
            ["<:rooThink:596576798351949847>"],
            font,
            fill=(0, 0, 0),
            support_ds_emj=True,
            source=source,
        )
        image.save(cache_dir / "text_with_ds_emj.png")


@pytest.mark.asyncio
async def test_edge_case(font_path, cache_dir):
    from PIL import Image, ImageFont

    from apilmoji import Apilmoji, EmojiCDNSource

    font = ImageFont.truetype(font_path, 24)
    source = EmojiCDNSource(cache_dir=cache_dir)
    with Image.new("RGB", (300, 200), (255, 255, 255)) as image:
        await Apilmoji.text(image, (10, 10), [""], font, fill=(0, 0, 0), source=source)
        await Apilmoji.text(
            image, (10, 40), "Hello World!", font, fill=(0, 0, 0), source=source
        )
        await Apilmoji.text(
            image,
            (10, 70),
            "",
            font,
            fill=(0, 0, 0),
            source=source,
        )
        await Apilmoji.text(
            image,
            (10, 100),
            "Hello World!",
            font,
            fill=(0, 0, 0),
            source=source,
        )
        image.save(cache_dir / "text_with_edge_case.png")


@pytest.mark.asyncio
async def test_text_with_transposed_font(font_path, cache_dir):
    from PIL import Image, ImageFont

    from apilmoji import Apilmoji, EmojiCDNSource

    font = ImageFont.truetype(font_path, 24)
    # 上下翻转字体
    font = ImageFont.TransposedFont(font, Image.Transpose.ROTATE_180)
    source = EmojiCDNSource(cache_dir=cache_dir)
    with Image.new("RGB", (600, 300), (255, 255, 255)) as image:
        await Apilmoji.text(
            image,
            (10, 40),
            COMPLEX_TEXT,
            font,
            fill=(0, 0, 0),
            support_ds_emj=True,
            source=source,
        )
        image.save(cache_dir / "text_with_transposed_font.png")


@pytest.mark.xfail(strict=True)
def test_get_font_height_with_imagefont():
    from PIL import ImageFont

    from apilmoji import Apilmoji

    font = ImageFont.load_default_imagefont()
    Apilmoji.get_font_height(font)


@pytest.mark.xfail(strict=True)
def test_get_font_size_with_imagefont():
    from PIL import ImageFont

    from apilmoji import Apilmoji

    font = ImageFont.load_default_imagefont()
    Apilmoji.get_font_size(font)
