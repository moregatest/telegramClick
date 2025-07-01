"""
TelegramClick CLI工具
用於快速創建TelegramClick應用
"""

import os
import sys
import click
from pathlib import Path
from typing import Optional

from . import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """TelegramClick CLI工具 - 快速創建Telegram Bot"""
    pass


@main.command()
@click.argument('project_name')
@click.option('--template', 
              type=click.Choice(['basic', 'advanced', 'production']), 
              default='basic',
              help='項目模板類型')
@click.option('--use-uv/--no-use-uv', default=True, help='使用uv作為包管理器')
def create(project_name: str, template: str, use_uv: bool):
    """創建新的TelegramClick項目"""
    project_path = Path(project_name)
    
    if project_path.exists():
        click.echo(f"❌ 項目目錄 {project_name} 已存在")
        return
    
    # 創建項目結構
    try:
        project_path.mkdir()
        _create_project_structure(project_path, template, use_uv)
        
        click.echo(f"✅ 項目 {project_name} 創建成功！")
        click.echo(f"📁 項目路徑：{project_path.absolute()}")
        click.echo("\n下一步操作：")
        click.echo(f"1. cd {project_name}")
        click.echo("2. 編輯 .env 文件，添加你的 BOT_TOKEN")
        
        if use_uv:
            click.echo("3. uv sync")
            click.echo("4. uv run python main.py")
        else:
            click.echo("3. pip install -r requirements.txt")
            click.echo("4. python main.py")
            
    except Exception as e:
        click.echo(f"❌ 創建項目失敗: {e}")
        # 清理失敗的目錄
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)


@main.command()
@click.argument('cli_file')
@click.option('--output', '-o', help='輸出文件名')
@click.option('--token-env', default='BOT_TOKEN', help='Bot Token環境變數名')
@click.option('--admin-users', help='管理員用戶ID，用逗號分隔')
def wrap(cli_file: str, output: Optional[str], token_env: str, admin_users: Optional[str]):
    """包裝現有的Click CLI為Telegram Bot"""
    cli_path = Path(cli_file)
    
    if not cli_path.exists():
        click.echo(f"❌ 找不到CLI文件: {cli_file}")
        return
    
    if not output:
        output = f"{cli_path.stem}_bot.py"
    
    # 解析管理員用戶
    admin_list = []
    if admin_users:
        try:
            admin_list = [int(uid.strip()) for uid in admin_users.split(',') if uid.strip()]
        except ValueError:
            click.echo("❌ 管理員用戶ID格式錯誤，請使用數字，用逗號分隔")
            return
    
    # 生成包裝器代碼
    wrapper_code = _generate_wrapper_code(cli_file, token_env, admin_list)
    
    try:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(wrapper_code)
        
        click.echo(f"✅ 包裝器創建成功: {output}")
        click.echo(f"📝 請設置環境變數 {token_env}")
        click.echo(f"🚀 運行: python {output}")
        
    except Exception as e:
        click.echo(f"❌ 創建包裝器失敗: {e}")


@main.command() 
@click.argument('script_file')
@click.option('--token-env', default='BOT_TOKEN', help='Bot Token環境變數名')
def script(script_file: str, token_env: str):
    """將現有Python腳本轉換為uv script格式的Bot"""
    script_path = Path(script_file)
    
    if not script_path.exists():
        click.echo(f"❌ 找不到腳本文件: {script_file}")
        return
    
    # 讀取原始腳本
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        click.echo(f"❌ 讀取文件失敗: {e}")
        return
    
    # 生成uv script版本
    script_content = _generate_uv_script(original_content, token_env)
    
    output_file = f"{script_path.stem}_uv.py"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        click.echo(f"✅ uv script創建成功: {output_file}")
        click.echo(f"🚀 運行: uv run {output_file}")
        
    except Exception as e:
        click.echo(f"❌ 創建uv script失敗: {e}")


@main.command()
def info():
    """顯示TelegramClick信息"""
    click.echo(f"📦 TelegramClick v{__version__}")
    click.echo("🔗 GitHub: https://github.com/tung/telegram-click")
    click.echo("📚 文檔: https://github.com/tung/telegram-click/wiki")
    click.echo("\n🎯 功能特色:")
    click.echo("  • 零侵入式Click CLI轉換")
    click.echo("  • 智能UI生成")
    click.echo("  • 雙模式支援(CLI/Bot)")
    click.echo("  • 生產就緒")
    click.echo("  • uv友好")


def _create_project_structure(project_path: Path, template: str, use_uv: bool):
    """創建項目結構"""
    # 創建基本目錄
    (project_path / "src").mkdir()
    
    # 創建配置文件
    if use_uv:
        _create_uv_config(project_path)
    else:
        _create_pip_config(project_path)
    
    # 創建主程序
    _create_main_file(project_path, template)
    
    # 創建環境變數文件
    _create_env_file(project_path)
    
    # 創建README
    _create_readme(project_path, template)


def _create_uv_config(project_path: Path):
    """創建uv配置"""
    pyproject_content = f'''[project]
name = "{project_path.name}"
version = "0.1.0"
description = "TelegramClick Bot 應用"
dependencies = [
    "telegram-click>=0.1.0",
    "click>=8.1.7",
    "python-dotenv>=1.0.0",
]
requires-python = ">=3.9"

[project.scripts]
{project_path.name.replace("-", "_")} = "main:main"
'''
    
    (project_path / "pyproject.toml").write_text(pyproject_content, encoding='utf-8')


def _create_pip_config(project_path: Path):
    """創建pip配置"""
    requirements_content = '''telegram-click>=0.1.0
click>=8.1.7
python-dotenv>=1.0.0
'''
    
    (project_path / "requirements.txt").write_text(requirements_content, encoding='utf-8')


def _create_main_file(project_path: Path, template: str):
    """創建主程序文件"""
    if template == 'basic':
        content = _get_basic_template()
    elif template == 'advanced':
        content = _get_advanced_template()
    else:  # production
        content = _get_production_template()
    
    (project_path / "main.py").write_text(content, encoding='utf-8')


def _create_env_file(project_path: Path):
    """創建環境變數文件"""
    env_content = '''# Telegram Bot Token (從 @BotFather 獲取)
BOT_TOKEN=your_bot_token_here

# 管理員用戶ID (用逗號分隔)
ADMIN_USERS=123456789

# 調試模式
DEBUG=false

# 日誌級別
LOG_LEVEL=INFO
'''
    
    (project_path / ".env").write_text(env_content, encoding='utf-8')


def _create_readme(project_path: Path, template: str):
    """創建README文件"""
    readme_content = f'''# {project_path.name}

使用TelegramClick創建的Telegram Bot應用

## 快速開始

1. 設置Bot Token:
   ```bash
   # 編輯 .env 文件，設置你的BOT_TOKEN
   ```

2. 安裝依賴:
   ```bash
   # 使用uv
   uv sync
   
   # 或使用pip
   pip install -r requirements.txt
   ```

3. 運行:
   ```bash
   # uv
   uv run python main.py
   
   # 或直接運行
   python main.py
   ```

## 功能

- 🤖 Telegram Bot界面
- 🔧 CLI命令轉換
- 🛡️ 用戶權限控制
- 📊 參數驗證

## 使用

### CLI模式
```bash
python main.py command --option value
```

### Bot模式
1. 啟動: `python main.py`
2. 在Telegram中發送: `/command`
3. 跟隨Bot的互動式指引

---
由 [TelegramClick](https://github.com/tung/telegram-click) 強力驅動
'''
    
    (project_path / "README.md").write_text(readme_content, encoding='utf-8')


def _get_basic_template() -> str:
    """基礎模板"""
    return '''#!/usr/bin/env python3
"""
基礎TelegramClick Bot應用
"""

import os
import sys
import click
from dotenv import load_dotenv
from telegram_click import telegram_bot

# 載入環境變數
load_dotenv()

@telegram_bot(os.getenv("BOT_TOKEN"))
@click.group()
def cli():
    """我的Bot命令"""
    pass

@cli.command()
@click.option('--name', required=True, help='您的姓名')
@click.option('--age', type=int, help='您的年齡（可選）')
def greet(name: str, age: int = None):
    """問候命令"""
    age_text = f"，{age}歲" if age else ""
    return f"您好 {name}{age_text}！很高興認識您！"

@cli.command()
@click.option('--text', required=True, help='要回應的文字')
def echo(text: str):
    """回聲命令"""
    return f"🔊 Echo: {text}"

def main():
    """主程序入口"""
    if not os.getenv("BOT_TOKEN"):
        print("❌ 請在 .env 文件中設置 BOT_TOKEN")
        sys.exit(1)
    
    # 智能模式：有參數=CLI，無參數=Bot
    if len(sys.argv) > 1:
        cli()  # CLI模式
    else:
        print("🤖 啟動Telegram Bot...")
        cli.run_telegram_bot()  # Bot模式

if __name__ == "__main__":
    main()
'''


def _get_advanced_template() -> str:
    """進階模板"""
    return '''#!/usr/bin/env python3
"""
進階TelegramClick Bot應用
"""

import os
import sys
import click
from datetime import datetime
from dotenv import load_dotenv
from telegram_click import telegram_bot

# 載入環境變數
load_dotenv()

# 解析管理員用戶
admin_users = []
if os.getenv("ADMIN_USERS"):
    admin_users = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",") if x.strip()]

@telegram_bot(
    bot_token=os.getenv("BOT_TOKEN"),
    admin_users=admin_users,
    custom_help={
        'status': '📊 查看系統狀態',
        'backup': '💾 執行數據備份',
        'deploy': '🚀 部署應用',
    }
)
@click.group()
def cli():
    """進階Bot命令集"""
    pass

@cli.command()
@click.option('--service', help='特定服務名稱')
def status(service: str = None):
    """查看系統狀態"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if service:
        return f"📊 服務 {service} 狀態: 運行中\\n🕒 檢查時間: {timestamp}"
    else:
        return f"📊 系統總覽:\\n✅ 在線服務: 5/5\\n🕒 檢查時間: {timestamp}"

@cli.command()
@click.option('--path', required=True, help='備份路徑')
@click.option('--compress', is_flag=True, help='是否壓縮')
def backup(path: str, compress: bool):
    """執行數據備份"""
    compress_text = " (壓縮)" if compress else ""
    return f"💾 開始備份到 {path}{compress_text}\\n⏱️ 預計需要5-10分鐘"

@cli.command()
@click.option('--env', 
              type=click.Choice(['dev', 'staging', 'prod']), 
              required=True,
              help='部署環境')
@click.option('--version', help='版本號')
def deploy(env: str, version: str = None):
    """部署應用"""
    version_text = f" v{version}" if version else ""
    return f"🚀 開始部署{version_text}到 {env} 環境\\n📋 部署日誌已記錄"

def main():
    """主程序入口"""
    if not os.getenv("BOT_TOKEN"):
        print("❌ 請在 .env 文件中設置 BOT_TOKEN")
        sys.exit(1)
    
    # 智能模式：有參數=CLI，無參數=Bot
    if len(sys.argv) > 1:
        cli()  # CLI模式
    else:
        print("🤖 啟動進階Telegram Bot...")
        cli.run_telegram_bot()  # Bot模式

if __name__ == "__main__":
    main()
'''


def _get_production_template() -> str:
    """生產模板"""
    return '''#!/usr/bin/env python3
"""
生產級TelegramClick Bot應用
"""

import os
import sys
import logging
import click
from datetime import datetime
from dotenv import load_dotenv
from telegram_click import production_telegram_bot

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 解析管理員用戶
admin_users = []
if os.getenv("ADMIN_USERS"):
    admin_users = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",") if x.strip()]

@production_telegram_bot(
    bot_token=os.getenv("BOT_TOKEN"),
    admin_users=admin_users,
    dangerous_commands=['reset', 'delete', 'drop'],
    custom_help={
        'status': '📊 查看生產環境狀態',
        'logs': '📋 查看應用日誌',
        'scale': '📈 調整服務規模',
        'health': '🏥 健康檢查',
    }
)
@click.group()
def cli():
    """生產環境運維工具"""
    pass

@cli.command()
@click.option('--service', help='服務名稱')
@click.option('--detail', is_flag=True, help='詳細信息')
def status(service: str = None, detail: bool = False):
    """查看生產環境狀態"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = f"📊 **生產環境狀態** ({timestamp})\\n\\n"
    
    if service:
        result += f"🔍 **服務**: {service}\\n"
        result += f"✅ **狀態**: 運行中\\n"
        result += f"💻 **實例**: 3/3 健康\\n"
        
        if detail:
            result += f"📈 **CPU**: 45%\\n"
            result += f"💾 **記憶體**: 67%\\n"
            result += f"🌐 **網路**: 正常\\n"
    else:
        result += f"🌍 **總覽**\\n"
        result += f"✅ **在線服務**: 12/14\\n"
        result += f"⚠️ **警告**: 2個服務負載較高\\n"
    
    return result

@cli.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--lines', type=int, default=50, help='行數')
@click.option('--level', 
              type=click.Choice(['error', 'warn', 'info']), 
              default='error',
              help='日誌級別')
def logs(app: str, lines: int, level: str):
    """查看應用日誌"""
    return f"📋 **{app}** 最近{lines}行{level}日誌:\\n```\\n[模擬日誌輸出]\\n```"

@cli.command()
@click.option('--service', required=True, help='服務名稱')
@click.option('--replicas', type=int, required=True, help='實例數量')
@click.option('--confirm', is_flag=True, help='確認執行')
def scale(service: str, replicas: int, confirm: bool):
    """調整服務規模"""
    if not confirm:
        return f"⚠️ 請使用 --confirm 確認將 {service} 調整為 {replicas} 個實例"
    
    return f"📈 已將 {service} 調整為 {replicas} 個實例\\n⏱️ 預計2-3分鐘完成"

@cli.command()
@click.option('--endpoint', required=True, help='健康檢查端點')
@click.option('--timeout', type=int, default=30, help='超時時間(秒)')
def health(endpoint: str, timeout: int):
    """執行健康檢查"""
    return f"🏥 {endpoint} 健康檢查:\\n✅ 響應時間: 145ms\\n🔄 狀態: 健康"

def main():
    """主程序入口"""
    if not os.getenv("BOT_TOKEN"):
        print("❌ 請在 .env 文件中設置 BOT_TOKEN")
        sys.exit(1)
    
    if not admin_users:
        print("⚠️ 警告: 未設置管理員用戶，所有用戶都可以使用")
    
    # 智能模式：有參數=CLI，無參數=Bot
    if len(sys.argv) > 1:
        cli()  # CLI模式
    else:
        print("🤖 啟動生產級Telegram Bot...")
        print(f"👥 管理員用戶: {admin_users}")
        cli.run_telegram_bot()  # Bot模式

if __name__ == "__main__":
    main()
'''


def _generate_wrapper_code(cli_file: str, token_env: str, admin_users: list) -> str:
    """生成包裝器代碼"""
    admin_str = str(admin_users) if admin_users else "[]"
    
    return f'''#!/usr/bin/env python3
"""
{Path(cli_file).stem} 的 Telegram Bot 包裝器
由 TelegramClick 自動生成
"""

import os
from dotenv import load_dotenv
from telegram_click import create_bot_from_cli_file

# 載入環境變數
load_dotenv()

def main():
    """啟動Bot"""
    bot_token = os.getenv("{token_env}")
    
    if not bot_token:
        print("❌ 請設置環境變數 {token_env}")
        return
    
    # 創建Bot
    bot = create_bot_from_cli_file(
        bot_token=bot_token,
        cli_file_path="{cli_file}",
        admin_users={admin_str},
        enable_logging=True
    )
    
    print("🚀 啟動 {Path(cli_file).stem} Telegram Bot...")
    bot.run()

if __name__ == "__main__":
    main()
'''


def _generate_uv_script(original_content: str, token_env: str) -> str:
    """生成uv script版本"""
    dependencies_header = '''# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "telegram-click",
#     "click>=8.1.7",
#     "python-dotenv>=1.0.0",
# ]
# ///

'''
    
    # 在原始內容前添加依賴聲明
    return dependencies_header + original_content


if __name__ == "__main__":
    main()
