"""
TelegramClick CLI工具測試
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, Mock

from telegram_click.cli import main, create, wrap, script, info


class TestCLICommands:
    """測試CLI命令"""
    
    def setup_method(self):
        """設置測試環境"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """清理測試環境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_command_help(self):
        """測試主命令幫助"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "TelegramClick CLI工具" in result.output
    
    def test_version_option(self):
        """測試版本選項"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCreateCommand:
    """測試create命令"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_create_basic_project(self):
        """測試創建基礎項目"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(create, ['test-project'])
            assert result.exit_code == 0
            assert "項目 test-project 創建成功" in result.output
            
            # 檢查文件是否創建
            project_path = Path('test-project')
            assert project_path.exists()
            assert (project_path / 'main.py').exists()
            assert (project_path / '.env').exists()
            assert (project_path / 'README.md').exists()
            assert (project_path / 'pyproject.toml').exists()
    
    def test_create_project_exists(self):
        """測試創建已存在的項目"""
        with self.runner.isolated_filesystem():
            # 先創建目錄
            Path('existing-project').mkdir()
            
            result = self.runner.invoke(create, ['existing-project'])
            assert result.exit_code == 0
            assert "已存在" in result.output
    
    def test_create_advanced_template(self):
        """測試創建進階模板"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(create, ['advanced-project', '--template', 'advanced'])
            assert result.exit_code == 0
            
            # 檢查main.py內容是否為進階模板
            main_content = (Path('advanced-project') / 'main.py').read_text()
            assert "進階TelegramClick Bot應用" in main_content
            assert "admin_users" in main_content
    
    def test_create_production_template(self):
        """測試創建生產模板"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(create, ['prod-project', '--template', 'production'])
            assert result.exit_code == 0
            
            main_content = (Path('prod-project') / 'main.py').read_text()
            assert "生產級TelegramClick Bot應用" in main_content
            assert "production_telegram_bot" in main_content
    
    def test_create_without_uv(self):
        """測試創建不使用uv的項目"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(create, ['pip-project', '--no-use-uv'])
            assert result.exit_code == 0
            
            # 應該有requirements.txt而不是pyproject.toml
            project_path = Path('pip-project')
            assert (project_path / 'requirements.txt').exists()


class TestWrapCommand:
    """測試wrap命令"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_wrap_existing_cli(self):
        """測試包裝現有CLI"""
        with self.runner.isolated_filesystem():
            # 創建測試CLI文件
            cli_content = '''
import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', required=True)
def greet(name):
    return f"Hello {name}!"

if __name__ == "__main__":
    cli()
'''
            with open('test_cli.py', 'w') as f:
                f.write(cli_content)
            
            result = self.runner.invoke(wrap, ['test_cli.py'])
            assert result.exit_code == 0
            assert "包裝器創建成功" in result.output
            
            # 檢查生成的包裝器文件
            wrapper_path = Path('test_cli_bot.py')
            assert wrapper_path.exists()
            
            wrapper_content = wrapper_path.read_text()
            assert "create_bot_from_cli_file" in wrapper_content
            assert "test_cli.py" in wrapper_content
    
    def test_wrap_nonexistent_file(self):
        """測試包裝不存在的文件"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(wrap, ['nonexistent.py'])
            assert result.exit_code == 0
            assert "找不到CLI文件" in result.output
    
    def test_wrap_with_admin_users(self):
        """測試帶管理員用戶的包裝"""
        with self.runner.isolated_filesystem():
            # 創建測試CLI文件
            with open('test_cli.py', 'w') as f:
                f.write('import click\n@click.group()\ndef cli(): pass')
            
            result = self.runner.invoke(wrap, [
                'test_cli.py', 
                '--admin-users', '123,456,789'
            ])
            assert result.exit_code == 0
            
            wrapper_content = Path('test_cli_bot.py').read_text()
            assert "[123, 456, 789]" in wrapper_content
    
    def test_wrap_with_custom_output(self):
        """測試自定義輸出文件名"""
        with self.runner.isolated_filesystem():
            with open('test_cli.py', 'w') as f:
                f.write('import click\n@click.group()\ndef cli(): pass')
            
            result = self.runner.invoke(wrap, [
                'test_cli.py', 
                '--output', 'custom_bot.py'
            ])
            assert result.exit_code == 0
            assert Path('custom_bot.py').exists()
    
    def test_wrap_invalid_admin_users(self):
        """測試無效的管理員用戶ID"""
        with self.runner.isolated_filesystem():
            with open('test_cli.py', 'w') as f:
                f.write('import click\n@click.group()\ndef cli(): pass')
            
            result = self.runner.invoke(wrap, [
                'test_cli.py',
                '--admin-users', 'invalid,not_number'
            ])
            assert result.exit_code == 0
            assert "格式錯誤" in result.output


class TestScriptCommand:
    """測試script命令"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_script_conversion(self):
        """測試腳本轉換"""
        with self.runner.isolated_filesystem():
            # 創建原始腳本
            original_script = '''#!/usr/bin/env python3
import click

@click.group()
def cli():
    pass

@cli.command()
def hello():
    return "Hello!"

if __name__ == "__main__":
    cli()
'''
            with open('original.py', 'w') as f:
                f.write(original_script)
            
            result = self.runner.invoke(script, ['original.py'])
            assert result.exit_code == 0
            assert "uv script創建成功" in result.output
            
            # 檢查生成的uv script
            uv_script_path = Path('original_uv.py')
            assert uv_script_path.exists()
            
            uv_content = uv_script_path.read_text()
            assert "# /// script" in uv_content
            assert "telegram-click" in uv_content
            assert "click>=8.1.7" in uv_content
    
    def test_script_nonexistent_file(self):
        """測試轉換不存在的腳本文件"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(script, ['nonexistent.py'])
            assert result.exit_code == 0
            assert "找不到腳本文件" in result.output
    
    def test_script_custom_token_env(self):
        """測試自定義Token環境變數"""
        with self.runner.isolated_filesystem():
            with open('test.py', 'w') as f:
                f.write('print("test")')
            
            result = self.runner.invoke(script, [
                'test.py',
                '--token-env', 'CUSTOM_TOKEN'
            ])
            assert result.exit_code == 0


class TestInfoCommand:
    """測試info命令"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_info_display(self):
        """測試信息顯示"""
        result = self.runner.invoke(info)
        assert result.exit_code == 0
        assert "TelegramClick" in result.output
        assert "0.1.0" in result.output
        assert "功能特色" in result.output
        assert "零侵入式" in result.output
        assert "GitHub" in result.output


class TestTemplateGeneration:
    """測試模板生成功能"""
    
    def test_basic_template_content(self):
        """測試基礎模板內容"""
        from telegram_click.cli import _get_basic_template
        
        template = _get_basic_template()
        assert "基礎TelegramClick Bot應用" in template
        assert "telegram_bot" in template
        assert "@click.group()" in template
        assert "greet" in template
        assert "echo" in template
    
    def test_advanced_template_content(self):
        """測試進階模板內容"""
        from telegram_click.cli import _get_advanced_template
        
        template = _get_advanced_template()
        assert "進階TelegramClick Bot應用" in template
        assert "admin_users" in template
        assert "custom_help" in template
        assert "status" in template
        assert "backup" in template
        assert "deploy" in template
    
    def test_production_template_content(self):
        """測試生產模板內容"""
        from telegram_click.cli import _get_production_template
        
        template = _get_production_template()
        assert "生產級TelegramClick Bot應用" in template
        assert "production_telegram_bot" in template
        assert "logging" in template
        assert "dangerous_commands" in template
        assert "scale" in template
        assert "health" in template


class TestCodeGeneration:
    """測試代碼生成功能"""
    
    def test_wrapper_code_generation(self):
        """測試包裝器代碼生成"""
        from telegram_click.cli import _generate_wrapper_code
        
        code = _generate_wrapper_code(
            cli_file="test_cli.py",
            token_env="BOT_TOKEN", 
            admin_users=[123, 456]
        )
        
        assert "create_bot_from_cli_file" in code
        assert "test_cli.py" in code
        assert "BOT_TOKEN" in code
        assert "[123, 456]" in code
    
    def test_uv_script_generation(self):
        """測試uv script生成"""
        from telegram_click.cli import _generate_uv_script
        
        original = "print('hello')"
        uv_script = _generate_uv_script(original, "TOKEN")
        
        assert "# /// script" in uv_script
        assert "telegram-click" in uv_script
        assert "print('hello')" in uv_script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
