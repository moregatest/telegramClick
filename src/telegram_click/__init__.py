"""
TelegramClick - 零侵入式Click CLI到Telegram Bot轉換器

讓你能夠5分鐘內將任何現有的Click CLI工具轉換為功能完整的Telegram Bot，
無需修改任何現有代碼。
"""

from .framework import ClickToTelegramConverter
from .types import TelegramClickConfig, ParameterType
from .decorators import telegram_bot
from .factory import (
    create_bot_from_click_group,
    create_bot_from_cli_file,
)

__version__ = "0.1.0"
__author__ = "Tung"
__email__ = "tung@example.com"
__description__ = "零侵入式Click CLI到Telegram Bot轉換器"

__all__ = [
    # 核心類
    "ClickToTelegramConverter",
    "TelegramClickConfig",
    "ParameterType",
    
    # 便利函數
    "telegram_bot",
    "create_bot_from_click_group", 
    "create_bot_from_cli_file",
    
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]
