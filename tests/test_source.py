import pytest


@pytest.mark.asyncio
async def test_get_emoji_from_cdn(cache_dir):
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
async def test_get_discord_emoji_from_cdn(cache_dir):
    from pilmoji import EmojiCDNSource

    discord_emoji_id = 596576798351949847
    async with EmojiCDNSource(cache_dir=cache_dir) as source:
        image = await source.get_discord_emoji(discord_emoji_id)
        assert image is not None
        # test cache
        image = await source.get_discord_emoji(discord_emoji_id)
        assert image is not None


@pytest.mark.asyncio
async def test_all_style(cache_dir):
    import asyncio

    from pilmoji import EmojiStyle, EmojiCDNSource

    emoji_str = "👍"

    assert str(EmojiStyle.APPLE) == "apple"
    assert str(EmojiStyle.GOOGLE) == "google"
    assert str(EmojiStyle.TWITTER) == "twitter"
    assert str(EmojiStyle.FACEBOOK) == "facebook"

    async def test_style(style: EmojiStyle):
        async with EmojiCDNSource(cache_dir=cache_dir, style=style) as source:
            image = await source.get_emoji(emoji_str)
            assert image is not None, f"Failed to get emoji for style {style}"

    styles = (
        EmojiStyle.APPLE,
        EmojiStyle.FACEBOOK,
        EmojiStyle.TWITTER,
        EmojiStyle.GOOGLE,
    )

    await asyncio.gather(*[test_style(style) for style in styles])


@pytest.mark.asyncio
async def test_source_without_context_manager(cache_dir):
    from pilmoji import EmojiCDNSource

    source = EmojiCDNSource(cache_dir=cache_dir)

    try:
        image = await source.get_emoji("👍")
        assert image is not None
    finally:
        await source.aclose()
