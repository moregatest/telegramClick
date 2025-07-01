"""
TelegramClick工具函數模組
"""

import inspect
import logging
import importlib.util
from pathlib import Path
from typing import Any, Optional, Dict, List
import click

from .types import ParameterType, TelegramParameter, ConversionResult

# 設置日誌
logger = logging.getLogger(__name__)


def setup_logging(enable: bool = True, level: str = "INFO"):
    """設置日誌配置"""
    if not enable:
        return
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_module_from_path(module_path: str) -> Any:
    """從路徑載入Python模組"""
    path = Path(module_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到CLI模組: {path}")
    
    try:
        spec = importlib.util.spec_from_file_location("cli_module", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"載入模組失敗: {e}")
        raise


def convert_click_param_to_telegram(click_param: click.Parameter) -> Optional[TelegramParameter]:
    """轉換Click參數為Telegram參數"""
    if isinstance(click_param, click.Option):
        param_type = ParameterType.TEXT
        choices = []
        
        # 判斷參數類型
        if isinstance(click_param.type, click.Choice):
            param_type = ParameterType.CHOICE
            choices = list(click_param.type.choices)
        elif click_param.type is click.BOOL:
            param_type = ParameterType.BOOLEAN
        elif click_param.type in (click.INT, click.FLOAT):
            param_type = ParameterType.NUMBER
        elif isinstance(click_param.type, click.File):
            param_type = ParameterType.FILE
        
        return TelegramParameter(
            name=click_param.name,
            param_type=param_type,
            required=click_param.required,
            choices=choices,
            help_text=click_param.help or "",
            default=click_param.default
        )
    
    elif isinstance(click_param, click.Argument):
        return TelegramParameter(
            name=click_param.name,
            param_type=ParameterType.TEXT,
            required=click_param.required,
            help_text="必需參數"
        )
    
    return None


def validate_and_convert_parameter_value(text: str, param: click.Parameter) -> ConversionResult:
    """驗證和轉換參數值"""
    try:
        param_type = param.type
        
        if param_type is click.INT:
            value = int(text)
        elif param_type is click.FLOAT:
            value = float(text)
        elif isinstance(param_type, click.Choice):
            if text not in param_type.choices:
                return ConversionResult(
                    success=False,
                    message=f"必須選擇: {', '.join(param_type.choices)}"
                )
            value = text
        elif param_type is click.BOOL:
            value = text.lower() in ('true', '1', 'yes', 'on', '是', 'y')
        else:
            value = text
        
        return ConversionResult(success=True, data=value)
        
    except ValueError as e:
        error_msg = "請輸入有效的數字" if param.type in (click.INT, click.FLOAT) else str(e)
        return ConversionResult(
            success=False, 
            message=error_msg,
            error=e
        )


def format_output_message(result: Any, max_length: int = 4000) -> str:
    """格式化輸出訊息"""
    if result is None:
        return "✅ 命令執行完成"
    
    output = str(result)
    
    if len(output) > max_length:
        output = output[:max_length-50] + "\n\n... (輸出過長，已截斷)"
    
    return f"✅ **執行結果：**\n```\n{output}\n```"


def extract_commands_from_click_group(group: click.Group) -> Dict[str, click.Command]:
    """從Click群組提取命令"""
    commands = {}
    
    for name, command in group.commands.items():
        commands[name] = command
        logger.debug(f"提取命令: {name}")
    
    return commands


def find_click_objects_in_module(module: Any) -> Dict[str, click.Command]:
    """在模組中查找Click命令和群組"""
    commands = {}
    
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        
        if isinstance(attr, click.Group):
            # 如果是群組，提取其中的命令
            group_commands = extract_commands_from_click_group(attr)
            commands.update(group_commands)
            logger.debug(f"找到Click群組: {attr_name}，包含 {len(group_commands)} 個命令")
            
        elif isinstance(attr, click.Command):
            commands[attr_name] = attr
            logger.debug(f"找到Click命令: {attr_name}")
    
    return commands


def is_user_authorized(user_id: int, admin_users: List[int]) -> bool:
    """檢查用戶是否有權限"""
    if not admin_users:  # 如果沒有設置管理員列表，允許所有用戶
        return True
    return user_id in admin_users


def should_include_command(name: str, whitelist: List[str], blacklist: List[str]) -> bool:
    """檢查是否應該包含這個命令"""
    if blacklist and name in blacklist:
        return False
    
    if whitelist:
        return name in whitelist
    
    return True


async def safe_call_function(func: Any, params: Dict[str, Any]) -> ConversionResult:
    """安全地調用函數（支援同步和異步）"""
    try:
        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            result = func(**params)
        
        return ConversionResult(success=True, data=result)
        
    except Exception as e:
        logger.error(f"函數調用失敗: {e}")
        return ConversionResult(
            success=False,
            message=f"執行錯誤：{str(e)}",
            error=e
        )


def escape_markdown_v2(text: str) -> str:
    """轉義MarkdownV2特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """截斷文字並添加省略號"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_parameter_display_name(param: click.Parameter) -> str:
    """獲取參數的顯示名稱"""
    if isinstance(param, click.Option):
        return param.name
    elif isinstance(param, click.Argument):
        return param.name
    return "未知參數"


def format_command_help(command: click.Command, custom_help: Dict[str, str]) -> str:
    """格式化命令幫助文字"""
    command_name = command.name
    
    # 使用自定義幫助或原始幫助
    description = custom_help.get(command_name, command.help or "無描述")
    
    help_text = f"🔸 `/{command_name}` - {description}\n"
    
    # 顯示參數資訊
    if hasattr(command, 'params') and command.params:
        help_text += "   參數：\n"
        for param in command.params:
            if isinstance(param, click.Option):
                required = "✳️" if param.required else "🔸"
                param_help = param.help or "無說明"
                help_text += f"   {required} `--{param.name}`: {param_help}\n"
    
    return help_text
