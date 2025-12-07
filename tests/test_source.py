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
async def test_elk_cdn_style(cache_dir):
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


@pytest.mark.asyncio
async def test_all_styles(cache_dir):
    import asyncio

    from apilmoji import MQRIO_DEV_CDN, EmojiStyle, EmojiCDNSource

    text = "👍"

    async def test_style(style: EmojiStyle):
        source = EmojiCDNSource(
            base_url=MQRIO_DEV_CDN, cache_dir=cache_dir, style=style
        )
        image = await source.get_emoji(text)
        if image is None:
            raise ValueError(f"Failed to get emoji for style {style}")

    results = await asyncio.gather(
        *[test_style(style) for style in EmojiStyle], return_exceptions=True
    )

    exceptions = [repr(e) for e in results if isinstance(e, ValueError)]
    if exceptions:
        pytest.skip("\n".join(exceptions))


@pytest.mark.asyncio
async def test_tqdm(cache_dir):
    from apilmoji import EmojiCDNSource

    emoji_str = "👍 😎 😊 😍 😘 😗 😙 😚 😋"
    emoji_list = emoji_str.split(" ")

    source = EmojiCDNSource(cache_dir=cache_dir, enable_tqdm=True)
    await source.fetch_emojis(set(emoji_list))


@pytest.mark.asyncio
async def test_fetch_emojis(cache_dir):
    from apilmoji import EmojiCDNSource

    emoji_set = {"👍", "😎", "😊", "😍", "😘", "😗", "😙", "😚", "😋"}
    discord_emoji_set = {"596576798351949847"}

    count = len(emoji_set) + len(discord_emoji_set)
    source = EmojiCDNSource(cache_dir=cache_dir, enable_tqdm=True)
    first_result = await source.fetch_emojis(emoji_set, discord_emoji_set)
    assert len(first_result) == count
    second_result = await source.fetch_emojis(emoji_set, discord_emoji_set)
    assert len(second_result) == count
