#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10:30 操作建议报告 - 周末版
基于持仓数据提供调仓建议参考
"""

import json
import requests
from datetime import datetime

# 飞书配置
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
BOSS_OPEN_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"
API_BASE = "https://open.feishu.cn/open-apis"

def get_tenant_access_token():
    """获取 tenant_access_token"""
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("tenant_access_token")
    return None

def send_text_message(text):
    """发送文本消息"""
    token = get_tenant_access_token()
    if not token:
        return False
    
    url = f"{API_BASE}/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "receive_id": BOSS_OPEN_ID,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    result = response.json()
    
    return result.get("code") == 0

def generate_report():
    """生成操作建议报告"""
    
    with open("/home/admin/openclaw/workspace/holdings_current.json", "r") as f:
        holdings = json.load(f)
    
    etfs = holdings["etfs"]
    
    # 分类建议
    # 1. 盈利品种（考虑止盈）
    profitable = [e for e in etfs if e["yield"] > 5]
    
    # 2. 亏损品种（关注止损）
    loss_makers = [e for e in etfs if e["yield"] < -5]
    
    # 3. 重仓品种（>8% 仓位）
    total_value = holdings["total_market_value"]
    heavy_positions = [e for e in etfs if (e["market_value"] / total_value) > 0.08]
    
    # 4. 轻仓品种（<3% 仓位）
    light_positions = [e for e in etfs if (e["market_value"] / total_value) < 0.03]
    
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_status": "周日休市",
        "summary": {
            "total_value": total_value,
            "total_profit": holdings["total_profit"],
            "yield_rate": holdings["yield_rate"]
        },
        "profitable_etfs": profitable,
        "loss_makers": loss_makers,
        "heavy_positions": heavy_positions,
        "light_positions": light_positions,
        "notes": [
            "今日 A 股休市，无法执行交易",
            "建议利用周末时间研究持仓结构",
            "周一开盘前确认调仓计划",
            "嘉实原油盈利 +611%，可考虑部分止盈",
            "黄金 9999 亏损 -13.34%，关注是否止损"
        ]
    }
    
    return report

def format_report(report):
    """格式化报告"""
    lines = []
    lines.append("📈 10:30 操作建议")
    lines.append(f"生成时间：{report['timestamp']}")
    lines.append("")
    lines.append(f"市场状态：{report['market_status']}")
    lines.append("")
    lines.append("━━━ 持仓概览 ━━━")
    s = report["summary"]
    lines.append(f"总市值：¥{s['total_value']:,.2f}")
    lines.append(f"总浮盈：¥{s['total_profit']:+,.2f}")
    lines.append(f"收益率：{s['yield_rate']:+.2f}%")
    lines.append("")
    
    if report["profitable_etfs"]:
        lines.append("━━━ 盈利品种 (>5%) ━━━")
        for etf in report["profitable_etfs"]:
            pct = (etf["market_value"] / s["total_value"]) * 100
            lines.append(f"• {etf['name']}: {etf['yield']:+.2f}% (仓位{pct:.1f}%)")
        lines.append("")
    
    if report["loss_makers"]:
        lines.append("━━━ 亏损品种 (<-5%) ━━━")
        for etf in report["loss_makers"]:
            pct = (etf["market_value"] / s["total_value"]) * 100
            lines.append(f"• {etf['name']}: {etf['yield']:+.2f}% (仓位{pct:.1f}%)")
        lines.append("")
    
    if report["heavy_positions"]:
        lines.append("━━━ 重仓品种 (>8%) ━━━")
        for etf in report["heavy_positions"]:
            pct = (etf["market_value"] / s["total_value"]) * 100
            lines.append(f"• {etf['name']}: {pct:.1f}% 仓位")
        lines.append("")
    
    lines.append("━━━ 操作建议 ━━━")
    for note in report["notes"]:
        lines.append(f"• {note}")
    lines.append("")
    lines.append("⚠️ 提醒：分析仅供参考，投资决策请自行判断")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("生成 10:30 操作建议报告...")
    report = generate_report()
    formatted = format_report(report)
    
    print("\n发送飞书消息...")
    success = send_text_message(formatted)
    
    if success:
        print("\n✅ 10:30 操作建议已发送至飞书")
    else:
        print("\n❌ 发送失败")
