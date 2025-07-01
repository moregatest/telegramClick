"""
TelegramClick裝飾器模組
提供便利的裝飾器函數
"""

import functools
import logging
from typing import List, Dict, Any, Callable
import click

from .factory import create_bot_from_click_group

logger = logging.getLogger(__name__)


def telegram_bot(
    bot_token: str,
    commands_whitelist: List[str] = None,
    commands_blacklist: List[str] = None,
    custom_help: Dict[str, str] = None,
    admin_users: List[int] = None,
    enable_logging: bool = True,
    max_message_length: int = 4000,
    **kwargs
):
    """
    裝飾器：將Click群組轉換為Telegram Bot
    
    這是最簡單的使用方式，只需要在Click群組上添加這個裝飾器。
    
    Args:
        bot_token: Telegram Bot Token
        commands_whitelist: 允許的命令白名單
        commands_blacklist: 禁用的命令黑名單
        custom_help: 自定義幫助文字
        admin_users: 管理員用戶ID列表
        enable_logging: 是否啟用日誌
        max_message_length: 最大訊息長度
        **kwargs: 其他配置參數
    
    Returns:
        裝飾後的Click群組，附加了Telegram Bot功能
    
    Example:
        >>> @telegram_bot("YOUR_BOT_TOKEN")
        >>> @click.group()
        >>> def my_cli():
        >>>     '''我的CLI工具'''
        >>>     pass
        >>> 
        >>> @my_cli.command()
        >>> @click.option('--name', required=True)
        >>> def greet(name):
        >>>     return f"Hello {name}!"
        >>> 
        >>> if __name__ == "__main__":
        >>>     # CLI模式：python script.py greet --name=Alice
        >>>     # Bot模式：my_cli.run_telegram_bot()
        >>>     my_cli.run_telegram_bot()
    """
    def decorator(click_group: click.Group) -> click.Group:
        if not isinstance(click_group, click.Group):
            raise TypeError("telegram_bot裝飾器只能用於Click群組")
        
        # 創建Bot實例
        bot = create_bot_from_click_group(
            bot_token=bot_token,
            click_group=click_group,
            commands_whitelist=commands_whitelist,
            commands_blacklist=commands_blacklist,
            custom_help=custom_help,
            admin_users=admin_users,
            enable_logging=enable_logging,
            max_message_length=max_message_length,
            **kwargs
        )
        
        # 將Bot功能附加到Click群組
        click_group.telegram_bot = bot
        click_group.run_telegram_bot = bot.run
        
        # 添加便利方法
        def get_bot_info():
            """獲取Bot信息"""
            return {
                'token': bot_token[:10] + "..." if bot_token else None,
                'commands_count': len(bot.click_commands),
                'admin_users': admin_users or [],
                'whitelist': commands_whitelist or [],
                'blacklist': commands_blacklist or []
            }
        
        def start_bot_in_background():
            """在背景啟動Bot（非阻塞）"""
            import threading
            thread = threading.Thread(target=bot.run, daemon=True)
            thread.start()
            return thread
        
        click_group.get_bot_info = get_bot_info
        click_group.start_bot_in_background = start_bot_in_background
        
        logger.info(f"為Click群組 '{click_group.name}' 配置了Telegram Bot功能")
        
        return click_group
    
    return decorator


def secure_telegram_bot(
    bot_token: str,
    admin_users: List[int],
    allowed_commands: List[str] = None,
    **kwargs
):
    """
    安全版本的telegram_bot裝飾器
    
    Args:
        bot_token: Telegram Bot Token
        admin_users: 管理員用戶ID列表（必需）
        allowed_commands: 允許的命令列表
        **kwargs: 其他配置參數
    
    Example:
        >>> @secure_telegram_bot("TOKEN", admin_users=[123456789])
        >>> @click.group()
        >>> def admin_tools():
        >>>     pass
    """
    if not admin_users:
        raise ValueError("安全模式下必須指定管理員用戶")
    
    return telegram_bot(
        bot_token=bot_token,
        admin_users=admin_users,
        commands_whitelist=allowed_commands,
        enable_logging=True,
        **kwargs
    )


def production_telegram_bot(
    bot_token: str,
    admin_users: List[int],
    dangerous_commands: List[str] = None,
    custom_help: Dict[str, str] = None,
    **kwargs
):
    """
    生產環境版本的telegram_bot裝飾器
    
    Args:
        bot_token: Telegram Bot Token
        admin_users: 管理員用戶ID列表
        dangerous_commands: 危險命令黑名單
        custom_help: 自定義幫助文字
        **kwargs: 其他配置參數
    
    Example:
        >>> @production_telegram_bot(
        >>>     "TOKEN", 
        >>>     admin_users=[123456789],
        >>>     dangerous_commands=['reset', 'delete']
        >>> )
        >>> @click.group()
        >>> def prod_tools():
        >>>     pass
    """
    # 生產環境預設的危險命令
    default_dangerous = ['rm', 'delete', 'reset', 'drop', 'truncate', 'destroy']
    dangerous_commands = (dangerous_commands or []) + default_dangerous
    
    return telegram_bot(
        bot_token=bot_token,
        admin_users=admin_users,
        commands_blacklist=dangerous_commands,
        custom_help=custom_help or {},
        enable_logging=True,
        **kwargs
    )


def telegram_command(
    help_text: str = None,
    admin_only: bool = False,
    **kwargs
):
    """
    命令級別的裝飾器，為單個命令添加Telegram特定配置
    
    Args:
        help_text: 自定義幫助文字
        admin_only: 是否僅限管理員
        **kwargs: 其他配置
    
    Example:
        >>> @my_cli.command()
        >>> @telegram_command(help_text="🚀 部署應用", admin_only=True)
        >>> @click.option('--env', required=True)
        >>> def deploy(env):
        >>>     return f"部署到{env}環境"
    """
    def decorator(func: Callable) -> Callable:
        # 在函數上標記Telegram配置
        if not hasattr(func, '_telegram_config'):
            func._telegram_config = {}
        
        func._telegram_config.update({
            'help_text': help_text,
            'admin_only': admin_only,
            **kwargs
        })
        
        return func
    
    return decorator


def validate_bot_token(token: str) -> bool:
    """
    驗證Bot Token格式
    
    Args:
        token: Bot Token
    
    Returns:
        bool: Token是否有效
    """
    if not token:
        return False
    
    # 基本格式檢查：數字:字母數字字符_-
    import re
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))


def smart_run(click_group: click.Group, auto_detect: bool = True):
    """
    智能運行模式：自動檢測CLI或Bot模式
    
    Args:
        click_group: Click群組
        auto_detect: 是否自動檢測模式
    
    Example:
        >>> if __name__ == "__main__":
        >>>     smart_run(my_cli)
    """
    import sys
    
    if auto_detect:
        # 有命令列參數 = CLI模式，無參數 = Bot模式
        if len(sys.argv) > 1 and not sys.argv[1].startswith('--telegram'):
            # CLI模式
            click_group()
        else:
            # Bot模式
            if hasattr(click_group, 'run_telegram_bot'):
                click_group.run_telegram_bot()
            else:
                logger.error("Click群組沒有配置Telegram Bot功能")
                sys.exit(1)
    else:
        # 總是運行Bot模式
        if hasattr(click_group, 'run_telegram_bot'):
            click_group.run_telegram_bot()
        else:
            logger.error("Click群組沒有配置Telegram Bot功能")
            sys.exit(1)
