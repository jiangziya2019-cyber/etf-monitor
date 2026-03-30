#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送周日复盘提醒到飞书
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

def generate_reminder():
    lines = []
    lines.append("📊 周日复盘提醒")
    lines.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("━━━ 复盘流程 ━━━")
    lines.append("")
    lines.append("1️⃣ 请老板发送最新持仓截图")
    lines.append("   • 支持多张图片")
    lines.append("   • 我会 OCR 识别并整理表格")
    lines.append("   • 供您确认后更新数据源")
    lines.append("")
    lines.append("2️⃣ 更新持仓记录和收益曲线")
    lines.append("   • 更新 holdings_current.json")
    lines.append("   • 保存收益曲线数据")
    lines.append("   • 自动备份旧数据")
    lines.append("")
    lines.append("3️⃣ 生成周度复盘报告")
    lines.append("   • 市值曲线")
    lines.append("   • 收益曲线")
    lines.append("   • 持仓变化")
    lines.append("   • 盈亏分析")
    lines.append("   • 行业分布")
    lines.append("   • 下周展望")
    lines.append("")
    lines.append("━━━ 当前持仓数据 ━━━")
    lines.append("数据截至：2026-03-27 22:30")
    lines.append("总市值：¥162,813.20")
    lines.append("总浮盈：+¥607.40")
    lines.append("收益率：+0.37%")
    lines.append("ETF 数量：20 只")
    lines.append("")
    lines.append("⚠️ 提示：请发送最新持仓截图以更新数据")
    
    return "\n".join(lines)

if __name__ == "__main__":
    reminder = generate_reminder()
    print(reminder)
    
    print("\n发送飞书提醒...")
    success = send_text_message(reminder)
    
    if success:
        print("\n✅ 复盘提醒已发送至飞书")
    else:
        print("\n❌ 发送失败")
