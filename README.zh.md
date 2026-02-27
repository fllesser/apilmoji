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
    "We have standard emojis: 😂, 🚀, 🐍, 💻."
    "And some more: 🌟✨🔥💯."
    """
    font = ImageFont.truetype("LXGWWenKai-Regular.ttf", 24)
    with Image.new("RGB", (600, 200), (255, 255, 255)) as image:
        await Apilmoji.text(image, (10, 10), text, font=font, fill=(0, 0, 0))
        image.show()


asyncio.run(main())

```
### 支持 Discord 表情符号

```python
import asyncio

from PIL import Image, ImageFont
from apilmoji import Apilmoji


async def main():
    text = """
    Unicode emojis: 👋 🎨 😎
    Discord emojis: <:rooThink:596576798351949847>
    """
    font = ImageFont.truetype("LXGWWenKai-Regular.ttf", 24)
    with Image.new("RGB", (600, 200), (255, 255, 255)) as image:
        await Apilmoji.text_with_discord(image, (10, 10), text, font, fill=(0, 0, 0))
        image.show()


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
