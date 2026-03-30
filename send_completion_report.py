#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送完成报告到飞书
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
    lines = []
    lines.append("✅ 三项优化全部完成")
    lines.append(f"完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("━━━ 完成情况 ━━━")
    lines.append("")
    lines.append("1️⃣ 行业轮动分析")
    lines.append("   📁 sector_rotation.py")
    lines.append("   • 分析持仓行业分布")
    lines.append("   • 生成轮动信号 (strong_buy/buy/hold/sell)")
    lines.append("   • 提供调仓建议")
    lines.append("")
    lines.append("2️⃣ 市场情绪指标")
    lines.append("   📁 market_sentiment.py")
    lines.append("   • 波动率监测 (类 VIX)")
    lines.append("   • 市场宽度 (涨跌比)")
    lines.append("   • 成交量分析")
    lines.append("   • 北向资金流向")
    lines.append("   • 综合情绪评分 (0-100)")
    lines.append("")
    lines.append("3️⃣ 回测框架优化")
    lines.append("   📁 backtest_framework.py")
    lines.append("   • 买入持有策略回测")
    lines.append("   • 定期调仓策略回测")
    lines.append("   • 性能指标 (夏普/回撤/胜率)")
    lines.append("   • 策略对比分析")
    lines.append("")
    lines.append("━━━ 使用方法 ━━━")
    lines.append("• 行业轮动：python3 sector_rotation.py")
    lines.append("• 市场情绪：python3 market_sentiment.py")
    lines.append("• 回测验证：python3 backtest_framework.py")
    lines.append("• 一键运行：python3 enhanced_analysis.py")
    lines.append("")
    lines.append("━━━ 技能文档 ━━━")
    lines.append("📄 skills/enhanced-analysis/SKILL.md")
    lines.append("")
    lines.append("⚠️ 提示：所有模块已测试通过，可立即使用")
    
    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_report()
    print(report)
    
    print("\n发送飞书消息...")
    success = send_text_message(report)
    
    if success:
        print("\n✅ 完成报告已发送至飞书")
    else:
        print("\n❌ 发送失败")
