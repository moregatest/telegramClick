"""
TelegramClick工廠函數模組
提供便利的創建函數
"""

import click
from typing import List, Dict, Any

from .framework import ClickToTelegramConverter
from .types import TelegramClickConfig


def create_bot_from_click_group(
    bot_token: str, 
    click_group: click.Group,
    commands_whitelist: List[str] = None,
    commands_blacklist: List[str] = None,
    custom_help: Dict[str, str] = None,
    admin_users: List[int] = None,
    enable_logging: bool = True,
    max_message_length: int = 4000,
    **kwargs
) -> ClickToTelegramConverter:
    """
    從Click群組直接創建Telegram Bot
    
    Args:
        bot_token: Telegram Bot Token
        click_group: Click群組對象
        commands_whitelist: 允許的命令白名單
        commands_blacklist: 禁用的命令黑名單
        custom_help: 自定義幫助文字
        admin_users: 管理員用戶ID列表
        enable_logging: 是否啟用日誌
        max_message_length: 最大訊息長度
        **kwargs: 其他配置參數
    
    Returns:
        ClickToTelegramConverter: 配置好的轉換器實例
    
    Example:
        >>> @click.group()
        >>> def my_cli():
        >>>     pass
        >>> 
        >>> bot = create_bot_from_click_group("TOKEN", my_cli)
        >>> bot.run()
    """
    config = TelegramClickConfig(
        bot_token=bot_token,
        cli_group=click_group,
        commands_whitelist=commands_whitelist or [],
        commands_blacklist=commands_blacklist or [],
        custom_help=custom_help or {},
        admin_users=admin_users or [],
        enable_logging=enable_logging,
        max_message_length=max_message_length,
        **kwargs
    )
    
    return ClickToTelegramConverter(config)


def create_bot_from_cli_file(
    bot_token: str,
    cli_file_path: str,
    commands_whitelist: List[str] = None,
    commands_blacklist: List[str] = None,
    custom_help: Dict[str, str] = None,
    admin_users: List[int] = None,
    enable_logging: bool = True,
    max_message_length: int = 4000,
    **kwargs
) -> ClickToTelegramConverter:
    """
    從CLI文件創建Telegram Bot
    
    Args:
        bot_token: Telegram Bot Token
        cli_file_path: CLI文件路徑
        commands_whitelist: 允許的命令白名單
        commands_blacklist: 禁用的命令黑名單  
        custom_help: 自定義幫助文字
        admin_users: 管理員用戶ID列表
        enable_logging: 是否啟用日誌
        max_message_length: 最大訊息長度
        **kwargs: 其他配置參數
    
    Returns:
        ClickToTelegramConverter: 配置好的轉換器實例
    
    Example:
        >>> bot = create_bot_from_cli_file("TOKEN", "my_cli.py")
        >>> bot.run()
    """
    config = TelegramClickConfig(
        bot_token=bot_token,
        cli_module_path=cli_file_path,
        commands_whitelist=commands_whitelist or [],
        commands_blacklist=commands_blacklist or [],
        custom_help=custom_help or {},
        admin_users=admin_users or [],
        enable_logging=enable_logging,
        max_message_length=max_message_length,
        **kwargs
    )
    
    return ClickToTelegramConverter(config)


def create_secure_bot(
    bot_token: str,
    click_group_or_file: Any,
    admin_users: List[int],
    allowed_commands: List[str] = None,
    **kwargs
) -> ClickToTelegramConverter:
    """
    創建安全的Bot（僅限管理員使用）
    
    Args:
        bot_token: Telegram Bot Token
        click_group_or_file: Click群組對象或CLI文件路徑
        admin_users: 管理員用戶ID列表（必需）
        allowed_commands: 允許的命令列表
        **kwargs: 其他配置參數
    
    Returns:
        ClickToTelegramConverter: 配置好的安全轉換器實例
    
    Example:
        >>> bot = create_secure_bot(
        >>>     "TOKEN", 
        >>>     my_cli_group,
        >>>     admin_users=[123456789],
        >>>     allowed_commands=['safe_command']
        >>> )
    """
    if not admin_users:
        raise ValueError("安全模式下必須指定管理員用戶")
    
    if isinstance(click_group_or_file, str):
        # 文件路徑
        return create_bot_from_cli_file(
            bot_token=bot_token,
            cli_file_path=click_group_or_file,
            admin_users=admin_users,
            commands_whitelist=allowed_commands,
            **kwargs
        )
    else:
        # Click群組
        return create_bot_from_click_group(
            bot_token=bot_token,
            click_group=click_group_or_file,
            admin_users=admin_users,
            commands_whitelist=allowed_commands,
            **kwargs
        )


def create_production_bot(
    bot_token: str,
    click_group_or_file: Any,
    admin_users: List[int],
    dangerous_commands: List[str] = None,
    custom_help: Dict[str, str] = None,
    **kwargs
) -> ClickToTelegramConverter:
    """
    創建生產環境Bot（帶安全限制）
    
    Args:
        bot_token: Telegram Bot Token
        click_group_or_file: Click群組對象或CLI文件路徑
        admin_users: 管理員用戶ID列表
        dangerous_commands: 危險命令黑名單
        custom_help: 自定義幫助文字
        **kwargs: 其他配置參數
    
    Returns:
        ClickToTelegramConverter: 配置好的生產環境轉換器實例
    
    Example:
        >>> bot = create_production_bot(
        >>>     "TOKEN",
        >>>     production_cli,
        >>>     admin_users=[123456789],
        >>>     dangerous_commands=['rm', 'delete', 'reset'],
        >>>     custom_help={'deploy': '🚀 部署到生產環境'}
        >>> )
    """
    # 生產環境預設的危險命令
    default_dangerous = ['rm', 'delete', 'reset', 'drop', 'truncate', 'destroy']
    dangerous_commands = (dangerous_commands or []) + default_dangerous
    
    if isinstance(click_group_or_file, str):
        return create_bot_from_cli_file(
            bot_token=bot_token,
            cli_file_path=click_group_or_file,
            admin_users=admin_users,
            commands_blacklist=dangerous_commands,
            custom_help=custom_help or {},
            enable_logging=True,
            **kwargs
        )
    else:
        return create_bot_from_click_group(
            bot_token=bot_token,
            click_group=click_group_or_file,
            admin_users=admin_users,
            commands_blacklist=dangerous_commands,
            custom_help=custom_help or {},
            enable_logging=True,
            **kwargs
        )
