#!/usr/bin/env python3
"""
生產級TelegramClick Bot範例
展示完整的生產環境最佳實踐：安全性、監控、日誌、錯誤處理
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import click
from dotenv import load_dotenv
from telegram_click import production_telegram_bot

# 載入環境變數
load_dotenv()

# 配置日誌
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 解析管理員用戶
admin_users = []
if os.getenv("ADMIN_USERS"):
    try:
        admin_users = [int(x.strip()) for x in os.getenv("ADMIN_USERS").split(",") if x.strip()]
        logger.info(f"載入管理員用戶：{admin_users}")
    except ValueError:
        logger.error("ADMIN_USERS 格式錯誤，請使用逗號分隔的數字")
        sys.exit(1)

# 生產環境配置
@production_telegram_bot(
    TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN"),
    admin_users=admin_users,
    dangerous_commands=['reset_database', 'delete_all', 'format_disk'],
    custom_help={
        'status': '📊 查看生產環境系統狀態',
        'logs': '📋 查看應用日誌（支援搜索和過濾）',
        'scale': '📈 調整服務實例數量',
        'deploy': '🚀 部署應用到生產環境',
        'rollback': '🔄 回滾到上一個穩定版本',
        'alert': '🚨 管理告警規則和通知',
        'metrics': '📊 查看關鍵性能指標',
        'maintenance': '🔧 進入/退出維護模式',
    }
)
@click.group()
def production_ops():
    """生產環境運維中心
    
    這是一個生產級的Telegram Bot，提供完整的運維功能，
    包括服務管理、監控、部署、告警等。
    
    安全特性：
    - 管理員用戶限制
    - 操作日誌記錄
    - 危險命令保護
    - 敏感信息隱藏
    """
    pass

@production_ops.command()
@click.option('--service', help='特定服務名稱')
@click.option('--env', 
              type=click.Choice(['all', 'prod', 'staging']), 
              default='prod',
              help='環境範圍')
@click.option('--detail', is_flag=True, help='顯示詳細信息')
def status(service: str, env: str, detail: bool):
    """查看生產環境狀態
    
    獲取系統整體健康狀況、服務狀態和關鍵指標。
    支援查看特定服務或全系統概覽。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"狀態查詢請求 - 服務:{service}, 環境:{env}, 詳細:{detail}")
    
    # 模擬系統狀態數據
    services_status = {
        'web-frontend': {'status': 'healthy', 'instances': '4/4', 'cpu': '45%', 'memory': '67%'},
        'api-backend': {'status': 'healthy', 'instances': '6/6', 'cpu': '52%', 'memory': '73%'},
        'database': {'status': 'healthy', 'instances': '2/2', 'cpu': '38%', 'memory': '81%'},
        'cache-redis': {'status': 'warning', 'instances': '2/3', 'cpu': '22%', 'memory': '45%'},
        'queue-worker': {'status': 'healthy', 'instances': '8/8', 'cpu': '35%', 'memory': '52%'},
        'monitoring': {'status': 'healthy', 'instances': '1/1', 'cpu': '15%', 'memory': '28%'}
    }
    
    result = f"📊 **生產環境狀態報告**\n"
    result += f"🕒 查詢時間：{timestamp}\n"
    result += f"🌍 環境範圍：{env.upper()}\n\n"
    
    if service:
        # 單一服務詳細狀態
        if service in services_status:
            svc = services_status[service]
            status_emoji = {"healthy": "✅", "warning": "⚠️", "error": "❌"}
            
            result += f"🔍 **服務詳情：{service}**\n"
            result += f"{status_emoji[svc['status']]} 狀態：{svc['status'].upper()}\n"
            result += f"💻 實例：{svc['instances']}\n"
            
            if detail:
                result += f"📈 CPU 使用率：{svc['cpu']}\n"
                result += f"💾 記憶體使用率：{svc['memory']}\n"
                result += f"🌐 網路狀態：正常\n"
                result += f"💽 磁碟使用率：65%\n"
                result += f"⚡ 回應時間：156ms\n"
                result += f"📈 QPS：1,247/秒\n"
        else:
            result += f"❌ 找不到服務：{service}"
    else:
        # 系統整體狀態
        healthy_count = sum(1 for s in services_status.values() if s['status'] == 'healthy')
        warning_count = sum(1 for s in services_status.values() if s['status'] == 'warning')
        error_count = sum(1 for s in services_status.values() if s['status'] == 'error')
        total_count = len(services_status)
        
        result += f"🌍 **系統總覽**\n"
        result += f"✅ 健康服務：{healthy_count}/{total_count}\n"
        result += f"⚠️ 警告服務：{warning_count}\n"
        result += f"❌ 異常服務：{error_count}\n\n"
        
        result += f"📋 **服務狀態列表**\n"
        for svc_name, svc_data in services_status.items():
            status_emoji = {"healthy": "✅", "warning": "⚠️", "error": "❌"}
            result += f"{status_emoji[svc_data['status']]} {svc_name}: {svc_data['instances']}\n"
        
        if detail:
            result += f"\n📊 **系統指標**\n"
            result += f"🔄 總請求數：2,847,392\n"
            result += f"⚡ 平均回應時間：178ms\n"
            result += f"📈 成功率：99.97%\n"
            result += f"💾 總記憶體使用：34.2GB / 64GB\n"
            result += f"💽 磁碟使用：1.2TB / 2TB\n"
    
    logger.info(f"狀態查詢完成 - 服務:{service}, 結果長度:{len(result)}")
    return result

@production_ops.command()
@click.option('--service', required=True, help='服務名稱')
@click.option('--replicas', type=int, required=True, help='目標實例數量')
@click.option('--confirm', is_flag=True, help='確認執行（必需）')
@click.option('--reason', help='操作原因')
def scale(service: str, replicas: int, confirm: bool, reason: str):
    """調整服務實例數量
    
    水平擴展或縮減服務實例，用於處理負載變化。
    需要明確確認以防止意外操作。
    """
    if not confirm:
        return (f"⚠️ **確認提示**\n"
                f"即將調整 {service} 實例數為 {replicas}\n"
                f"請使用 --confirm 參數確認執行此操作")
    
    if replicas < 1:
        return "❌ 實例數量不能少於 1"
    
    if replicas > 20:
        return "❌ 實例數量不能超過 20（安全限制）"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.warning(f"服務擴縮容操作 - 服務:{service}, 目標實例:{replicas}, 原因:{reason}")
    
    # 模擬當前實例數
    current_replicas = 4
    
    result = f"📈 **服務擴縮容操作**\n"
    result += f"🔧 服務名稱：{service}\n"
    result += f"📊 當前實例：{current_replicas}\n"
    result += f"🎯 目標實例：{replicas}\n"
    
    if reason:
        result += f"📝 操作原因：{reason}\n"
    
    result += f"🕒 操作時間：{timestamp}\n\n"
    
    if replicas > current_replicas:
        # 擴容
        diff = replicas - current_replicas
        result += f"📈 **擴容操作**\n"
        result += f"➕ 新增實例：{diff} 個\n"
        result += f"⏱️ 預計耗時：2-3 分鐘\n"
        result += f"📋 **操作步驟：**\n"
        result += f"1. 啟動新實例容器\n"
        result += f"2. 健康檢查\n"
        result += f"3. 加入負載平衡器\n"
        result += f"4. 驗證服務可用性\n"
        
    elif replicas < current_replicas:
        # 縮容
        diff = current_replicas - replicas
        result += f"📉 **縮容操作**\n"
        result += f"➖ 移除實例：{diff} 個\n"
        result += f"⏱️ 預計耗時：1-2 分鐘\n"
        result += f"📋 **操作步驟：**\n"
        result += f"1. 從負載平衡器移除實例\n"
        result += f"2. 等待連接排空\n"
        result += f"3. 優雅停止服務\n"
        result += f"4. 釋放資源\n"
    else:
        result += f"✅ 當前實例數已符合目標，無需調整"
        return result
    
    result += f"\n🔔 **通知設定：**\n"
    result += f"• 操作完成後將發送通知\n"
    result += f"• 如有異常將立即告警\n"
    result += f"• 操作日誌已記錄到審計系統"
    
    return result

@production_ops.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--version', required=True, help='版本標籤')
@click.option('--strategy',
              type=click.Choice(['rolling', 'blue-green', 'canary']),
              default='rolling',
              help='部署策略')
@click.option('--confirm', is_flag=True, help='確認部署（必需）')
@click.option('--rollback-on-error', is_flag=True, default=True, help='錯誤時自動回滾')
def deploy(app: str, version: str, strategy: str, confirm: bool, rollback_on_error: bool):
    """生產環境部署
    
    執行應用部署到生產環境，支援多種部署策略。
    包含完整的驗證和回滾機制。
    """
    if not confirm:
        return (f"⚠️ **生產部署確認**\n"
                f"應用：{app}\n"
                f"版本：{version}\n"
                f"策略：{strategy}\n"
                f"🚨 這是生產環境部署！\n"
                f"請使用 --confirm 參數確認執行")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.critical(f"生產部署請求 - 應用:{app}, 版本:{version}, 策略:{strategy}")
    
    result = f"🚀 **生產環境部署**\n"
    result += f"📱 應用：{app}\n"
    result += f"🏷️ 版本：{version}\n"
    result += f"📋 策略：{strategy}\n"
    result += f"🕒 開始時間：{timestamp}\n"
    result += f"🔄 自動回滾：{'啟用' if rollback_on_error else '停用'}\n\n"
    
    # 部署策略說明
    strategy_info = {
        'rolling': {
            'desc': '滾動更新 - 逐步替換實例',
            'time': '8-12 分鐘',
            'downtime': '零停機時間'
        },
        'blue-green': {
            'desc': '藍綠部署 - 環境切換',
            'time': '15-20 分鐘',
            'downtime': '< 30 秒'
        },
        'canary': {
            'desc': '金絲雀發布 - 灰度發布',
            'time': '30-45 分鐘',
            'downtime': '零停機時間'
        }
    }
    
    info = strategy_info[strategy]
    result += f"📊 **部署信息**\n"
    result += f"📝 策略說明：{info['desc']}\n"
    result += f"⏱️ 預計耗時：{info['time']}\n"
    result += f"⏸️ 停機時間：{info['downtime']}\n\n"
    
    # 部署檢查清單
    result += f"✅ **部署前檢查**\n"
    result += f"✅ 版本檔案完整性驗證\n"
    result += f"✅ 資料庫遷移腳本檢查\n"
    result += f"✅ 配置檔案語法驗證\n"
    result += f"✅ 依賴服務健康檢查\n"
    result += f"✅ 備份當前版本\n\n"
    
    # 部署步驟
    if strategy == 'rolling':
        steps = [
            "🔄 開始滾動更新",
            "📦 下載新版本鏡像",
            "🏥 健康檢查端點準備",
            "🔄 逐個更新實例 (25% 批次)",
            "🔍 驗證新實例功能",
            "🔄 繼續下一批次更新",
            "✅ 所有實例更新完成",
            "🧪 生產流量驗證"
        ]
    elif strategy == 'blue-green':
        steps = [
            "🟦 準備藍色環境",
            "📦 部署新版本到藍色環境",
            "🧪 藍色環境功能測試",
            "🔄 DNS 切換到藍色環境",
            "📊 監控新環境指標",
            "🟩 停用綠色環境",
            "✅ 部署完成"
        ]
    else:  # canary
        steps = [
            "🐣 準備金絲雀實例",
            "📦 部署新版本到金絲雀",
            "🔀 導入 5% 流量到金絲雀",
            "📊 監控關鍵指標",
            "🔀 逐步增加流量 (20%, 50%, 100%)",
            "📈 持續監控性能",
            "🔄 全量切換",
            "✅ 部署完成"
        ]
    
    result += f"📋 **{strategy.upper()} 部署步驟**\n"
    for i, step in enumerate(steps, 1):
        result += f"{i}. {step}\n"
    
    result += f"\n🚨 **緊急聯絡**\n"
    result += f"📞 值班工程師：+886-XXX-XXXX\n"
    result += f"💬 緊急群組：@prod-alerts\n"
    result += f"📧 郵件通知：ops@company.com\n"
    result += f"\n⚡ 部署任務已啟動！請密切關注系統指標。"
    
    return result

@production_ops.command()
@click.option('--to-version', help='回滾到特定版本（預設上一版本）')
@click.option('--confirm', is_flag=True, help='確認回滾（必需）')
@click.option('--reason', required=True, help='回滾原因')
def rollback(to_version: str, confirm: bool, reason: str):
    """緊急回滾
    
    快速回滾到上一個穩定版本，用於緊急故障恢復。
    """
    if not confirm:
        target = to_version or "上一版本"
        return (f"⚠️ **回滾確認**\n"
                f"目標版本：{target}\n"
                f"原因：{reason}\n"
                f"🚨 這是緊急回滾操作！\n"
                f"請使用 --confirm 參數確認執行")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_version = to_version or "v2.3.1"  # 模擬上一版本
    current_version = "v2.4.0"  # 模擬當前版本
    
    logger.critical(f"緊急回滾操作 - 從{current_version}回滾到{target_version}, 原因:{reason}")
    
    result = f"🔄 **緊急回滾操作**\n"
    result += f"📉 當前版本：{current_version}\n"
    result += f"🎯 目標版本：{target_version}\n"
    result += f"📝 回滾原因：{reason}\n"
    result += f"🕒 開始時間：{timestamp}\n\n"
    
    result += f"⚡ **快速回滾流程**\n"
    result += f"1. 🛑 停止當前版本部署\n"
    result += f"2. 📦 準備回滾版本鏡像\n"
    result += f"3. 🔄 快速切換服務版本\n"
    result += f"4. 🏥 健康檢查驗證\n"
    result += f"5. 📊 監控關鍵指標\n"
    result += f"6. ✅ 回滾完成確認\n\n"
    
    result += f"⏱️ **預計耗時：3-5 分鐘**\n"
    result += f"📈 **監控重點：**\n"
    result += f"• 錯誤率變化\n"
    result += f"• 回應時間\n"
    result += f"• 系統資源使用\n"
    result += f"• 使用者請求成功率\n\n"
    
    result += f"🚨 **後續動作：**\n"
    result += f"1. 分析故障原因\n"
    result += f"2. 修復程式問題\n"
    result += f"3. 重新測試驗證\n"
    result += f"4. 準備下次部署\n"
    result += f"\n⚡ 緊急回滾已啟動！團隊已收到通知。"
    
    return result

@production_ops.command()
@click.option('--app', required=True, help='應用名稱')
@click.option('--level',
              type=click.Choice(['error', 'warn', 'info', 'debug']),
              default='error',
              help='日誌級別')
@click.option('--lines', type=int, default=100, help='顯示行數')
@click.option('--grep', help='搜索關鍵字')
@click.option('--since', help='時間範圍（如：1h, 30m, 2d）')
@click.option('--json-format', is_flag=True, help='JSON格式輸出')
def logs(app: str, level: str, lines: int, grep: str, since: str, json_format: bool):
    """生產環境日誌查看
    
    安全地查看生產環境日誌，支援過濾和搜索。
    自動過濾敏感信息。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"日誌查詢 - 應用:{app}, 級別:{level}, 行數:{lines}, 搜索:{grep}")
    
    # 模擬日誌數據（已過濾敏感信息）
    log_entries = [
        {"timestamp": "2025-01-01T10:30:15Z", "level": "INFO", "message": "Application started successfully", "module": "app.main"},
        {"timestamp": "2025-01-01T10:30:16Z", "level": "WARN", "message": "Database connection pool reaching limit", "module": "db.pool"},
        {"timestamp": "2025-01-01T10:30:17Z", "level": "ERROR", "message": "Failed to process request: timeout after 30s", "module": "api.handler"},
        {"timestamp": "2025-01-01T10:30:18Z", "level": "INFO", "message": "Request completed in 245ms", "module": "api.middleware"},
        {"timestamp": "2025-01-01T10:30:19Z", "level": "DEBUG", "message": "Cache hit rate: 89%", "module": "cache.redis"},
        {"timestamp": "2025-01-01T10:30:20Z", "level": "ERROR", "message": "Authentication failed for user [REDACTED]", "module": "auth.service"},
        {"timestamp": "2025-01-01T10:30:21Z", "level": "WARN", "message": "Rate limit exceeded from IP [REDACTED]", "module": "rate.limiter"}
    ]
    
    # 級別過濾
    level_priority = {"debug": 0, "info": 1, "warn": 2, "error": 3}
    min_level = level_priority[level]
    filtered_logs = [log for log in log_entries if level_priority[log["level"].lower()] >= min_level]
    
    # 關鍵字搜索
    if grep:
        filtered_logs = [log for log in filtered_logs if grep.lower() in log["message"].lower()]
    
    # 限制行數
    display_logs = filtered_logs[-lines:]
    
    if json_format:
        # JSON格式輸出
        result = f"📋 **{app}** JSON日誌 ({timestamp})\n"
        result += f"```json\n"
        for log in display_logs:
            result += json.dumps(log, ensure_ascii=False) + "\n"
        result += "```"
    else:
        # 人類可讀格式
        result = f"📋 **{app}** 應用日誌 ({timestamp})\n"
        result += f"🔍 級別：{level.upper()} | 行數：{len(display_logs)}"
        
        if grep:
            result += f" | 搜索：{grep}"
        if since:
            result += f" | 時間：最近{since}"
        
        result += "\n\n```\n"
        for log in display_logs:
            level_emoji = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "DEBUG": "🔧"}
            emoji = level_emoji.get(log["level"], "📝")
            result += f"{log['timestamp']} {emoji} [{log['level']}] {log['module']}: {log['message']}\n"
        result += "```"
    
    result += f"\n🔒 **隱私保護：**敏感信息已自動過濾\n"
    result += f"📊 **統計：**共 {len(display_logs)} 條日誌符合條件"
    
    return result

@production_ops.command()
@click.option('--metric',
              type=click.Choice(['cpu', 'memory', 'disk', 'network', 'requests', 'errors', 'all']),
              default='all',
              help='指標類型')
@click.option('--duration',
              type=click.Choice(['5m', '15m', '1h', '6h', '24h']),
              default='1h',
              help='時間範圍')
@click.option('--threshold', type=float, help='告警閾值')
def metrics(metric: str, duration: str, threshold: float):
    """關鍵性能指標
    
    查看生產環境的關鍵性能指標和趨勢分析。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 模擬指標數據
    import random
    metrics_data = {
        'cpu': {'current': random.randint(30, 80), 'avg': random.randint(25, 75), 'peak': random.randint(40, 95)},
        'memory': {'current': random.randint(40, 85), 'avg': random.randint(35, 80), 'peak': random.randint(50, 95)},
        'disk': {'current': random.randint(20, 60), 'avg': random.randint(18, 55), 'peak': random.randint(25, 70)},
        'network': {'current': random.randint(15, 70), 'avg': random.randint(12, 65), 'peak': random.randint(20, 85)},
        'requests': {'current': 1247, 'avg': 1156, 'peak': 2891},
        'errors': {'current': 0.03, 'avg': 0.07, 'peak': 0.15}
    }
    
    result = f"📊 **關鍵性能指標** ({timestamp})\n"
    result += f"⏱️ 時間範圍：最近 {duration}\n"
    
    if threshold:
        result += f"🚨 告警閾值：{threshold}%\n"
    
    result += "\n"
    
    def format_metric(name, data, unit="%"):
        current = data['current']
        avg = data['avg']
        peak = data['peak']
        
        # 狀態判斷
        if current > 80:
            status = "🔴"
        elif current > 60:
            status = "🟡"
        else:
            status = "🟢"
        
        # 閾值告警
        alert = ""
        if threshold and current > threshold:
            alert = f" 🚨 超過閾值({threshold}{unit})"
        
        return f"{status} **{name.upper()}**{alert}\n   當前：{current}{unit} | 平均：{avg}{unit} | 峰值：{peak}{unit}\n"
    
    if metric == 'all':
        result += format_metric('CPU', metrics_data['cpu'])
        result += format_metric('Memory', metrics_data['memory'])
        result += format_metric('Disk', metrics_data['disk'])
        result += format_metric('Network', metrics_data['network'])
        result += format_metric('Requests', metrics_data['requests'], "/s")
        result += format_metric('Error Rate', metrics_data['errors'])
    else:
        if metric in metrics_data:
            unit = "/s" if metric == 'requests' else "%" if metric != 'errors' else "%"
            result += format_metric(metric, metrics_data[metric], unit)
    
    # 趨勢分析
    result += f"\n📈 **趨勢分析 ({duration})**\n"
    result += f"📊 整體負載：中等偏高\n"
    result += f"🔄 請求增長：+12% vs 上週\n"
    result += f"❌ 錯誤率：-0.02% vs 昨日\n"
    result += f"⚡ 回應時間：156ms (+5ms vs 上週)\n"
    
    # 建議
    result += f"\n💡 **優化建議**\n"
    if any(metrics_data[m]['current'] > 70 for m in ['cpu', 'memory']):
        result += f"• 考慮水平擴展實例\n"
    if metrics_data['errors']['current'] > 0.1:
        result += f"• 檢查錯誤日誌並修復問題\n"
    result += f"• 繼續監控系統穩定性\n"
    
    return result

@production_ops.command()
@click.option('--action',
              type=click.Choice(['enable', 'disable', 'status']),
              required=True,
              help='維護模式操作')
@click.option('--message', help='維護公告訊息')
@click.option('--duration', help='預計維護時長')
def maintenance(action: str, message: str, duration: str):
    """維護模式管理
    
    啟用或停用系統維護模式，控制用戶訪問。
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.warning(f"維護模式操作 - 動作:{action}, 訊息:{message}, 時長:{duration}")
    
    if action == 'status':
        # 查看維護狀態
        result = f"🔧 **維護模式狀態** ({timestamp})\n"
        result += f"📊 當前狀態：正常運行\n"
        result += f"🕒 上次維護：2024-12-25 02:00-04:30\n"
        result += f"📅 下次計劃維護：2025-01-15 03:00\n"
        result += f"⏱️ 計劃時長：2小時\n"
        return result
    
    elif action == 'enable':
        # 啟用維護模式
        if not message:
            message = "系統維護中，請稍後再試"
        
        result = f"🔧 **啟用維護模式**\n"
        result += f"🕒 開始時間：{timestamp}\n"
        result += f"📝 公告訊息：{message}\n"
        
        if duration:
            result += f"⏱️ 預計時長：{duration}\n"
        
        result += f"\n📋 **維護模式效果：**\n"
        result += f"• 🚫 阻擋新用戶請求\n"
        result += f"• ⏳ 現有連接優雅關閉\n"
        result += f"• 📢 顯示維護公告頁面\n"
        result += f"• 🔄 健康檢查返回維護狀態\n"
        result += f"• 📊 監控系統繼續運行\n"
        
        result += f"\n✅ 維護模式已啟用！"
        
    else:  # disable
        # 停用維護模式
        result = f"🔧 **停用維護模式**\n"
        result += f"🕒 恢復時間：{timestamp}\n"
        
        result += f"\n📋 **恢復操作：**\n"
        result += f"• ✅ 恢復用戶請求處理\n"
        result += f"• 🔄 重新啟用負載平衡\n"
        result += f"• 📊 恢復正常健康檢查\n"
        result += f"• 📈 開始接收流量\n"
        
        result += f"\n🎉 系統已恢復正常運行！"
    
    return result

def main():
    """主程序入口"""
    # 環境驗證
    if not os.getenv("TELEGRAM_TOKEN"):
        logger.error("TELEGRAM_TOKEN 環境變數未設置")
        print("❌ 請設置 TELEGRAM_TOKEN 環境變數")
        print("📝 範例：export TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh")
        sys.exit(1)
    
    if not admin_users:
        logger.warning("未設置管理員用戶，所有用戶都可以使用")
        print("⚠️ 警告：未設置管理員用戶（ADMIN_USERS）")
        print("🔒 生產環境建議設置管理員限制")
    
    # 啟動信息
    print("🏭 生產級 TelegramClick Bot")
    print("=" * 60)
    print(f"📊 日誌級別：{LOG_LEVEL}")
    print(f"👥 管理員用戶：{admin_users if admin_users else '無限制'}")
    print(f"🛡️ 安全特性：已啟用")
    print(f"📝 已註冊命令：{len(production_ops.commands)} 個")
    
    # 智能運行模式
    if len(sys.argv) > 1:
        # CLI模式
        logger.info("CLI模式啟動")
        print("📟 CLI模式啟動")
        production_ops()
    else:
        # Telegram Bot模式
        logger.info("Telegram Bot模式啟動")
        print("🤖 Telegram Bot模式啟動")
        print("💬 在Telegram中發送 /start 開始使用")
        print("🔔 所有操作都會被記錄到日誌文件")
        production_ops.run_telegram_bot()

if __name__ == "__main__":
    main()
