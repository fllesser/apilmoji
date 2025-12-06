# Apilmoji

An asynchronous emoji rendering Extension for PIL

[![LICENSE](https://img.shields.io/github/license/fllesser/apilmoji)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/apilmoji.svg)](https://pypi.python.org/pypi/apilmoji)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13|3.14-blue.svg)](https://python.org)
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/fllesser/apilmoji/main.svg)](https://results.pre-commit.ci/latest/github/fllesser/apilmoji/main)
[![codecov](https://codecov.io/gh/fllesser/apilmoji/graph/badge.svg?token=VCS8IHSO7U)](https://codecov.io/gh/fllesser/apilmoji)

</div>

## ✨ Features

- 🎨 **Unicode Emoji Support** - Render standard Unicode emojis
- 💬 **Discord Emoji Support** - Render custom Discord emojis
- 🔄 **Concurrent Downloads** - Support concurrent emoji downloads for better performance
- 💾 **Smart Caching** - Local file caching to avoid repeated downloads
- 🎭 **Multiple Styles** - Support for Apple, Google, Twitter, Facebook, and other styles
- 📊 **Progress Display** - Optional progress bar for download progress

## 📦 Installation

**Requirements:** Python 3.10 or higher

```bash
uv add apilmoji
```

Or install from source:

```bash
uv add git+https://github.com/fllesser/apilmoji
```

## 🚀 Quick Start

### Basic Usage (Unicode Emojis Only)

```python
import asyncio
from PIL import Image, ImageFont
from apilmoji import Apilmoji

async def main():
    text = '''
    Hello, world! 👋
    Here are some emojis: 🎨 🌊 😎
    Supports multi-line text! 🚀 ✨
    '''

    # Create image
    image = Image.new('RGB', (550, 150), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)

    # Render text with emojis
    await Apilmoji.text(
        image,
        (10, 10),
        text.strip(),
        font,
        fill=(0, 0, 0)
    )

    image.save('output.png')
    image.show()

asyncio.run(main())
```

### Discord Emoji Support

```python
async def main():
    text = '''
    Unicode emojis: 👋 🎨 😎
    Discord emojis: <:rooThink:123456789012345678>
    '''

    image = Image.new('RGB', (550, 100), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)
    source = EmojiCDNSource(enable_discord=True)
    await Apilmoji.text(
        image,
        (10, 40),
        COMPLEX_TEXT,
        font,
        fill=(0, 0, 0),
        support_ds_emj=True,
        source=source,
    )

    image.save('output.png')

asyncio.run(main())
```

## 🎨 Emoji Styles

Choose different emoji styles:

```python
from apilmoji import Apilmoji, EmojiCDNSource, EmojiStyle

# Apple style (default)
source = EmojiCDNSource(style=EmojiStyle.APPLE)

# Google style
source = EmojiCDNSource(style=EmojiStyle.GOOGLE)

await Apilmoji.text(
    image,
    (10, 10),
    "Hello 👋",
    font,
    source=source
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/fllesser/apilmoji/issues) page.
