#!/usr/bin/env python3
"""
基礎使用範例：展示TelegramClick的基本功能
"""

import os
import sys
import click
from dotenv import load_dotenv
from telegram_click import telegram_bot

# 載入環境變數
load_dotenv()

@telegram_bot(os.getenv("TELEGRAM_TOKEN"))
@click.group()
def my_tools():
    """我的工具箱"""
    pass

@my_tools.command()
@click.option('--name', required=True, help='您的姓名')
@click.option('--age', type=int, help='您的年齡（可選）')
@click.option('--formal', is_flag=True, help='是否使用正式問候')
def greet(name: str, age: int = None, formal: bool = False):
    """問候命令
    
    這個命令會根據提供的參數生成個性化的問候語。
    """
    greeting = "您好" if formal else "嗨"
    age_text = f"，{age}歲" if age else ""
    
    if formal:
        return f"{greeting} {name}先生/女士{age_text}，很榮幸認識您！"
    else:
        return f"{greeting} {name}{age_text}！很高興見到你！😊"

@my_tools.command()
@click.option('--text', required=True, help='要回應的文字')
@click.option('--times', type=int, default=1, help='重複次數')
@click.option('--uppercase', is_flag=True, help='是否轉換為大寫')
def echo(text: str, times: int, uppercase: bool):
    """回聲命令
    
    重複輸出指定的文字。
    """
    output_text = text.upper() if uppercase else text
    result = []
    
    for i in range(times):
        result.append(f"{i+1}. {output_text}")
    
    return "🔊 Echo 結果：\n" + "\n".join(result)

@my_tools.command()
@click.option('--operation', 
              type=click.Choice(['add', 'subtract', 'multiply', 'divide']),
              required=True,
              help='運算類型')
@click.option('--a', type=float, required=True, help='第一個數字')
@click.option('--b', type=float, required=True, help='第二個數字')
def calc(operation: str, a: float, b: float):
    """簡單計算器
    
    執行基本的數學運算。
    """
    operations = {
        'add': (a + b, '+'),
        'subtract': (a - b, '-'),
        'multiply': (a * b, '×'),
        'divide': (a / b if b != 0 else "錯誤：除數不能為零", '÷')
    }
    
    result, symbol = operations[operation]
    
    if isinstance(result, str):  # 錯誤情況
        return f"❌ {result}"
    
    return f"🧮 計算結果：\n{a} {symbol} {b} = {result}"

@my_tools.command()
@click.option('--message', required=True, help='要處理的訊息')
@click.option('--action',
              type=click.Choice(['count', 'reverse', 'words', 'upper', 'lower']),
              required=True,
              help='處理動作')
def text_process(message: str, action: str):
    """文字處理工具
    
    對文字執行各種處理操作。
    """
    actions = {
        'count': f"📏 字符數量：{len(message)}",
        'reverse': f"🔄 反轉結果：{message[::-1]}",
        'words': f"📝 單詞數量：{len(message.split())}",
        'upper': f"🔤 大寫結果：{message.upper()}",
        'lower': f"🔡 小寫結果：{message.lower()}"
    }
    
    return actions[action]

@my_tools.command()
@click.option('--from-unit',
              type=click.Choice(['celsius', 'fahrenheit', 'kelvin']),
              required=True,
              help='原始溫度單位')
@click.option('--to-unit',
              type=click.Choice(['celsius', 'fahrenheit', 'kelvin']),
              required=True,
              help='目標溫度單位')
@click.option('--temperature', type=float, required=True, help='溫度值')
def convert_temp(from_unit: str, to_unit: str, temperature: float):
    """溫度轉換器
    
    在攝氏度、華氏度和開氏度之間轉換溫度。
    """
    # 先轉換為攝氏度
    if from_unit == 'fahrenheit':
        celsius = (temperature - 32) * 5/9
    elif from_unit == 'kelvin':
        celsius = temperature - 273.15
    else:  # celsius
        celsius = temperature
    
    # 從攝氏度轉換為目標單位
    if to_unit == 'fahrenheit':
        result = celsius * 9/5 + 32
        unit_symbol = '°F'
    elif to_unit == 'kelvin':
        result = celsius + 273.15
        unit_symbol = 'K'
    else:  # celsius
        result = celsius
        unit_symbol = '°C'
    
    return f"🌡️ 溫度轉換：\n{temperature}°{from_unit[0].upper()} = {result:.2f}{unit_symbol}"

def main():
    """主程序入口"""
    if not os.getenv("TELEGRAM_TOKEN"):
        print("❌ 請在 .env 文件中設置 TELEGRAM_TOKEN")
        print("或設置環境變數：export TELEGRAM_TOKEN=your_bot_token")
        sys.exit(1)
    
    print("🎯 TelegramClick 基礎範例")
    print("=" * 40)
    
    # 智能運行模式
    if len(sys.argv) > 1:
        # CLI模式
        print("📟 CLI模式啟動")
        my_tools()
    else:
        # Telegram Bot模式
        print("🤖 Telegram Bot模式啟動")
        print(f"📝 已註冊 {len(my_tools.commands)} 個命令")
        print("💬 在Telegram中發送 /start 開始使用")
        my_tools.run_telegram_bot()

if __name__ == "__main__":
    main()
