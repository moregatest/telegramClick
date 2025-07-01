"""
TelegramClick工具函數測試
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import click

from telegram_click.utils import (
    load_module_from_path,
    convert_click_param_to_telegram,
    validate_and_convert_parameter_value,
    format_output_message,
    extract_commands_from_click_group,
    find_click_objects_in_module,
    is_user_authorized,
    should_include_command,
    escape_markdown_v2,
    truncate_text,
    format_command_help
)
from telegram_click.types import ParameterType


class TestModuleLoading:
    """測試模組載入功能"""
    
    def test_load_module_from_path(self):
        """測試從路徑載入模組"""
        # 創建臨時Python文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
import click

@click.group()
def test_cli():
    pass

@test_cli.command()
def hello():
    return "Hello!"
''')
            temp_path = f.name
        
        try:
            module = load_module_from_path(temp_path)
            assert hasattr(module, 'test_cli')
            assert hasattr(module, 'click')
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_module(self):
        """測試載入不存在的模組"""
        with pytest.raises(FileNotFoundError):
            load_module_from_path("nonexistent.py")


class TestParameterValidation:
    """測試參數驗證和轉換"""
    
    def test_validate_int_parameter(self):
        """測試整數參數驗證"""
        param = click.Option(['--count'], type=click.INT)
        
        # 有效整數
        result = validate_and_convert_parameter_value("42", param)
        assert result.success == True
        assert result.data == 42
        
        # 無效整數
        result = validate_and_convert_parameter_value("not_a_number", param)
        assert result.success == False
        assert "有效的數字" in result.message
    
    def test_validate_float_parameter(self):
        """測試浮點數參數驗證"""
        param = click.Option(['--rate'], type=click.FLOAT)
        
        # 有效浮點數
        result = validate_and_convert_parameter_value("3.14", param)
        assert result.success == True
        assert result.data == 3.14
        
        # 無效浮點數
        result = validate_and_convert_parameter_value("not_a_float", param)
        assert result.success == False
    
    def test_validate_choice_parameter(self):
        """測試選擇參數驗證"""
        param = click.Option(['--choice'], type=click.Choice(['a', 'b', 'c']))
        
        # 有效選擇
        result = validate_and_convert_parameter_value("a", param)
        assert result.success == True
        assert result.data == "a"
        
        # 無效選擇
        result = validate_and_convert_parameter_value("d", param)
        assert result.success == False
        assert "必須選擇" in result.message
    
    def test_validate_boolean_parameter(self):
        """測試布林參數驗證"""
        param = click.Option(['--flag'], type=click.BOOL)
        
        # True值
        for true_val in ['true', '1', 'yes', 'on', '是', 'y']:
            result = validate_and_convert_parameter_value(true_val, param)
            assert result.success == True
            assert result.data == True
        
        # False值
        result = validate_and_convert_parameter_value("false", param)
        assert result.success == True
        assert result.data == False
    
    def test_validate_text_parameter(self):
        """測試文字參數驗證"""
        param = click.Option(['--text'], type=str)
        
        result = validate_and_convert_parameter_value("hello world", param)
        assert result.success == True
        assert result.data == "hello world"


class TestOutputFormatting:
    """測試輸出格式化"""
    
    def test_format_output_message_none(self):
        """測試None結果格式化"""
        result = format_output_message(None)
        assert result == "✅ 命令執行完成"
    
    def test_format_output_message_text(self):
        """測試文字結果格式化"""
        result = format_output_message("Hello World")
        assert "Hello World" in result
        assert "執行結果" in result
    
    def test_format_output_message_long_text(self):
        """測試長文字截斷"""
        long_text = "A" * 5000
        result = format_output_message(long_text, max_length=100)
        assert len(result) < 200  # 應該被截斷
        assert "截斷" in result
    
    def test_format_output_message_custom_length(self):
        """測試自定義長度限制"""
        text = "Hello World"
        result = format_output_message(text, max_length=5)
        assert "截斷" in result


class TestClickExtraction:
    """測試Click命令提取"""
    
    def test_extract_commands_from_group(self):
        """測試從群組提取命令"""
        @click.group()
        def test_group():
            pass

        @test_group.command()
        def cmd1():
            pass

        @test_group.command()
        def cmd2():
            pass

        commands = extract_commands_from_click_group(test_group)
        assert len(commands) == 2
        assert "cmd1" in commands
        assert "cmd2" in commands
    
    def test_find_click_objects_in_module(self):
        """測試在模組中查找Click對象"""
        # 創建模擬模組
        class MockModule:
            @click.group()
            def cli():
                pass

            @click.command()
            def standalone():
                pass
            
            def not_click_function():
                pass
            
            regular_variable = "not_click"

        module = MockModule()
        commands = find_click_objects_in_module(module)
        
        # 應該找到standalone命令，但不包括群組內的命令
        assert "standalone" in commands
        assert isinstance(commands["standalone"], click.Command)


class TestAuthorizationAndFiltering:
    """測試授權和過濾功能"""
    
    def test_is_user_authorized_no_admin_list(self):
        """測試無管理員列表時的授權"""
        assert is_user_authorized(123, []) == True
        assert is_user_authorized(456, []) == True
    
    def test_is_user_authorized_with_admin_list(self):
        """測試有管理員列表時的授權"""
        admin_users = [123, 456]
        assert is_user_authorized(123, admin_users) == True
        assert is_user_authorized(456, admin_users) == True
        assert is_user_authorized(789, admin_users) == False
    
    def test_should_include_command_no_filters(self):
        """測試無過濾器時的命令包含"""
        assert should_include_command("test", [], []) == True
    
    def test_should_include_command_whitelist(self):
        """測試白名單過濾"""
        whitelist = ["allowed1", "allowed2"]
        assert should_include_command("allowed1", whitelist, []) == True
        assert should_include_command("not_allowed", whitelist, []) == False
    
    def test_should_include_command_blacklist(self):
        """測試黑名單過濾"""
        blacklist = ["forbidden1", "forbidden2"]
        assert should_include_command("allowed", [], blacklist) == True
        assert should_include_command("forbidden1", [], blacklist) == False
    
    def test_should_include_command_both_filters(self):
        """測試同時有白名單和黑名單"""
        whitelist = ["allowed"]
        blacklist = ["allowed"]  # 黑名單優先
        assert should_include_command("allowed", whitelist, blacklist) == False


class TestTextUtilities:
    """測試文字處理工具"""
    
    def test_escape_markdown_v2(self):
        """測試MarkdownV2轉義"""
        text = "Hello_world*test[link](url)"
        escaped = escape_markdown_v2(text)
        assert "\\_" in escaped
        assert "\\*" in escaped
        assert "\\[" in escaped
        assert "\\]" in escaped
        assert "\\(" in escaped
        assert "\\)" in escaped
    
    def test_truncate_text_short(self):
        """測試短文字不截斷"""
        text = "Hello"
        result = truncate_text(text, 10)
        assert result == "Hello"
    
    def test_truncate_text_long(self):
        """測試長文字截斷"""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, 10)
        assert len(result) == 10
        assert result.endswith("...")
    
    def test_truncate_text_exact_length(self):
        """測試恰好達到長度限制"""
        text = "1234567890"
        result = truncate_text(text, 10)
        assert result == text


class TestCommandHelp:
    """測試命令幫助格式化"""
    
    def test_format_command_help_basic(self):
        """測試基本命令幫助格式化"""
        @click.command()
        def test_cmd():
            """測試命令"""
            pass
        
        test_cmd.name = "test"
        help_text = format_command_help(test_cmd, {})
        
        assert "/test" in help_text
        assert "測試命令" in help_text
    
    def test_format_command_help_custom(self):
        """測試自定義幫助文字"""
        @click.command()
        def test_cmd():
            """原始幫助"""
            pass
        
        test_cmd.name = "test"
        custom_help = {"test": "自定義幫助文字"}
        help_text = format_command_help(test_cmd, custom_help)
        
        assert "自定義幫助文字" in help_text
        assert "原始幫助" not in help_text
    
    def test_format_command_help_with_params(self):
        """測試帶參數的命令幫助"""
        @click.command()
        @click.option('--name', required=True, help='用戶名稱')
        @click.option('--age', type=int, help='用戶年齡')
        def test_cmd(name, age):
            """測試命令"""
            pass
        
        test_cmd.name = "test"
        help_text = format_command_help(test_cmd, {})
        
        assert "參數：" in help_text
        assert "--name" in help_text
        assert "--age" in help_text
        assert "用戶名稱" in help_text
        assert "用戶年齡" in help_text
        assert "✳️" in help_text  # 必需參數標記
        assert "🔸" in help_text  # 可選參數標記


class TestAsyncFunctions:
    """測試異步函數"""
    
    @pytest.mark.asyncio
    async def test_safe_call_function_sync(self):
        """測試安全調用同步函數"""
        from telegram_click.utils import safe_call_function
        
        def sync_func(x, y):
            return x + y
        
        result = await safe_call_function(sync_func, {"x": 1, "y": 2})
        assert result.success == True
        assert result.data == 3
    
    @pytest.mark.asyncio
    async def test_safe_call_function_async(self):
        """測試安全調用異步函數"""
        from telegram_click.utils import safe_call_function
        
        async def async_func(x, y):
            return x * y
        
        result = await safe_call_function(async_func, {"x": 3, "y": 4})
        assert result.success == True
        assert result.data == 12
    
    @pytest.mark.asyncio
    async def test_safe_call_function_error(self):
        """測試安全調用函數錯誤處理"""
        from telegram_click.utils import safe_call_function
        
        def error_func():
            raise ValueError("測試錯誤")
        
        result = await safe_call_function(error_func, {})
        assert result.success == False
        assert "測試錯誤" in result.message
        assert isinstance(result.error, ValueError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
