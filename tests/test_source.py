import pytest


@pytest.mark.asyncio
async def test_get_emoji_from_cdn(cache_dir):
    from apilmoji import EmojiCDNSource

    emoji_str = "👍 😎 😊 😍 😘 😗 😙 😚 😋"
    emoji_list = emoji_str.split(" ")

    source = EmojiCDNSource(cache_dir=cache_dir)

    for emoji in emoji_list:
        image = await source.get_emoji(emoji)
        assert image is not None
    # test cache
    for emoji in emoji_list:
        image = await source.get_emoji(emoji)
        assert image is not None


@pytest.mark.asyncio
async def test_get_discord_emoji_from_cdn(cache_dir):
    from apilmoji import EmojiCDNSource

    discord_emoji_id = "596576798351949847"
    source = EmojiCDNSource(cache_dir=cache_dir)

    image = await source.get_discord_emoji(discord_emoji_id)
    assert image is not None
    # test cache
    image = await source.get_discord_emoji(discord_emoji_id)
    assert image is not None


@pytest.mark.asyncio
async def test_all_style(cache_dir):
    import asyncio

    from apilmoji import EmojiStyle, EmojiCDNSource

    emoji_str = "👍"

    assert str(EmojiStyle.APPLE) == "apple"
    assert str(EmojiStyle.GOOGLE) == "google"
    assert str(EmojiStyle.TWITTER) == "twitter"
    assert str(EmojiStyle.FACEBOOK) == "facebook"

    async def test_style(style: EmojiStyle):
        source = EmojiCDNSource(cache_dir=cache_dir, style=style)
        image = await source.get_emoji(emoji_str)
        assert image is not None, f"Failed to get emoji for style {style}"

    styles = (
        EmojiStyle.APPLE,
        EmojiStyle.FACEBOOK,
        EmojiStyle.TWITTER,
        EmojiStyle.GOOGLE,
    )

    await asyncio.gather(*[test_style(style) for style in styles])
