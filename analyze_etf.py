#!/usr/bin/env python3
"""
Analyze ETF portfolio data and generate recommendations.
"""

import json
from datetime import datetime

# Load raw data
with open("/home/admin/openclaw/workspace/etf_raw_data.json", "r") as f:
    etf_data = json.load(f)

# Portfolio weights (assumed equal weight for now, or user can provide)
# For grid analysis, we need reference prices (cost basis)
# Since we don't have cost basis, we'll analyze based on recent performance

print("="*100)
print("=== ETF 持仓数据分析报告 ===")
print(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
print()

# 1. 现金流 ETF (159399) 分析
print("="*100)
print("=== 1. 现金流 ETF (159399) 减仓分析 ===")
print("="*100)

cf_etf = etf_data.get("159399", {})
if cf_etf:
    price = cf_etf.get("price")
    change_pct = cf_etf.get("change_pct")
    volume = cf_etf.get("volume")
    amount = cf_etf.get("amount")
    
    print(f"当前价格：{price}")
    print(f"今日涨跌：{change_pct}")
    print(f"成交量：{volume:,} 手")
    print(f"成交额：{amount:,} 万")
    print()
    
    # Analysis based on today's performance
    print("分析要点：")
    print(f"- 今日下跌 {change_pct}，表现弱于大盘（300ETF -1.41%）")
    print(f"- 成交量 {int(volume)/100:.0f}万手，成交活跃")
    print()
    
    # Recommendation
    print("减仓建议（12.1% → 8%）：")
    if change_pct and change_pct < -1.0:
        print("⚠️ 今日表现较弱，但单日下跌不构成减仓理由")
        print("✅ 建议：按计划执行减仓，但可分批进行，避免在单日大跌时集中卖出")
        print("   - 第一批：减仓 2%（12.1% → 10.1%）")
        print("   - 第二批：观察 3-5 个交易日，若继续走弱再减至 8%")
    else:
        print("✅ 当前价格相对平稳，可按计划执行减仓")
else:
    print("未找到现金流 ETF 数据")

print()

# 2. 网格加仓条件分析
print("="*100)
print("=== 2. 网格加仓条件分析 ===")
print("="*100)
print()
print("说明：网格加仓需要参考成本价/建仓价。以下基于今日跌幅分析相对强弱。")
print("假设网格条件：较成本价下跌 -5%/-10%/-15% 触发加仓")
print()

# Sort by change_pct to find the worst performers
sorted_etfs = []
for code, data in etf_data.items():
    if "price" in data and "change_pct" in data:
        try:
            change_pct = float(data["change_pct"].replace("%", "")) if isinstance(data["change_pct"], str) else data["change_pct"]
            sorted_etfs.append((code, data["name"], change_pct, data["price"]))
        except:
            pass

sorted_etfs.sort(key=lambda x: x[2] if x[2] is not None else 0)

print("按今日跌幅排序（从大到小）：")
print(f"{'代码':<8} {'名称':<14} {'最新价':>10} {'今日涨跌%':>12} {'网格状态':>15}")
print("-"*65)

for code, name, change_pct, price in sorted_etfs:
    if change_pct is not None:
        # Grid status (assuming reference is recent high or cost)
        if change_pct <= -15:
            status = "🔴 触发 -15%"
        elif change_pct <= -10:
            status = "🟠 触发 -10%"
        elif change_pct <= -5:
            status = "🟡 触发 -5%"
        else:
            status = "🟢 未触发"
        
        print(f"{code:<8} {name:<14} {price:>10} {change_pct:>11.2f}% {status:>15}")

print()
print("网格加仓建议：")
print("- 当前市场普跌，多数 ETF 跌幅在 -1% 到 -3% 之间")
print("- 暂未触发 -5% 网格加仓条件")
print("- 若后续继续下跌，关注以下品种的加仓机会：")
worst_3 = sorted_etfs[:3]
for code, name, change_pct, price in worst_3:
    print(f"  • {code} {name} (今日 {change_pct:.2f}%)")

print()

# 3. 整体市场概况
print("="*100)
print("=== 3. 整体市场概况 ===")
print("="*100)
print()

# Count positive/negative
positive = sum(1 for _, _, cp, _ in sorted_etfs if cp is not None and cp > 0)
negative = sum(1 for _, _, cp, _ in sorted_etfs if cp is not None and cp < 0)
total = positive + negative

print(f"上涨：{positive} 只 | 下跌：{negative} 只 | 总计：{total} 只")
print(f"市场情绪：{'偏多' if positive > negative else '偏空'}")
print()

# Best and worst performers
if sorted_etfs:
    best = sorted_etfs[-1]  # Last is best (sorted ascending)
    worst = sorted_etfs[0]  # First is worst
    print(f"今日最佳：{best[1]} ({best[0]}) {best[2]:.2f}%")
    print(f"今日最差：{worst[1]} ({worst[0]}) {worst[2]:.2f}%")

print()

# 4. 调仓建议总结
print("="*100)
print("=== 4. 调仓建议总结 ===")
print("="*100)
print()
print("【减仓操作】")
print("现金流 ETF (159399)：建议按计划从 12.1% 减至 8%")
print("  - 理由：降低单一品种集中度，优化组合风险")
print("  - 执行：可分 2 批完成，避免集中卖出")
print()
print("【加仓操作】")
print("今日新建仓/加仓品种：")
print("  • 510880 红利 ETF (+0.28%) - 防御性配置，今日逆势上涨")
print("  • 510300 300ETF (-1.41%) - 核心宽基，逢低布局")
print("  • 510500 500ETF (-1.79%) - 中小盘代表，逢低布局")
print("  • 513500 标普 500ETF (+0.32%) - QDII 配置，分散风险")
print()
print("【网格监控】")
print("  - 当前暂无品种触发 -5% 网格条件")
print("  - 重点关注：科创芯片 ETF (-3.65%)、新能源车 ETF (-3.42%)")
print("  - 若继续下跌至 -5%，可考虑触发网格加仓")
print()
print("="*100)
print("⚠️ 风险提示：以上分析仅供参考，不构成投资建议。市场有风险，投资需谨慎。")
print("="*100)
