"""
TelegramClick類型定義模組
"""

import click
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from telegram import Update


class ParameterType(Enum):
    """參數類型枚舉"""
    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"
    BOOLEAN = "boolean"
    FILE = "file"


@dataclass
class TelegramParameter:
    """Telegram參數定義"""
    name: str
    param_type: ParameterType
    required: bool = True
    choices: List[str] = field(default_factory=list)
    help_text: str = ""
    default: Any = None


@dataclass
class TelegramCommand:
    """Telegram命令定義"""
    name: str
    description: str
    parameters: List[TelegramParameter] = field(default_factory=list)
    callback: Callable = None
    parent: Optional['TelegramCommand'] = None
    subcommands: Dict[str, 'TelegramCommand'] = field(default_factory=dict)


@dataclass 
class TelegramClickConfig:
    """Telegram轉換配置"""
    bot_token: str
    cli_module_path: Optional[str] = None  # CLI模組路径
    cli_group: Optional[click.Group] = None  # 直接傳入的Click群組
    commands_whitelist: List[str] = field(default_factory=list)  # 允許的命令白名單
    commands_blacklist: List[str] = field(default_factory=list)  # 禁用的命令黑名單
    custom_help: Dict[str, str] = field(default_factory=dict)  # 自定義幫助文字
    admin_users: List[int] = field(default_factory=list)  # 管理員用戶ID
    enable_logging: bool = True  # 是否啟用日誌
    max_message_length: int = 4000  # 最大訊息長度


class TelegramClickContext:
    """命令執行上下文"""
    def __init__(self, update: Update, user_id: int, chat_id: int):
        self.update = update
        self.user_id = user_id
        self.chat_id = chat_id
        self.current_command: Optional[TelegramCommand] = None
        self.collected_params: Dict[str, Any] = {}
        self.current_param_index: int = 0
        self.required_params: List[click.Parameter] = []
        self.command_name: str = ""
        self.waiting_for_input: bool = False


@dataclass
class ConversionResult:
    """轉換結果"""
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[Exception] = None
