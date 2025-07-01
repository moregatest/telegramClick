"""
TelegramClick核心框架測試
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import click
from telegram import Update, User, Chat, Message
from telegram.ext import CallbackContext

from telegram_click import (
    ClickToTelegramConverter,
    TelegramClickConfig,
    create_bot_from_click_group,
    telegram_bot
)
from telegram_click.types import ParameterType
from telegram_click.utils import convert_click_param_to_telegram


class TestClickToTelegramConverter:
    """測試核心轉換器"""
    
    @pytest.fixture
    def sample_cli(self):
        """創建測試用的Click CLI"""
        @click.group()
        def test_cli():
            """測試CLI"""
            pass

        @test_cli.command()
        @click.option('--name', required=True, help='姓名')
        @click.option('--age', type=int, help='年齡')
        def greet(name, age):
            """問候命令"""
            age_text = f"，{age}歲" if age else ""
            return f"Hello {name}{age_text}!"

        @test_cli.command()
        @click.option('--choice', type=click.Choice(['a', 'b', 'c']), required=True)
        @click.option('--flag', is_flag=True)
        def test_params(choice, flag):
            """測試參數類型"""
            return f"Choice: {choice}, Flag: {flag}"

        return test_cli
    
    @pytest.fixture
    def config(self):
        """測試配置"""
        return TelegramClickConfig(
            bot_token="test_token",
            enable_logging=False
        )
    
    @pytest.fixture
    def mock_update(self):
        """創建模擬的Update對象"""
        user = User(id=123, first_name="Test", is_bot=False)
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user,
            text="/test"
        )
        
        update = Update(
            update_id=1,
            message=message
        )
        
        return update
    
    def test_config_creation(self, config):
        """測試配置創建"""
        assert config.bot_token == "test_token"
        assert config.enable_logging == False
        assert config.commands_whitelist == []
        assert config.commands_blacklist == []
    
    def test_converter_initialization(self, sample_cli, config):
        """測試轉換器初始化"""
        config.cli_group = sample_cli
        
        converter = ClickToTelegramConverter(config)
        
        assert len(converter.click_commands) == 2
        assert "greet" in converter.click_commands
        assert "test_params" in converter.click_commands
    
    def test_command_filtering_whitelist(self, sample_cli, config):
        """測試命令白名單過濾"""
        config.cli_group = sample_cli
        config.commands_whitelist = ["greet"]
        
        converter = ClickToTelegramConverter(config)
        
        assert len(converter.click_commands) == 1
        assert "greet" in converter.click_commands
        assert "test_params" not in converter.click_commands
    
    def test_command_filtering_blacklist(self, sample_cli, config):
        """測試命令黑名單過濾"""
        config.cli_group = sample_cli
        config.commands_blacklist = ["test_params"]
        
        converter = ClickToTelegramConverter(config)
        
        assert len(converter.click_commands) == 1
        assert "greet" in converter.click_commands
        assert "test_params" not in converter.click_commands
    
    @pytest.mark.asyncio
    async def test_start_handler(self, sample_cli, config, mock_update):
        """測試/start命令處理"""
        config.cli_group = sample_cli
        converter = ClickToTelegramConverter(config)
        
        # 模擬reply_text方法
        mock_update.message.reply_text = AsyncMock()
        
        await converter._handle_start(mock_update, None)
        
        # 驗證回復被調用
        mock_update.message.reply_text.assert_called_once()
        
        # 檢查回復內容包含命令列表
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "/greet" in call_args
        assert "/test_params" in call_args
    
    @pytest.mark.asyncio
    async def test_admin_authorization(self, sample_cli, config, mock_update):
        """測試管理員權限"""
        config.cli_group = sample_cli
        config.admin_users = [999]  # 不包含測試用戶ID 123
        
        converter = ClickToTelegramConverter(config)
        mock_update.message.reply_text = AsyncMock()
        
        await converter._handle_start(mock_update, None)
        
        # 應該收到權限拒絕消息
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "沒有使用此機器人的權限" in call_args


class TestParameterConversion:
    """測試參數轉換"""
    
    def test_text_option_conversion(self):
        """測試文字選項轉換"""
        option = click.Option(['--name'], required=True, help='姓名')
        telegram_param = convert_click_param_to_telegram(option)
        
        assert telegram_param.name == 'name'
        assert telegram_param.param_type == ParameterType.TEXT
        assert telegram_param.required == True
        assert telegram_param.help_text == '姓名'
    
    def test_choice_option_conversion(self):
        """測試選擇選項轉換"""
        option = click.Option(['--choice'], type=click.Choice(['a', 'b', 'c']))
        telegram_param = convert_click_param_to_telegram(option)
        
        assert telegram_param.param_type == ParameterType.CHOICE
        assert telegram_param.choices == ['a', 'b', 'c']
    
    def test_boolean_option_conversion(self):
        """測試布林選項轉換"""
        option = click.Option(['--flag'], is_flag=True)
        telegram_param = convert_click_param_to_telegram(option)
        
        assert telegram_param.param_type == ParameterType.BOOLEAN
    
    def test_number_option_conversion(self):
        """測試數字選項轉換"""
        int_option = click.Option(['--count'], type=click.INT)
        telegram_param = convert_click_param_to_telegram(int_option)
        
        assert telegram_param.param_type == ParameterType.NUMBER
        
        float_option = click.Option(['--rate'], type=click.FLOAT)
        telegram_param = convert_click_param_to_telegram(float_option)
        
        assert telegram_param.param_type == ParameterType.NUMBER
    
    def test_argument_conversion(self):
        """測試參數轉換"""
        argument = click.Argument(['filename'])
        telegram_param = convert_click_param_to_telegram(argument)
        
        assert telegram_param.name == 'filename'
        assert telegram_param.param_type == ParameterType.TEXT
        assert telegram_param.required == True


class TestFactoryFunctions:
    """測試工廠函數"""
    
    def test_create_bot_from_click_group(self):
        """測試從Click群組創建Bot"""
        @click.group()
        def test_cli():
            pass

        @test_cli.command()
        def hello():
            return "Hello!"

        bot = create_bot_from_click_group("test_token", test_cli)
        
        assert isinstance(bot, ClickToTelegramConverter)
        assert "hello" in bot.click_commands
    
    def test_create_bot_with_admin_users(self):
        """測試創建帶管理員限制的Bot"""
        @click.group()
        def test_cli():
            pass

        bot = create_bot_from_click_group(
            "test_token", 
            test_cli,
            admin_users=[123, 456]
        )
        
        assert bot.config.admin_users == [123, 456]
    
    def test_create_bot_with_custom_help(self):
        """測試創建帶自定義幫助的Bot"""
        @click.group()
        def test_cli():
            pass

        @test_cli.command()
        def deploy():
            pass

        custom_help = {"deploy": "🚀 部署應用"}
        bot = create_bot_from_click_group(
            "test_token",
            test_cli,
            custom_help=custom_help
        )
        
        assert bot.config.custom_help == custom_help


class TestDecorators:
    """測試裝飾器"""
    
    def test_telegram_bot_decorator(self):
        """測試telegram_bot裝飾器"""
        @telegram_bot("test_token")
        @click.group()
        def test_cli():
            pass

        @test_cli.command()
        def hello():
            return "Hello!"

        # 檢查Bot功能被附加到CLI
        assert hasattr(test_cli, 'telegram_bot')
        assert hasattr(test_cli, 'run_telegram_bot')
        assert hasattr(test_cli, 'get_bot_info')
        
        # 檢查Bot信息
        info = test_cli.get_bot_info()
        assert 'commands_count' in info
        assert info['commands_count'] == 1
    
    def test_decorator_with_admin_users(self):
        """測試帶管理員用戶的裝飾器"""
        @telegram_bot("test_token", admin_users=[123])
        @click.group()
        def test_cli():
            pass

        info = test_cli.get_bot_info()
        assert info['admin_users'] == [123]


class TestUtilityFunctions:
    """測試工具函數"""
    
    def test_should_include_command(self):
        """測試命令包含判斷"""
        from telegram_click.utils import should_include_command
        
        # 無限制時應該包含
        assert should_include_command("test", [], []) == True
        
        # 白名單測試
        assert should_include_command("test", ["test"], []) == True
        assert should_include_command("test", ["other"], []) == False
        
        # 黑名單測試
        assert should_include_command("test", [], ["test"]) == False
        assert should_include_command("test", [], ["other"]) == True
    
    def test_is_user_authorized(self):
        """測試用戶授權"""
        from telegram_click.utils import is_user_authorized
        
        # 無管理員列表時允許所有用戶
        assert is_user_authorized(123, []) == True
        
        # 有管理員列表時只允許列表中的用戶
        assert is_user_authorized(123, [123, 456]) == True
        assert is_user_authorized(789, [123, 456]) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
