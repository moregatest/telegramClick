#!/usr/bin/env python3
"""
DevOps運維Bot範例：展示TelegramClick在DevOps場景中的應用
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import click
from dotenv import load_dotenv
from telegram_click import telegram_bot

# 載入環境變數
load_dotenv()

# 解析管理員用戶
admin_users = []
if os.getenv("ADMIN_USERS"):
    admin_users = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",") if x.strip()]

@telegram_bot(
    bot_token=os.getenv("TELEGRAM_TOKEN"),
    admin_users=admin_users,
    custom_help={
        'service': '🔧 管理系統服務 (start/stop/restart)',
        'logs': '📋 查看應用日誌',
        'backup': '💾 備份重要數據',
        'deploy': '🚀 部署應用到不同環境',
        'monitor': '📊 監控系統資源使用情況',
        'healthcheck': '🏥 檢查服務健康狀態',
        'config': '⚙️ 管理應用配置',
    }
)
@click.group()
def devops():
    """DevOps運維工具箱"""
    pass

@devops.command()
@click.option('--name', required=True, help='服務名稱')
@click.option('--action', 
              type=click.Choice(['start', 'stop', 'restart', 'status']),
              required=True,
              help='服務操作')
@click.option('--force', is_flag=True, help='強制執行（用於stop操作）')
def service(name: str, action: str, force: bool):
    """系統服務管理
    
    管理系統服務的啟動、停止、重啟和狀態查詢。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 模擬服務狀態
    service_status = {
        'nginx': 'running',
        'mysql': 'running', 
        'redis': 'stopped',
        'docker': 'running',
        'postgresql': 'running'
    }
    
    current_status = service_status.get(name, 'unknown')
    
    if action == 'status':
        status_emoji = "✅" if current_status == 'running' else "❌"
        return f"📊 **服務狀態查詢**\n🔍 服務：{name}\n{status_emoji} 狀態：{current_status}\n🕒 查詢時間：{timestamp}"
    
    elif action == 'start':
        if current_status == 'running':
            return f"⚠️ 服務 {name} 已經在運行中"
        return f"✅ **服務啟動**\n🔧 正在啟動 {name}...\n⏱️ 預計耗時：5-10秒\n🕒 操作時間：{timestamp}"
    
    elif action == 'stop':
        if current_status == 'stopped':
            return f"⚠️ 服務 {name} 已經停止"
        force_text = " (強制)" if force else ""
        return f"🛑 **服務停止**\n🔧 正在停止 {name}{force_text}...\n⏱️ 預計耗時：3-5秒\n🕒 操作時間：{timestamp}"
    
    elif action == 'restart':
        return f"🔄 **服務重啟**\n🔧 正在重啟 {name}...\n⏱️ 預計耗時：10-15秒\n🕒 操作時間：{timestamp}"

@devops.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--level',
              type=click.Choice(['error', 'warn', 'info', 'debug']),
              default='error',
              help='日誌級別')
@click.option('--lines', type=int, default=50, help='顯示行數')
@click.option('--grep', help='搜索關鍵字')
@click.option('--follow', is_flag=True, help='持續追蹤日誌')
def logs(app: str, level: str, lines: int, grep: str, follow: bool):
    """應用日誌查看
    
    查看和搜索應用日誌，支援不同級別的日誌過濾。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 模擬日誌內容
    sample_logs = {
        'web': [
            "2025-01-01 10:30:15 [INFO] Application started successfully",
            "2025-01-01 10:30:16 [WARN] Database connection pool reaching limit", 
            "2025-01-01 10:30:17 [ERROR] Failed to process user request: timeout",
            "2025-01-01 10:30:18 [INFO] Request completed in 245ms",
            "2025-01-01 10:30:19 [DEBUG] Cache hit rate: 89%"
        ],
        'api': [
            "2025-01-01 10:31:01 [INFO] API server listening on port 8080",
            "2025-01-01 10:31:02 [ERROR] Redis connection failed",
            "2025-01-01 10:31:03 [WARN] Rate limit exceeded for user 12345"
        ]
    }
    
    app_logs = sample_logs.get(app, [f"[INFO] No specific logs for {app}"])
    
    # 級別過濾
    level_filter = {
        'error': ['ERROR'],
        'warn': ['ERROR', 'WARN'],
        'info': ['ERROR', 'WARN', 'INFO'],
        'debug': ['ERROR', 'WARN', 'INFO', 'DEBUG']
    }
    
    filtered_logs = []
    for log in app_logs:
        for log_level in level_filter[level]:
            if f"[{log_level}]" in log:
                filtered_logs.append(log)
                break
    
    # 關鍵字過濾
    if grep:
        filtered_logs = [log for log in filtered_logs if grep.lower() in log.lower()]
    
    # 限制行數
    display_logs = filtered_logs[-lines:]
    
    result = f"📋 **{app}** 日誌 ({timestamp})\n"
    result += f"🔍 級別：{level.upper()} | 行數：{len(display_logs)}"
    
    if grep:
        result += f" | 搜索：{grep}"
    if follow:
        result += " | 追蹤模式"
    
    result += "\n\n```\n"
    result += "\n".join(display_logs)
    result += "\n```"
    
    if follow:
        result += "\n\n⏳ 持續追蹤中...（實際應用中會定期更新）"
    
    return result

@devops.command()
@click.option('--source', required=True, help='備份來源路徑')
@click.option('--destination', help='備份目標路徑（預設為 /backup）')
@click.option('--compress', is_flag=True, help='是否壓縮備份')
@click.option('--exclude', multiple=True, help='排除的檔案模式')
@click.option('--incremental', is_flag=True, help='增量備份')
def backup(source: str, destination: str, compress: bool, exclude: tuple, incremental: bool):
    """數據備份
    
    備份重要數據到指定位置，支援壓縮和增量備份。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = destination or f"/backup/{timestamp}"
    
    result = f"💾 **數據備份任務**\n"
    result += f"📂 來源：{source}\n"
    result += f"📁 目標：{dest}\n"
    
    if compress:
        result += f"🗜️ 壓縮：啟用\n"
    
    if incremental:
        result += f"📈 類型：增量備份\n"
    else:
        result += f"📦 類型：完整備份\n"
    
    if exclude:
        result += f"🚫 排除：{', '.join(exclude)}\n"
    
    # 模擬備份大小和時間
    import random
    backup_size = random.randint(100, 5000)  # MB
    estimated_time = max(1, backup_size // 100)  # 估算時間
    
    result += f"\n📊 **預估信息**\n"
    result += f"💽 數據大小：~{backup_size} MB\n"
    result += f"⏱️ 預計耗時：{estimated_time} 分鐘\n"
    result += f"🕒 開始時間：{timestamp}\n"
    result += f"\n✅ 備份任務已啟動！"
    
    return result

@devops.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--env',
              type=click.Choice(['dev', 'staging', 'prod']),
              required=True,
              help='部署環境')
@click.option('--version', help='版本標籤')
@click.option('--rollback', is_flag=True, help='回滾到上一版本')
@click.option('--dry-run', is_flag=True, help='預演模式（不實際執行）')
def deploy(app: str, env: str, version: str, rollback: bool, dry_run: bool):
    """應用部署
    
    將應用部署到指定環境，支援版本指定和回滾。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if dry_run:
        result = f"🧪 **部署預演模式**\n"
    elif rollback:
        result = f"🔄 **應用回滾**\n"
    else:
        result = f"🚀 **應用部署**\n"
    
    result += f"📱 應用：{app}\n"
    result += f"🌍 環境：{env}\n"
    
    if rollback:
        result += f"↩️ 操作：回滾到上一版本\n"
    else:
        version_text = version or "latest"
        result += f"🏷️ 版本：{version_text}\n"
    
    # 環境特定的注意事項
    env_warnings = {
        'prod': "⚠️ **生產環境部署，請謹慎操作！**",
        'staging': "📋 測試環境，可進行功能驗證",
        'dev': "🛠️ 開發環境，可隨時部署"
    }
    
    result += f"\n{env_warnings[env]}\n"
    
    if not dry_run:
        # 模擬部署步驟
        steps = [
            "📥 下載新版本",
            "🔍 驗證檔案完整性", 
            "🛑 停止舊版本服務",
            "📂 更新應用檔案",
            "⚙️ 更新配置檔案",
            "🔄 啟動新版本服務",
            "🏥 健康檢查",
            "✅ 部署完成"
        ]
        
        result += f"\n📋 **部署步驟：**\n"
        for i, step in enumerate(steps, 1):
            result += f"{i}. {step}\n"
        
        result += f"\n⏱️ 預計耗時：3-5 分鐘\n"
        result += f"🕒 開始時間：{timestamp}"
    else:
        result += f"\n✅ 預演檢查通過，可以執行實際部署"
    
    return result

@devops.command()
@click.option('--resource',
              type=click.Choice(['cpu', 'memory', 'disk', 'network', 'all']),
              default='all',
              help='監控資源類型')
@click.option('--duration', type=int, default=60, help='監控時長（分鐘）')
@click.option('--alert-threshold', type=float, help='告警閾值（百分比）')
def monitor(resource: str, duration: int, alert_threshold: float):
    """系統監控
    
    監控系統資源使用情況，設置告警閾值。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 模擬資源使用數據
    import random
    resource_data = {
        'cpu': random.randint(20, 85),
        'memory': random.randint(30, 90),
        'disk': random.randint(40, 75),
        'network': random.randint(10, 60)
    }
    
    result = f"📊 **系統監控報告** ({timestamp})\n"
    result += f"⏱️ 監控時長：{duration} 分鐘\n\n"
    
    if resource == 'all':
        for res_name, usage in resource_data.items():
            emoji = "🔴" if usage > 80 else "🟡" if usage > 60 else "🟢"
            result += f"{emoji} {res_name.upper()}：{usage}%\n"
            
            if alert_threshold and usage > alert_threshold:
                result += f"   ⚠️ 超過告警閾值 {alert_threshold}%\n"
    else:
        usage = resource_data[resource]
        emoji = "🔴" if usage > 80 else "🟡" if usage > 60 else "🟢"
        result += f"{emoji} {resource.upper()} 使用率：{usage}%\n"
        
        if alert_threshold and usage > alert_threshold:
            result += f"⚠️ 已超過告警閾值 {alert_threshold}%\n"
            result += f"🚨 建議立即檢查系統狀態！\n"
    
    result += f"\n📈 **統計信息：**\n"
    result += f"🔄 更新頻率：每 30 秒\n"
    result += f"📊 數據保留：7 天\n"
    result += f"⏰ 下次更新：{duration} 分鐘後"
    
    return result

@devops.command()
@click.option('--url', required=True, help='檢查的URL或服務端點')
@click.option('--timeout', type=int, default=30, help='超時時間（秒）')
@click.option('--expected-status', type=int, default=200, help='期望的HTTP狀態碼')
@click.option('--check-content', help='檢查響應內容是否包含指定文字')
def healthcheck(url: str, timeout: int, expected_status: int, check_content: str):
    """健康檢查
    
    檢查服務的健康狀態，驗證HTTP響應和內容。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 模擬健康檢查結果
    import random
    response_time = random.randint(50, 500)  # ms
    is_healthy = random.choice([True, True, True, False])  # 75%健康率
    
    result = f"🏥 **健康檢查報告** ({timestamp})\n"
    result += f"🌐 URL：{url}\n"
    result += f"⏰ 超時設置：{timeout} 秒\n"
    result += f"📊 期望狀態：HTTP {expected_status}\n"
    
    if is_healthy:
        result += f"\n✅ **檢查結果：健康**\n"
        result += f"📈 響應時間：{response_time} ms\n"
        result += f"📊 HTTP狀態：{expected_status}\n"
        
        if check_content:
            result += f"✅ 內容檢查：包含 '{check_content}'\n"
    else:
        result += f"\n❌ **檢查結果：異常**\n"
        result += f"📈 響應時間：超時 ({timeout}s)\n"
        result += f"📊 HTTP狀態：503 Service Unavailable\n"
        result += f"🚨 **建議動作：**\n"
        result += f"1. 檢查服務是否正在運行\n"
        result += f"2. 驗證網路連接\n"
        result += f"3. 查看服務日誌\n"
    
    return result

@devops.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--key', required=True, help='配置鍵')
@click.option('--value', help='配置值（不提供則查看當前值）')
@click.option('--env',
              type=click.Choice(['dev', 'staging', 'prod']),
              default='dev',
              help='環境')
@click.option('--secret', is_flag=True, help='是否為敏感信息')
def config(app: str, key: str, value: str, env: str, secret: bool):
    """配置管理
    
    管理應用配置，支援不同環境的配置隔離。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if value is None:
        # 查看配置
        display_value = "***敏感信息***" if secret else "example_config_value"
        result = f"⚙️ **配置查詢** ({timestamp})\n"
        result += f"📱 應用：{app}\n"
        result += f"🌍 環境：{env}\n"
        result += f"🔑 配置鍵：{key}\n"
        result += f"💾 當前值：{display_value}\n"
        
        if secret:
            result += f"🔐 類型：敏感信息\n"
    else:
        # 設置配置
        display_value = "***已設置***" if secret else value
        result = f"⚙️ **配置更新** ({timestamp})\n"
        result += f"📱 應用：{app}\n"
        result += f"🌍 環境：{env}\n"
        result += f"🔑 配置鍵：{key}\n"
        result += f"✅ 新值：{display_value}\n"
        
        if secret:
            result += f"🔐 類型：敏感信息（已加密存儲）\n"
        
        result += f"\n📋 **注意事項：**\n"
        result += f"• 配置更新後需要重啟應用才能生效\n"
        result += f"• 建議在非生產環境先測試\n"
        
        if env == 'prod':
            result += f"⚠️ **生產環境配置變更，請謹慎操作！**"
    
    return result

def main():
    """主程序入口"""
    if not os.getenv("TELEGRAM_TOKEN"):
        print("❌ 請在 .env 文件中設置 TELEGRAM_TOKEN")
        print("📝 範例：TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh")
        sys.exit(1)
    
    print("🛠️ DevOps運維Bot範例")
    print("=" * 50)
    
    if not admin_users:
        print("⚠️ 警告：未設置管理員用戶，所有用戶都可以使用")
        print("📝 設置方法：ADMIN_USERS=123456789,987654321")
    else:
        print(f"👥 管理員用戶：{admin_users}")
    
    # 智能運行模式
    if len(sys.argv) > 1:
        # CLI模式
        print("📟 CLI模式啟動")
        devops()
    else:
        # Telegram Bot模式
        print("🤖 Telegram Bot模式啟動")
        print(f"📝 已註冊 {len(devops.commands)} 個運維命令")
        print("💬 在Telegram中發送 /start 開始使用")
        devops.run_telegram_bot()

if __name__ == "__main__":
    main()
