#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓监控与报告生成工具
- 每日持仓快照保存
- 周一复盘报告
- 月度复盘报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# 目录配置
WORKSPACE = Path('/home/admin/openclaw/workspace')
HISTORY_DIR = WORKSPACE / 'portfolio_history' / 'daily'
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

def parse_holdings_table(text):
    """
    解析持仓表格文本为结构化数据
    支持格式：标的名称	持仓/可用	现价	成本	持仓盈亏	持仓盈亏 (%)	市值
    """
    holdings = []
    lines = text.strip().split('\n')
    
    for line in lines[1:]:  # 跳过表头
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            name = parts[0].strip()
            position_str = parts[1].strip()
            position = int(position_str.split('/')[0]) if '/' in position_str else int(position_str)
            price = float(parts[2].strip())
            cost = float(parts[3].strip())
            pnl = float(parts[4].strip().replace(',', ''))
            pnl_pct = float(parts[5].strip().replace('%', ''))
            market_value = float(parts[6].strip().replace(',', ''))
            
            holdings.append({
                'name': name,
                'position': position,
                'price': price,
                'cost': cost,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'market_value': market_value
            })
    
    return holdings

def save_daily_snapshot(holdings, date=None):
    """保存每日持仓快照"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    total_value = sum(h['market_value'] for h in holdings)
    total_pnl = sum(h['pnl'] for h in holdings)
    
    # 生成 Markdown 报告
    md_content = f"""# 持仓快照 - {date}

**录入时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**数据来源**: 老板飞书发送  
**市场状态**: 收盘后

---

## 📊 持仓明细

| # | 品种 | 持仓 | 成本 | 现价 | 盈亏 | 盈亏% | 市值 |
|---|------|------|------|------|------|-------|------|
"""
    
    for i, h in enumerate(holdings, 1):
        md_content += f"| {i} | {h['name']} | {h['position']} | {h['cost']:.3f} | {h['price']:.3f} | {h['pnl']:+.2f} | {h['pnl_pct']:+.1f}% | {h['market_value']:,.0f} |\n"
    
    md_content += f"""
---

## 📈 汇总数据

| 指标 | 数值 |
|------|------|
| **持仓数量** | {len(holdings)} 只 |
| **总市值** | {total_value:,.0f} 元 |
| **总盈亏** | {total_pnl:+,.0f} 元 |
| **平均盈亏** | {(total_pnl/total_value*100):+.2f}% |

---

## 🎯 仓位分布

| 仓位区间 | 数量 | 品种 |
|---------|------|------|
"""
    
    # 计算仓位分布
    heavy = [h for h in holdings if h['market_value'] / total_value > 0.08]
    medium = [h for h in holdings if 0.05 <= h['market_value'] / total_value <= 0.08]
    light = [h for h in holdings if h['market_value'] / total_value < 0.05]
    
    md_content += f"| **重仓 (>8%)** | {len(heavy)} 只 | {', '.join(h['name'] for h in heavy)} |\n"
    md_content += f"| **中等 (5-8%)** | {len(medium)} 只 | {', '.join(h['name'] for h in medium)} |\n"
    md_content += f"| **轻仓 (<5%)** | {len(light)} 只 | 其他 |\n"
    
    md_content += """
---

## 🟢 盈利品种

| 品种 | 盈亏% | 市值 |
|------|-------|------|
"""
    
    gainers = sorted([h for h in holdings if h['pnl_pct'] > 0], key=lambda x: x['pnl_pct'], reverse=True)
    for h in gainers[:5]:
        md_content += f"| {h['name']} | {h['pnl_pct']:+.1f}% | {h['market_value']:,.0f} 元 |\n"
    
    md_content += """
---

## 🔴 高风险品种 (浮亏>10%)

| 品种 | 盈亏% | 市值 |
|------|-------|------|
"""
    
    losers = sorted([h for h in holdings if h['pnl_pct'] < -10], key=lambda x: x['pnl_pct'])
    for h in losers[:5]:
        md_content += f"| {h['name']} | {h['pnl_pct']:+.1f}% | {h['market_value']:,.0f} 元 |\n"
    
    # 保存文件
    file_path = HISTORY_DIR / f"{date}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ 持仓快照已保存：{file_path}")
    return file_path

def compare_holdings(old_file, new_file):
    """对比两个持仓快照"""
    print(f"\n📊 持仓对比分析")
    print(f"对比：{old_file} vs {new_file}")
    print("=" * 60)
    # TODO: 实现对比逻辑
    pass

def generate_weekly_report():
    """生成周度复盘报告"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    
    print(f"\n📈 生成周度复盘报告 ({monday.strftime('%Y-%m-%d')})")
    # TODO: 实现周度报告逻辑
    pass

def generate_monthly_report():
    """生成月度复盘报告"""
    today = datetime.now()
    first_day = today.replace(day=1)
    
    print(f"\n📊 生成月度复盘报告 ({first_day.strftime('%Y-%m-%d')})")
    # TODO: 实现月度报告逻辑
    pass

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "daily":
            # 从 stdin 读取持仓数据
            text = sys.stdin.read()
            holdings = parse_holdings_table(text)
            save_daily_snapshot(holdings)
        elif command == "weekly":
            generate_weekly_report()
        elif command == "monthly":
            generate_monthly_report()
    else:
        print("用法：python portfolio_monitor.py [daily|weekly|monthly]")
        print("  daily   - 保存每日持仓快照 (从 stdin 读取)")
        print("  weekly  - 生成周度复盘报告")
        print("  monthly - 生成月度复盘报告")
