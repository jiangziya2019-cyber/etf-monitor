#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送盘前准备报告到飞书
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
    else:
        print(f"获取 token 失败：{data}")
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
    
    if result.get("code") == 0:
        print(f"消息发送成功：{result.get('data', {}).get('message_id')}")
        return True
    else:
        print(f"消息发送失败：{result}")
        return False

def generate_report():
    """生成盘前报告"""
    
    # 读取持仓数据
    with open("/home/admin/openclaw/workspace/holdings_current.json", "r") as f:
        holdings = json.load(f)
    
    # 按收益率排序
    etfs_sorted = sorted(holdings["etfs"], key=lambda x: x["yield"], reverse=True)
    
    # 分类统计
    positive = [e for e in holdings["etfs"] if e["yield"] > 0]
    negative = [e for e in holdings["etfs"] if e["yield"] <= 0]
    
    # 行业分类
    sectors = {
        "科技": ["创业板 AI", "创业智能", "AI 智能", "半导体", "卫星 ETF", "机床 ETF", "储能电池"],
        "医药": ["医药 ETF"],
        "周期": ["光伏 ETF", "航空 ETF", "航空航天"],
        "商品": ["嘉实原油", "黄金 9999"],
        "宽基": ["创业 50", "纳指 100", "标普 500", "300ETF", "500ETF"],
        "策略": ["现金流", "红利 ETF"]
    }
    
    sector_performance = {}
    for sector, names in sectors.items():
        sector_etfs = [e for e in holdings["etfs"] if e["name"] in names]
        if sector_etfs:
            avg_yield = sum(e["yield"] for e in sector_etfs) / len(sector_etfs)
            sector_performance[sector] = {
                "avg_yield": avg_yield,
                "count": len(sector_etfs),
                "total_value": sum(e["market_value"] for e in sector_etfs)
            }
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_status": "周日休市",
        "holdings_summary": {
            "total_value": holdings["total_market_value"],
            "total_profit": holdings["total_profit"],
            "yield_rate": holdings["yield_rate"],
            "etf_count": holdings["etf_count"],
            "positive_count": len(positive),
            "negative_count": len(negative)
        },
        "top_performers": etfs_sorted[:5],
        "bottom_performers": etfs_sorted[-5:],
        "sector_performance": sector_performance
    }

def format_report(report):
    """格式化报告"""
    lines = []
    lines.append("📊 盘前准备报告")
    lines.append(f"生成时间：{report['timestamp']}")
    lines.append("")
    lines.append(f"市场状态：{report['market_status']}")
    lines.append("")
    lines.append("━━━ 持仓概览 ━━━")
    s = report["holdings_summary"]
    lines.append(f"总市值：¥{s['total_value']:,.2f}")
    lines.append(f"总浮盈：¥{s['total_profit']:+,.2f}")
    lines.append(f"收益率：{s['yield_rate']:+.2f}%")
    lines.append(f"持仓 ETF：{s['etf_count']}只 ({s['positive_count']}红/{s['negative_count']}绿)")
    lines.append("")
    
    lines.append("━━━ 表现最佳 TOP5 ━━━")
    for i, etf in enumerate(report["top_performers"], 1):
        lines.append(f"{i}. {etf['name']}: {etf['yield']:+.2f}%")
    lines.append("")
    
    lines.append("━━━ 表现最差 TOP5 ━━━")
    for i, etf in enumerate(report["bottom_performers"], 1):
        lines.append(f"{i}. {etf['name']}: {etf['yield']:+.2f}%")
    lines.append("")
    
    lines.append("━━━ 行业板块 ━━━")
    sectors_sorted = sorted(report["sector_performance"].items(), 
                           key=lambda x: x[1]["avg_yield"], reverse=True)
    for sector, data in sectors_sorted:
        lines.append(f"• {sector}: {data['avg_yield']:+.2f}% ({data['count']}只)")
    lines.append("")
    
    lines.append("━━━ 今日关注 ━━━")
    lines.append("• A 股休市，无交易")
    lines.append("• 关注今晚美股开盘")
    lines.append("• 关注原油、黄金价格")
    lines.append("• 周一 9:15 集合竞价")
    lines.append("")
    lines.append("注：数据截至 2026-03-27 收盘")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("生成盘前报告...")
    report = generate_report()
    formatted = format_report(report)
    
    print("\n发送飞书消息...")
    success = send_text_message(formatted)
    
    if success:
        print("\n✅ 盘前报告已发送至飞书")
    else:
        print("\n❌ 发送失败")
