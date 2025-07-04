"""
TelegramClick核心框架模組
"""

import logging
from typing import Dict, List, Any, Optional
import click
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from .types import (
    TelegramClickConfig, 
    TelegramClickContext, 
    ParameterType,
    ConversionResult
)
from .utils import (
    setup_logging,
    load_module_from_path,
    convert_click_param_to_telegram,
    validate_and_convert_parameter_value,
    format_output_message,
    extract_commands_from_click_group,
    find_click_objects_in_module,
    is_user_authorized,
    should_include_command,
    safe_call_function,
    format_command_help
)

logger = logging.getLogger(__name__)


class ClickToTelegramConverter:
    """Click CLI到Telegram Bot的轉換器"""
    
    def __init__(self, config: TelegramClickConfig):
        self.config = config
        self.app = None  # 延遲初始化
        self.click_commands: Dict[str, click.Command] = {}
        self.command_name_mapping: Dict[str, str] = {}  # telegram_name -> original_name
        self.user_contexts: Dict[int, TelegramClickContext] = {}
        
        # 設置日誌
        setup_logging(config.enable_logging)
    
    def _discover_click_commands(self):
        """自動發現Click命令"""
        try:
            if self.config.cli_group:
                # 直接使用傳入的Click群組
                self._extract_commands_from_group(self.config.cli_group)
            elif self.config.cli_module_path:
                # 從模組路徑載入
                self._load_commands_from_module()
            else:
                raise ValueError("必須提供 cli_group 或 cli_module_path")
                
            logger.info(f"成功註冊 {len(self.click_commands)} 個命令")
            
        except Exception as e:
            logger.error(f"命令發現失敗: {e}")
            raise
    
    def _extract_commands_from_group(self, group: click.Group):
        """從Click群組提取命令"""
        commands = extract_commands_from_click_group(group)
        
        for name, command in commands.items():
            if should_include_command(
                name, 
                self.config.commands_whitelist, 
                self.config.commands_blacklist
            ):
                self.click_commands[name] = command
                logger.debug(f"註冊命令: {name}")
    
    def _load_commands_from_module(self):
        """從模組載入Click命令"""
        module = load_module_from_path(self.config.cli_module_path)
        commands = find_click_objects_in_module(module)
        
        for name, command in commands.items():
            if should_include_command(
                name,
                self.config.commands_whitelist,
                self.config.commands_blacklist
            ):
                self.click_commands[name] = command
                logger.debug(f"註冊命令: {name}")
    
    def _normalize_command_name(self, cmd_name: str) -> str:
        """將Click命令名轉換為有效的Telegram命令名"""
        # 替換破折號為下劃線，只保留字母數字和下劃線
        normalized = cmd_name.lower().replace('-', '_')
        # 確保只包含有效字符
        import re
        normalized = re.sub(r'[^a-z0-9_]', '', normalized)
        # 確保長度不超過32個字符
        return normalized[:32]
    
    def _setup_telegram_handlers(self):
        """設置Telegram處理器"""
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
        
        # 為每個Click命令創建Telegram命令處理器
        for cmd_name in self.click_commands:
            telegram_cmd_name = self._normalize_command_name(cmd_name)
            self.command_name_mapping[telegram_cmd_name] = cmd_name
            self.app.add_handler(CommandHandler(telegram_cmd_name, self._handle_click_command))
        
        logger.info("Telegram處理器設置完成")
    
    async def _handle_start(self, update: Update, context):
        """處理/start命令"""
        user_id = update.effective_user.id
        
        if not is_user_authorized(user_id, self.config.admin_users):
            await update.message.reply_text("❌ 您沒有使用此機器人的權限")
            return
        
        commands_list = "\n".join([f"🔹 /{name}" for name in self.click_commands.keys()])
        
        welcome_msg = (
            f"🤖 **CLI Bot 已啟動！**\n\n"
            f"這個機器人將您的CLI命令轉換為互動式界面。\n\n"
            f"**可用命令：**\n{commands_list}\n\n"
            f"使用 /help 獲取詳細說明"
        )
        
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"用戶 {user_id} 啟動了機器人")
    
    async def _handle_help(self, update: Update, context):
        """處理/help命令"""
        user_id = update.effective_user.id
        
        if not is_user_authorized(user_id, self.config.admin_users):
            await update.message.reply_text("❌ 您沒有使用此機器人的權限")
            return
        
        help_text = "📋 **命令說明：**\n\n"
        
        for name, cmd in self.click_commands.items():
            help_text += format_command_help(cmd, self.config.custom_help)
            help_text += "\n"
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_click_command(self, update: Update, context):
        """處理Click命令"""
        user_id = update.effective_user.id
        
        if not is_user_authorized(user_id, self.config.admin_users):
            await update.message.reply_text("❌ 您沒有使用此機器人的權限")
            return
        
        command_name = update.message.text[1:].split()[0]
        
        if command_name not in self.click_commands:
            await update.message.reply_text("❌ 未知命令")
            return
        
        # 創建用戶上下文
        chat_id = update.effective_chat.id
        self.user_contexts[user_id] = TelegramClickContext(update, user_id, chat_id)
        self.user_contexts[user_id].command_name = command_name
        
        logger.info(f"用戶 {user_id} 執行命令: {command_name}")
        
        # 開始參數收集
        await self._start_parameter_collection(user_id)
    
    async def _start_parameter_collection(self, user_id: int):
        """開始參數收集流程"""
        context = self.user_contexts[user_id]
        command = self.click_commands[context.command_name]
        
        # 分離必需和可選參數
        required_params = []
        optional_params = []
        if hasattr(command, 'params'):
            for param in command.params:
                if isinstance(param, (click.Option, click.Argument)):
                    if param.required:
                        required_params.append(param)
                    else:
                        optional_params.append(param)
        
        # 將所有參數合併，但保留分離信息
        all_params = required_params + optional_params
        
        if not all_params:
            # 沒有參數，直接執行
            await self._execute_click_command(user_id)
            return
        
        context.required_params = all_params
        await self._collect_next_parameter(user_id)
    
    async def _collect_next_parameter(self, user_id: int):
        """收集下一個參數"""
        context = self.user_contexts[user_id]
        required_params = context.required_params
        
        if context.current_param_index >= len(required_params):
            # 參數收集完成
            await self._execute_click_command(user_id)
            return
        
        param = required_params[context.current_param_index]
        
        # 根據參數類型生成UI
        if isinstance(param.type, click.Choice):
            await self._show_choice_parameter(user_id, param)
        elif param.type is click.BOOL:
            await self._show_boolean_parameter(user_id, param)
        else:
            await self._show_text_parameter(user_id, param)
    
    async def _show_choice_parameter(self, user_id: int, param: click.Parameter):
        """顯示選擇參數"""
        context = self.user_contexts[user_id]
        
        keyboard = []
        for choice in param.type.choices:
            callback_data = f"param:{param.name}:{choice}"
            keyboard.append([InlineKeyboardButton(choice, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        param_desc = param.help or f"選擇 {param.name}"
        message = f"🔸 **{param.name}**\n{param_desc}\n\n請選擇："
        
        await context.update.effective_chat.send_message(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_boolean_parameter(self, user_id: int, param: click.Parameter):
        """顯示布林參數"""
        context = self.user_contexts[user_id]
        
        # 如果是可選參數，提供三選一界面
        if not param.required:
            keyboard = []
            
            # 是/否選項
            keyboard.append([
                InlineKeyboardButton("✅ 是", callback_data=f"param:{param.name}:true"),
                InlineKeyboardButton("❌ 否", callback_data=f"param:{param.name}:false")
            ])
            
            # 使用默認值按鈕（如果有默認值）
            if param.default is not None:
                default_text = "是" if param.default else "否"
                keyboard.append([InlineKeyboardButton(f"📋 使用默認值 ({default_text})", callback_data=f"default:{param.name}")])
            
            # 跳過按鈕
            keyboard.append([InlineKeyboardButton("⏭️ 跳過", callback_data=f"skip:{param.name}")])
            
            param_desc = param.help or f"設置 {param.name}"
            message = f"🔸 {param.name} (可選)\n{param_desc}\n\n請選擇："
        else:
            # 必需參數，只提供是/否選項
            keyboard = [
                [
                    InlineKeyboardButton("✅ 是", callback_data=f"param:{param.name}:true"),
                    InlineKeyboardButton("❌ 否", callback_data=f"param:{param.name}:false")
                ]
            ]
            
            param_desc = param.help or f"設置 {param.name}"
            message = f"🔸 {param.name} (必需)\n{param_desc}\n\n請選擇："
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.update.effective_chat.send_message(
            message,
            reply_markup=reply_markup
        )
    
    async def _show_text_parameter(self, user_id: int, param: click.Parameter):
        """顯示文字參數"""
        context = self.user_contexts[user_id]
        
        param_type_hint = "文字"
        if param.type in (click.INT, click.FLOAT):
            param_type_hint = "數字"
        elif isinstance(param.type, click.File):
            param_type_hint = "檔案"
        
        param_desc = param.help or f"請輸入 {param.name}"
        
        # 如果是可選參數，提供選項按鈕
        if not param.required:
            keyboard = []
            
            # 輸入自定義值按鈕
            keyboard.append([InlineKeyboardButton("✏️ 輸入自定義值", callback_data=f"input:{param.name}")])
            
            # 使用默認值按鈕（如果有默認值）
            if param.default is not None:
                default_text = str(param.default)[:20] + ("..." if len(str(param.default)) > 20 else "")
                keyboard.append([InlineKeyboardButton(f"📋 使用默認值 ({default_text})", callback_data=f"default:{param.name}")])
            
            # 跳過按鈕
            keyboard.append([InlineKeyboardButton("⏭️ 跳過", callback_data=f"skip:{param.name}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"🔸 **{param.name}** (可選)\n{param_desc}\n\n請選擇："
            
            await context.update.effective_chat.send_message(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # 必需參數，直接要求輸入
            message = f"🔸 **{param.name}** (必需)\n{param_desc}\n\n請輸入{param_type_hint}："
            await context.update.effective_chat.send_message(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_callback(self, update: Update, context):
        """處理按鈕回調"""
        query = update.callback_query
        await query.answer()
        
        if (query.data.startswith("param:") or 
            query.data.startswith("input:") or 
            query.data.startswith("default:") or 
            query.data.startswith("skip:")):
            await self._handle_parameter_callback(query)
    
    async def _handle_parameter_callback(self, query):
        """處理參數按鈕回調"""
        user_id = query.from_user.id
        
        if user_id not in self.user_contexts:
            await query.edit_message_text("❌ 會話已過期，請重新開始")
            return
        
        context = self.user_contexts[user_id]
        callback_data = query.data
        
        if callback_data.startswith("input:"):
            # 用戶選擇輸入自定義值
            param_name = callback_data.split(":", 1)[1]
            await query.edit_message_text(f"✏️ 請輸入 {param_name} 的值：")
            # 設置狀態等待用戶輸入
            context.waiting_for_input = True
            
        elif callback_data.startswith("default:"):
            # 用戶選擇使用默認值
            param_name = callback_data.split(":", 1)[1]
            param = context.required_params[context.current_param_index]
            context.collected_params[param_name] = param.default
            context.current_param_index += 1
            await query.edit_message_text(f"📋 {param_name} = {param.default} (默認值)")
            await self._collect_next_parameter(user_id)
            
        elif callback_data.startswith("skip:"):
            # 用戶選擇跳過
            param_name = callback_data.split(":", 1)[1]
            context.collected_params[param_name] = None
            context.current_param_index += 1
            await query.edit_message_text(f"⏭️ 跳過 {param_name}")
            await self._collect_next_parameter(user_id)
            
        elif callback_data.startswith("param:"):
            # 處理原有的選擇和布林參數回調
            try:
                _, param_name, value = callback_data.split(":", 2)
            except ValueError:
                await query.edit_message_text("❌ 無效的回調數據")
                return
            
            # 轉換值
            if value == "true":
                value = True
            elif value == "false":
                value = False
            
            context.collected_params[param_name] = value
            context.current_param_index += 1
            
            await query.edit_message_text(f"✅ {param_name} = {value}")
            await self._collect_next_parameter(user_id)
    
    async def _handle_text(self, update: Update, context):
        """處理文字輸入"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_contexts:
            return
        
        user_context = self.user_contexts[user_id]
        required_params = user_context.required_params
        
        if user_context.current_param_index < len(required_params):
            param = required_params[user_context.current_param_index]
            
            # 檢查是否正在等待輸入（可選參數選擇了輸入自定義值）
            if user_context.waiting_for_input:
                # 驗證和轉換輸入
                result = validate_and_convert_parameter_value(update.message.text, param)
                
                if result.success:
                    user_context.collected_params[param.name] = result.data
                    user_context.current_param_index += 1
                    user_context.waiting_for_input = False
                    
                    await update.message.reply_text(f"✅ {param.name} = {result.data}")
                    await self._collect_next_parameter(user_id)
                else:
                    await update.message.reply_text(f"❌ {result.message}")
            elif param.required:
                # 必需參數的直接輸入
                result = validate_and_convert_parameter_value(update.message.text, param)
                
                if result.success:
                    user_context.collected_params[param.name] = result.data
                    user_context.current_param_index += 1
                    
                    await update.message.reply_text(f"✅ {param.name} = {result.data}")
                    await self._collect_next_parameter(user_id)
                else:
                    await update.message.reply_text(f"❌ {result.message}")
    
    async def _execute_click_command(self, user_id: int):
        """執行Click命令"""
        context = self.user_contexts[user_id]
        command = self.click_commands[context.command_name]
        
        logger.info(f"執行命令 {context.command_name}，參數: {context.collected_params}")
        
        # 調用命令函數
        result = await safe_call_function(command.callback, context.collected_params)
        
        if result.success:
            output_msg = format_output_message(result.data, self.config.max_message_length)
            await context.update.effective_chat.send_message(
                output_msg, 
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"命令 {context.command_name} 執行成功")
        else:
            await context.update.effective_chat.send_message(result.message)
            logger.error(f"命令 {context.command_name} 執行失敗: {result.error}")
        
        # 清理上下文
        del self.user_contexts[user_id]
    
    def run(self):
        """啟動Bot"""
        if not self.config.bot_token:
            raise ValueError("必須提供有效的 bot_token 才能啟動 Telegram Bot")
        
        # 創建 Telegram Application
        self.app = Application.builder().token(self.config.bot_token).build()
        
        # 在運行時才發現和註冊命令
        self._discover_click_commands()
        self._setup_telegram_handlers()
        
        logger.info("🚀 TelegramClick轉換器啟動中...")
        logger.info(f"📝 已註冊 {len(self.click_commands)} 個命令")
        
        try:
            self.app.run_polling()
        except KeyboardInterrupt:
            logger.info("機器人已停止")
        except Exception as e:
            logger.error(f"機器人運行錯誤: {e}")
            raise
