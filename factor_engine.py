#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版因子引擎 - 基于量化文章思路
对持仓 ETF 进行多维度因子评分
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/home/admin/openclaw/workspace')

HOLDINGS = [
    {'name': '半导体', 'code': '512480', 'price': 1.460, 'cost': 1.572, 'pnl_pct': -7.125, 'market_value': 4818},
    {'name': '卫星 ETF', 'code': '159206', 'price': 1.587, 'cost': 1.562, 'pnl_pct': 1.601, 'market_value': 6824},
    {'name': '机床', 'code': '159663', 'price': 1.723, 'cost': 1.595, 'pnl_pct': 8.025, 'market_value': 5514},
    {'name': '纳指 100', 'code': '513110', 'price': 1.922, 'cost': 1.999, 'pnl_pct': -3.852, 'market_value': 8649},
    {'name': '储能电池', 'code': '159566', 'price': 2.233, 'cost': 2.149, 'pnl_pct': 3.909, 'market_value': 13845},
    {'name': '标普 500', 'code': '513500', 'price': 2.201, 'cost': 2.283, 'pnl_pct': -3.592, 'market_value': 10125},
    {'name': '红利 ETF', 'code': '515080', 'price': 3.252, 'cost': 3.275, 'pnl_pct': -0.702, 'market_value': 6829},
    {'name': '300ETF', 'code': '510300', 'price': 4.496, 'cost': 4.592, 'pnl_pct': -2.091, 'market_value': 13488},
    {'name': '500ETF', 'code': '510500', 'price': 7.751, 'cost': 7.905, 'pnl_pct': -1.948, 'market_value': 6976},
    {'name': '黄金 9999', 'code': '159937', 'price': 9.414, 'cost': 10.671, 'pnl_pct': -11.780, 'market_value': 16004},
    {'name': '医药 ETF', 'code': '512010', 'price': 0.361, 'cost': 0.368, 'pnl_pct': -1.902, 'market_value': 2780},
    {'name': '机器人 AI', 'code': '159770', 'price': 0.958, 'cost': 4.098, 'pnl_pct': -76.623, 'market_value': 479},
    {'name': '创业板 AI', 'code': '159363', 'price': 1.066, 'cost': 1.078, 'pnl_pct': -1.113, 'market_value': 10660},
    {'name': '创业智能', 'code': '159243', 'price': 1.077, 'cost': 1.126, 'pnl_pct': -4.352, 'market_value': 6462},
    {'name': '光伏 ETF', 'code': '515790', 'price': 1.100, 'cost': 1.139, 'pnl_pct': -3.424, 'market_value': 4180},
    {'name': '现金流', 'code': '159399', 'price': 1.117, 'cost': 1.118, 'pnl_pct': -0.089, 'market_value': 20553},
    {'name': '军工 ETF', 'code': '512660', 'price': 1.289, 'cost': 2.368, 'pnl_pct': -45.566, 'market_value': 387},
    {'name': '航空 TH', 'code': '159241', 'price': 1.280, 'cost': 1.336, 'pnl_pct': -4.192, 'market_value': 2176},
    {'name': '嘉实原油', 'code': '160723', 'price': 2.876, 'cost': 1.084, 'pnl_pct': 165.314, 'market_value': 6615},
    {'name': '航空航天', 'code': '159227', 'price': 1.254, 'cost': 1.260, 'pnl_pct': -0.476, 'market_value': 5016},
    {'name': 'AI 智能', 'code': '159819', 'price': 1.476, 'cost': 1.512, 'pnl_pct': -2.381, 'market_value': 8413},
    {'name': '创业板 50', 'code': '159949', 'price': 1.551, 'cost': 1.551, 'pnl_pct': 0.000, 'market_value': 1551},
]

def calculate_factors(etf):
    """计算单个 ETF 的所有因子得分"""
    pnl_pct = etf['pnl_pct']
    price = etf['price']
    cost = etf['cost']
    ratio = price / cost
    
    # 动量因子 (40% 权重)
    momentum = max(0, min(100, 50 + pnl_pct * 2.5))
    
    # 估值因子 (30% 权重)
    value = max(0, min(100, 50 + (ratio - 1) * 100))
    
    # 趋势因子 (20% 权重)
    if pnl_pct > 5: trend = 90
    elif pnl_pct > 0: trend = 70
    elif pnl_pct > -5: trend = 40
    elif pnl_pct > -10: trend = 25
    else: trend = 10
    
    # 波动因子 (10% 权重)
    abs_pnl = abs(pnl_pct)
    if abs_pnl < 2: volatility = 95
    elif abs_pnl < 5: volatility = 80
    elif abs_pnl < 10: volatility = 60
    elif abs_pnl < 20: volatility = 40
    else: volatility = 20
    
    # 综合得分
    composite = momentum * 0.40 + value * 0.30 + trend * 0.20 + volatility * 0.10
    
    return {
        'momentum': round(momentum, 1),
        'value': round(value, 1),
        'trend': round(trend, 1),
        'volatility': round(volatility, 1),
        'composite': round(composite, 1)
    }

def generate_report():
    """生成因子分析报告"""
    print("=" * 90)
    print("📊 ETF 持仓因子分析报告")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # 计算所有因子
    results = []
    for etf in HOLDINGS:
        factors = calculate_factors(etf)
        results.append({**etf, **factors})
    
    # 排序
    results.sort(key=lambda x: x['composite'], reverse=True)
    
    # 表格输出
    print("\n📈 持仓 ETF 因子评分")
    print("-" * 90)
    print(f"{'排名':<4} | {'品种':<10} | {'综合':<6} | {'动量':<6} | {'估值':<6} | {'趋势':<6} | {'波动':<6} | {'盈亏%':<8} | {'市值':<8}")
    print("-" * 90)
    
    for i, r in enumerate(results, 1):
        print(f"{i:<4} | {r['name']:<10} | {r['composite']:<6.1f} | {r['momentum']:<6.1f} | {r['value']:<6.1f} | {r['trend']:<6.1f} | {r['volatility']:<6.1f} | {r['pnl_pct']:<+8.1f}% | {r['market_value']/1000:<7.1f}k")
    
    # 分类建议
    print("\n🎯 调仓建议")
    print("=" * 90)
    
    excellent = [r for r in results if r['composite'] >= 70]
    print(f"\n✅ 优秀品种 ({len(excellent)}只，建议持有/加仓):")
    for r in excellent:
        print(f"   {r['name']} ({r['code']}): {r['composite']:.1f}分 | 盈亏{r['pnl_pct']:+.1f}%")
    
    good = [r for r in results if 50 <= r['composite'] < 70]
    print(f"\n🟡 良好品种 ({len(good)}只，建议观望):")
    for r in good:
        print(f"   {r['name']} ({r['code']}): {r['composite']:.1f}分 | 盈亏{r['pnl_pct']:+.1f}%")
    
    poor = [r for r in results if r['composite'] < 50]
    print(f"\n🔴 较差品种 ({len(poor)}只，建议减仓/清仓):")
    for r in poor:
        print(f"   {r['name']} ({r['code']}): {r['composite']:.1f}分 | 盈亏{r['pnl_pct']:+.1f}%")
    
    # 保存报告
    report_file = WORKSPACE / 'reports' / f'factor_analysis_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# ETF 持仓因子分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 因子评分表\n\n")
        f.write("| 排名 | 品种 | 代码 | 综合 | 动量 | 估值 | 趋势 | 波动 | 盈亏% | 市值 |\n")
        f.write("|------|------|------|------|------|------|------|------|-------|------|\n")
        for i, r in enumerate(results, 1):
            f.write(f"| {i} | {r['name']} | {r['code']} | {r['composite']:.1f} | {r['momentum']:.1f} | {r['value']:.1f} | {r['trend']:.1f} | {r['volatility']:.1f} | {r['pnl_pct']:+.1f}% | {r['market_value']/1000:.1f}k |\n")
        f.write("\n## 调仓建议\n\n")
        f.write("### 优秀品种\n\n")
        for r in excellent:
            f.write(f"- {r['name']} ({r['code']}): {r['composite']:.1f}分\n")
        f.write("\n### 良好品种\n\n")
        for r in good:
            f.write(f"- {r['name']} ({r['code']}): {r['composite']:.1f}分\n")
        f.write("\n### 较差品种\n\n")
        for r in poor:
            f.write(f"- {r['name']} ({r['code']}): {r['composite']:.1f}分\n")
    
    print(f"\n✅ 报告已保存：{report_file}")
    return results

if __name__ == "__main__":
    generate_report()
