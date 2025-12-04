# Pilmoji for Parser

A simplified emoji renderer for [Pillow](https://github.com/python-pillow/Pillow/), Python's imaging library. This is a streamlined fork optimized for use with [nonebot-plugin-parser](https://github.com/fllesser/nonebot-plugin-parser).

## ✨ Features

- 🎨 **Unicode Emoji Support** - Render standard Unicode emojis
- 💬 **Discord Emoji Support** - Render custom Discord emojis
- 📝 **Multi-line Text** - Automatic line break handling
- 🎭 **Multiple Emoji Styles** - Apple, Google, Twitter, Facebook
- ⚡ **Async/Await** - Built with modern async Python
- 💾 **Smart Caching** - Local file caching for better performance
- 🔧 **Simple API** - Easy-to-use interface with sensible defaults

## 📦 Installation

**Requirements:** Python 3.10 or higher

```bash
pip install apilmoji
```

Or install from source:

```bash
git clone https://github.com/fllesser/apilmoji.git
cd apilmoji
pip install .
```

## 🚀 Quick Start

### Basic Usage (Unicode Emoji Only)

```python
import asyncio
from pilmoji import Pilmoji
from PIL import Image, ImageFont

async def main():
    text = '''
    Hello, world! 👋
    Here are some emojis: 🎨 🌊 😎
    Multi-line support! 🚀 ✨
    '''

    # Create image
    image = Image.new('RGB', (550, 150), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)

    # Render text with emojis
    async with Pilmoji() as pilmoji:
        await pilmoji.text(image, (10, 10), text.strip(), font, fill=(0, 0, 0))

    image.save('output.png')
    image.show()

asyncio.run(main())
```

### With Discord Emoji Support

```python
async def main():
    text = '''
    Unicode emoji: 👋 🎨 😎
    Discord emoji: <:custom:123456789012345678>
    '''

    image = Image.new('RGB', (550, 100), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)

    async with Pilmoji() as pilmoji:
        await pilmoji.text_with_discord_emoji(
            image, (10, 10), text.strip(), font, fill=(0, 0, 0)
        )

    image.save('output.png')

asyncio.run(main())
```

## 🎨 Emoji Styles

Choose from different emoji styles:

```python
from pilmoji import Pilmoji, EmojiStyle, EmojiCDNSource

# Apple style (default)
source = EmojiCDNSource(style=EmojiStyle.APPLE)

# Google style
source = EmojiCDNSource(style=EmojiStyle.GOOGLE)

# Twitter style
source = EmojiCDNSource(style=EmojiStyle.TWITTER)

# Facebook style
source = EmojiCDNSource(style=EmojiStyle.FACEBOOK)

async with Pilmoji(source=source) as pilmoji:
    await pilmoji.text(image, (10, 10), "Hello 👋", font)
```

## 🔧 API Reference

### `Pilmoji`

Main class for rendering text with emojis.

**Constructor:**

```python
Pilmoji(
    source: BaseSource = EmojiCDNSource(),
    cache: bool = True
)
```

**Parameters:**

- `source`: Emoji source to use (default: `EmojiCDNSource()`)
- `cache`: Enable emoji caching (default: `True`)

**Methods:**

#### `async text(image, xy, text, font, fill=None)`

Render text with Unicode emoji support.

- `image`: PIL Image object to render onto
- `xy`: Tuple of (x, y) coordinates for text position
- `text`: Text string to render (supports multiple lines)
- `font`: PIL Font object
- `fill`: Text color (default: black)

#### `async text_with_discord_emoji(image, xy, text, font, fill=None)`

Render text with both Unicode and Discord emoji support.

Parameters are the same as `text()`.

### `EmojiCDNSource`

Default emoji source using [emojicdn.elk.sh](https://emojicdn.elk.sh/).

**Constructor:**

```python
EmojiCDNSource(
    style: EmojiStyle = EmojiStyle.APPLE,
    cache_dir: Path | None = None
)
```

**Parameters:**

- `style`: Emoji style to use (Apple, Google, Twitter, Facebook)
- `cache_dir`: Custom cache directory (default: `~/.cache/pilmoji`)

## 🔌 Custom Emoji Sources

Create your own emoji source by subclassing `BaseSource`:

```python
from pilmoji import BaseSource
from io import BytesIO

class CustomEmojiSource(BaseSource):
    async def get_emoji(self, emoji: str) -> BytesIO | None:
        # Your custom emoji fetching logic
        pass

    async def get_discord_emoji(self, id: int) -> BytesIO | None:
        # Your custom Discord emoji fetching logic
        pass

# Use your custom source
async with Pilmoji(source=CustomEmojiSource()) as pilmoji:
    await pilmoji.text(image, (10, 10), "Hello 👋", font)
```

## 📝 Examples

### Different Text Colors

```python
# Red text
await pilmoji.text(image, (10, 10), "Red text 🔴", font, fill=(255, 0, 0))

# RGB tuple
await pilmoji.text(image, (10, 50), "Blue text 🔵", font, fill=(0, 0, 255))

# RGBA tuple with transparency
await pilmoji.text(image, (10, 90), "Semi-transparent 👻", font, fill=(0, 0, 0, 128))
```

### Multi-line Text

```python
text = """Line 1 with emoji 🎨
Line 2 with emoji 🌊
Line 3 with emoji 😎"""

await pilmoji.text(image, (10, 10), text, font, fill=(0, 0, 0))
```

### Without Context Manager

```python
pilmoji = Pilmoji()
await pilmoji.text(image, (10, 10), "Hello 👋", font)
await pilmoji.aclose()  # Don't forget to close!
```

## 🧪 Development

### Setup

```bash
# Clone the repository
git clone https://github.com/fllesser/apilmoji.git
cd apilmoji

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

### Running Tests

```bash
# Run all tests
uv run poe test

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original [Pilmoji](https://github.com/jay3332/pilmoji) project by jay3332
- [Pillow](https://github.com/python-pillow/Pillow/) - Python Imaging Library
- [emojicdn.elk.sh](https://emojicdn.elk.sh/) - Emoji CDN service

## 🔗 Links

- **Repository:** https://github.com/fllesser/apilmoji
- **Issues:** https://github.com/fllesser/apilmoji/issues
- **Releases:** https://github.com/fllesser/apilmoji/releases
- **Related Project:** [nonebot-plugin-parser](https://github.com/fllesser/nonebot-plugin-parser)
