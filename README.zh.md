# Apilmoji

An asynchronous emoji rendering Extension for PIL

[![LICENSE](https://img.shields.io/github/license/fllesser/apilmoji)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/apilmoji.svg)](https://pypi.python.org/pypi/apilmoji)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13|3.14-blue.svg)](https://python.org)
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/fllesser/apilmoji/main.svg)](https://results.pre-commit.ci/latest/github/fllesser/apilmoji/main)
[![codecov](https://codecov.io/gh/fllesser/apilmoji/graph/badge.svg?token=VCS8IHSO7U)](https://codecov.io/gh/fllesser/apilmoji)

## ✨ 特性

- 🎨 **Unicode 表情符号支持** - 渲染标准 Unicode 表情符号
- 💬 **Discord 表情符号支持** - 渲染自定义 Discord 表情符号
- 🔄 **并发下载** - 支持并发下载表情符号，提升性能
- 💾 **智能缓存** - 本地文件缓存，避免重复下载
- 🎭 **多种样式** - 支持 Apple、Google、Twitter、Facebook 等样式
- 📊 **进度显示** - 可选进度条显示下载进度

## 📦 安装

**要求:** Python 3.10 或更高版本

```bash
uv add apilmoji
```

或从源码安装：

```bash
uv add git+https://github.com/fllesser/apilmoji
```

## 🚀 快速开始

### 基本用法（仅 Unicode 表情符号）

```python
import asyncio
from PIL import Image, ImageFont
from apilmoji import Apilmoji


async def main():
    text = """
    Hello, world! 👋
    这里有一些表情符号：🎨 🌊 😎
    支持多行文本！🚀 ✨
    """

    # 创建图像
    image = Image.new("RGB", (550, 150), (255, 255, 255))
    font = ImageFont.truetype("arial.ttf", 24)

    # 渲染带表情符号的文本
    await Apilmoji.text(image, (10, 10), text.strip(), font, fill=(0, 0, 0))

    image.save("output.png")
    image.show()


asyncio.run(main())
```

### 支持 Discord 表情符号

```python
import asyncio
from PIL import Image, ImageFont
from apilmoji import Apilmoji, EmojiCDNSource

async def main():
    text = """
    Unicode emojis: 👋 🎨 😎
    Discord emojis: <:rooThink:123456789012345678>
    """

    image = Image.new("RGB", (550, 100), (255, 255, 255))
    font = ImageFont.truetype("arial.ttf", 24)
    source = EmojiCDNSource()
    await Apilmoji.text_with_discord(
        image,
        (10, 40),
        text,
        font,
        fill=(0, 0, 0),
        source=source,
    )

    image.save("output.png")

asyncio.run(main())
```

## 🎨 表情符号样式

选择不同的表情符号样式：

```python
from apilmoji import Apilmoji, EmojiCDNSource, EmojiStyle

# Apple 样式（默认）
source = EmojiCDNSource(style=EmojiStyle.APPLE)

# Google 样式
source = EmojiCDNSource(style=EmojiStyle.GOOGLE)

await Apilmoji.text(
    image,
    (10, 10),
    "Hello 👋",
    font,
    source=source
)
```
