# TelegramClick

**零侵入式Click CLI到Telegram Bot轉換器**

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/telegram-click.svg)](https://badge.fury.io/py/telegram-click)

TelegramClick讓您能夠**5分鐘內**將任何現有的Click CLI工具轉換為功能完整的Telegram Bot，無需修改任何現有代碼。

## ✨ 核心特色

- 🔄 **零侵入轉換** - 現有Click CLI代碼完全不需要修改
- 🤖 **智能UI生成** - 自動將Click選項轉換為Telegram按鈕和對話
- 🎯 **雙模式支援** - 同一份代碼支援CLI和Telegram使用
- 🛡️ **生產就緒** - 支援用戶權限、錯誤處理、環境變數配置
- 📦 **uv友好** - 完美支援uv script dependencies

## 🚀 快速開始

### 安裝

#### 從PyPI安裝
```bash
# 使用uv安裝
uv add telegram-click

# 或使用pip安裝
pip install telegram-click
```

#### 從GitHub安裝
```bash
# 使用uv從GitHub安裝
uv add git+https://github.com/moregatest/telegramClick.git

# 或使用pip從GitHub安裝
pip install git+https://github.com/moregatest/telegramClick.git

# 安裝特定版本/分支
uv add git+https://github.com/moregatest/telegramClick.git@main
```

#### 開發模式安裝
```bash
# 克隆並安裝
git clone https://github.com/moregatest/telegramClick.git
cd telegramClick
uv sync --dev
```

### 基本使用

#### 方法1：裝飾器方式（推薦新項目）

```python
import os
import sys
import click
from telegram_click import telegram_bot

@telegram_bot(os.getenv("BOT_TOKEN"))
@click.group()
def my_tools():
    """我的工具集"""
    pass

@my_tools.command()
@click.option('--name', required=True, help='您的姓名')
@click.option('--age', type=int, help='您的年齡')
def greet(name, age):
    """問候命令"""
    age_text = f"，{age}歲" if age else ""
    return f"您好 {name}{age_text}！"

if __name__ == "__main__":
    # CLI模式：python script.py greet --name=王小明
    # Bot模式：python script.py
    if len(sys.argv) > 1:
        my_tools()
    else:
        my_tools.run_telegram_bot()
```

#### 方法2：包裝現有CLI（零修改）

```python
# 你的現有CLI文件完全不動
# existing_cli.py
import click

@click.group()
def devops():
    """DevOps工具"""
    pass

@devops.command()
@click.option('--service', required=True)
def restart(service):
    return f"重啟服務: {service}"

# 新建bot.py（只需要這個新文件）
import os
from telegram_click import create_bot_from_cli_file

bot = create_bot_from_cli_file(
    bot_token=os.getenv("BOT_TOKEN"),
    cli_file_path="existing_cli.py"
)
bot.run()
```

#### 方法3：uv script（最簡單）

```python
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "git+https://github.com/moregatest/telegramClick.git",
#     "click>=8.1.7",
# ]
# ///

import os
import click
from telegram_click import telegram_bot

@telegram_bot(os.getenv("BOT_TOKEN"))
@click.group()
def tools():
    pass

@tools.command()
@click.option('--text', required=True)
def echo(text):
    return f"Echo: {text}"

if __name__ == "__main__":
    tools.run_telegram_bot()
```

運行：`uv run my_bot.py`

## 🎮 使用體驗

### CLI使用
```bash
$ python my_cli.py greet --name="Alice" --age=25
您好 Alice，25歲！
```

### Telegram使用
1. 發送 `/greet` 
2. 機器人回應：「🔸 **name** - 請輸入您的姓名：」
3. 輸入：「Alice」
4. 機器人回應：「🔸 **age** - 請輸入您的年齡：」  
5. 輸入：「25」
6. 機器人回應：「✅ 執行結果：您好 Alice，25歲！」

## 🛠️ 進階功能

### 安全控制

```python
from telegram_click import create_bot_from_click_group

bot = create_bot_from_click_group(
    bot_token="YOUR_TOKEN",
    click_group=my_cli,
    admin_users=[123456789],  # 只有這些用戶可以使用
    commands_blacklist=['dangerous_cmd'],  # 隱藏危險命令
)
```

### 自定義幫助

```python
from telegram_click import create_bot_from_cli_file

bot = create_bot_from_cli_file(
    bot_token="YOUR_TOKEN",
    cli_file_path="my_cli.py",
    custom_help={
        'deploy': '🚀 部署應用到生產環境',
        'backup': '💾 備份重要數據'
    }
)
```

### 參數類型自動轉換

- `click.Choice(['a', 'b'])` → Telegram按鈕選擇
- `click.BOOL` → 是/否按鈕  
- `click.INT/FLOAT` → 數字輸入驗證
- `str` → 文字輸入

## 📚 完整範例

查看 `examples/` 目錄中的完整範例：

- `examples/basic_example.py` - 基礎使用
- `examples/devops_bot.py` - DevOps工具Bot
- `examples/production_ready.py` - 生產級範例

## 🧪 開發

### 設置開發環境

```bash
# 克隆項目
git clone https://github.com/moregatest/telegramClick.git
cd telegramClick

# 使用uv設置環境
uv sync --dev

# 運行測試
uv run pytest

# 代碼格式化
uv run black .
uv run isort .
```

### 運行測試

```bash
# 運行所有測試
uv run pytest

# 運行特定測試
uv run pytest tests/test_framework.py

# 運行測試並查看覆蓋率
uv run pytest --cov
```

### 代碼質量檢查

```bash
# 格式化代碼
uv run black .
uv run isort .

# 類型檢查
uv run mypy src/

# 代碼檢查
uv run flake8 src/
```

### 建構和發佈

```bash
# 建構套件
uv build

# 本地安裝
uv pip install -e .
```

## 📋 系統需求

- Python 3.9+
- python-telegram-bot >= 20.7
- click >= 8.1.7
- python-dotenv >= 1.0.0

## 🔧 環境變數

設定您的環境變數：

```bash
# .env 檔案
BOT_TOKEN=your_telegram_bot_token_here
```

## 📖 API文檔

### 核心類別

- `ClickToTelegramConverter` - 核心轉換器類別
- `TelegramClickConfig` - 配置數據類別
- `TelegramClickContext` - 執行上下文

### 裝飾器

- `@telegram_bot` - 基本Telegram Bot裝飾器
- `@secure_telegram_bot` - 安全版本（需要用戶驗證）
- `@production_telegram_bot` - 生產版本（包含錯誤處理）

### 工廠函數

- `create_bot_from_click_group()` - 從Click群組創建Bot
- `create_bot_from_cli_file()` - 從CLI檔案創建Bot

## 🤝 貢獻

歡迎提交Issue和Pull Request！

1. Fork此專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟Pull Request

## 📄 授權

本專案採用MIT授權條款 - 查看 [LICENSE](LICENSE) 文件了解詳情

## 🙏 致謝

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - 強大的Telegram Bot框架
- [Click](https://github.com/pallets/click) - 優雅的CLI框架
- 所有貢獻者和用戶

## 🔗 相關連結

- [GitHub Repository](https://github.com/moregatest/telegramClick)
- [Issues](https://github.com/moregatest/telegramClick/issues)
- [Wiki](https://github.com/moregatest/telegramClick/wiki)

---

**讓CLI工具擁有現代化的Telegram界面，就是這麼簡單！** 🚀