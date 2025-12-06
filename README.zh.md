# Apilmoji

一个高性能的异步表情符号渲染库

[![LICENSE](https://img.shields.io/github/license/fllesser/apilmoji)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/apilmoji.svg)](https://pypi.python.org/pypi/apilmoji)
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13|3.14-blue.svg)](https://python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/fllesser/apilmoji/master.svg)](https://results.pre-commit.ci/latest/github/fllesser/apilmoji/master)
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
    text = '''
    Hello, world! 👋
    这里有一些表情符号：🎨 🌊 😎
    支持多行文本！🚀 ✨
    '''

    # 创建图像
    image = Image.new('RGB', (550, 150), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)

    # 渲染带表情符号的文本
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

### 支持 Discord 表情符号

```python
async def main():
    text = '''
    Unicode 表情符号：👋 🎨 😎
    Discord 表情符号：<:rooThink:123456789012345678>
    '''

    image = Image.new('RGB', (550, 100), (255, 255, 255))
    font = ImageFont.truetype('arial.ttf', 24)

    await Apilmoji.text(
        image,
        (10, 10),
        text.strip(),
        font,
        fill=(0, 0, 0),
        support_ds_emj=True  # 启用 Discord 表情符号支持
    )

    image.save('output.png')

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

# Twitter 样式
source = EmojiCDNSource(style=EmojiStyle.TWITTER)

# Facebook 样式
source = EmojiCDNSource(style=EmojiStyle.FACEBOOK)

await Apilmoji.text(
    image,
    (10, 10),
    "Hello 👋",
    font,
    source=source
)
```

## 🔧 API 参考

### `Apilmoji.text`

主要的文本渲染方法。

```python
await Apilmoji.text(
    image: PILImage,
    xy: tuple[int, int],
    lines: list[str] | str,
    font: FontT,
    *,
    fill: ColorT | None = None,
    line_height: int | None = None,
    support_ds_emj: bool = False,
    source: EmojiCDNSource | None = None,
) -> None
```

**参数:**

- `image`: PIL Image 对象，用于渲染
- `xy`: 文本位置的 (x, y) 坐标元组
- `lines`: 要渲染的文本行（支持多行）
- `font`: PIL Font 对象
- `fill`: 文本颜色（默认：黑色）
- `line_height`: 行高（默认：字体高度）
- `support_ds_emj`: 是否支持 Discord 表情符号（默认：False）
- `source`: 表情符号源（默认：EmojiCDNSource()）

### `EmojiCDNSource`

默认表情符号源，使用 [emojicdn.elk.sh](https://emojicdn.elk.sh/)。

```python
EmojiCDNSource(
    base_url: str = "https://emojicdn.elk.sh",
    style: EmojiStyle = EmojiStyle.APPLE,
    *,
    cache_dir: Path | None = None,
    enable_discord: bool = False,
    max_concurrent: int = 50,
    enable_tqdm: bool = False,
)
```

**参数:**

- `base_url`: CDN 基础 URL
- `style`: 表情符号样式
- `cache_dir`: 自定义缓存目录（默认：`~/.cache/apilmoji`）
- `enable_discord`: 启用 Discord 表情符号支持
- `max_concurrent`: 最大并发下载数（默认：50）
- `enable_tqdm`: 启用进度条显示

## 📝 高级用法

### 自定义行高和颜色

```python
# 自定义行高和颜色
await Apilmoji.text(
    image,
    (10, 10),
    "自定义样式 🎨",
    font,
    fill=(255, 0, 0),      # 红色文本
    line_height=40,        # 自定义行高
    support_ds_emj=True
)
```

### 启用进度条

```python
from apilmoji import EmojiCDNSource

# 启用进度条显示
source = EmojiCDNSource(enable_tqdm=True)

await Apilmoji.text(
    image,
    (10, 10),
    "带进度条的表情符号下载 📊",
    font,
    source=source
)
```

### 调整并发数

```python
# 调整并发下载数
source = EmojiCDNSource(max_concurrent=10)  # 限制为10个并发

await Apilmoji.text(
    image,
    (10, 10),
    "限制并发下载 ⚡",
    font,
    source=source
)
```
