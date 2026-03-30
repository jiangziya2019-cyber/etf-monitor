#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易盘前报告 - 基于持仓数据生成
"""

import json
from datetime import datetime

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
    
    # 行业分类（简化）
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
    
    report = {
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
        "sector_performance": sector_performance,
        "notes": [
            "今日 A 股休市，无交易",
            "关注今晚美股开盘表现（纳指 100、标普 500）",
            "关注原油、黄金价格波动",
            "周一 9:15 开始集合竞价"
        ]
    }
    
    return report

def format_report(report):
    """格式化报告为飞书消息"""
    
    lines = []
    lines.append("📊 **盘前准备报告**")
    lines.append(f"_生成时间：{report['timestamp']}_")
    lines.append("")
    lines.append(f"**市场状态**: {report['market_status']}")
    lines.append("")
    lines.append("━━━ 持仓概览 ━━━")
    s = report["holdings_summary"]
    lines.append(f"总市值：¥{s['total_value']:,.2f}")
    lines.append(f"总浮盈：¥{s['total_profit']:+,.2f}")
    lines.append(f"收益率：{s['yield_rate']:+.2f}%")
    lines.append(f"持仓 ETF：{s['etf_count']} 只 ({s['positive_count']} 红 / {s['negative_count']} 绿)")
    lines.append("")
    
    lines.append("━━━ 表现最佳 TOP5 ━━━")
    for i, etf in enumerate(report["top_performers"], 1):
        lines.append(f"{i}. {etf['name']}: {etf['yield']:+.2f}%")
    lines.append("")
    
    lines.append("━━━ 表现最差 TOP5 ━━━")
    for i, etf in enumerate(report["bottom_performers"], 1):
        lines.append(f"{i}. {etf['name']}: {etf['yield']:+.2f}%")
    lines.append("")
    
    lines.append("━━━ 行业板块表现 ━━━")
    sectors_sorted = sorted(report["sector_performance"].items(), 
                           key=lambda x: x[1]["avg_yield"], reverse=True)
    for sector, data in sectors_sorted:
        lines.append(f"• {sector}: {data['avg_yield']:+.2f}% ({data['count']}只，¥{data['total_value']:,.0f})")
    lines.append("")
    
    lines.append("━━━ 今日关注 ━━━")
    for note in report["notes"]:
        lines.append(f"• {note}")
    lines.append("")
    lines.append("_注：数据截至 2026-03-27 收盘，周日休市_")
    
    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_report()
    formatted = format_report(report)
    print(formatted)
    
    # 保存为 JSON
    with open("/home/admin/openclaw/workspace/panqian_report_20260329.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n报告已保存至 panqian_report_20260329.json")
