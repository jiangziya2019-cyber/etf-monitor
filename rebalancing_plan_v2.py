#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 调仓计划 v2 - 优化现金占比至 22.5%
"""

from datetime import datetime

holdings = [
    {"name": "医药 ETF", "code": "512010", "shares": 7700, "price": 0.361, "mv": 2779.70},
    {"name": "机器人 AI", "code": "159770", "shares": 500, "price": 0.959, "mv": 479.50},
    {"name": "创业板 AI", "code": "159363", "shares": 10000, "price": 1.067, "mv": 10670.00},
    {"name": "创业智能", "code": "159243", "shares": 6000, "price": 1.078, "mv": 6468.00},
    {"name": "光伏 ETF", "code": "515790", "shares": 3800, "price": 1.102, "mv": 4187.60},
    {"name": "现金流", "code": "159399", "shares": 18400, "price": 1.117, "mv": 20552.80},
    {"name": "军工 ETF", "code": "512660", "shares": 300, "price": 1.291, "mv": 387.30},
    {"name": "航空 TH", "code": "159241", "shares": 1700, "price": 1.283, "mv": 2181.10},
    {"name": "嘉实原油", "code": "160723", "shares": 2300, "price": 2.710, "mv": 6233.00},
    {"name": "航空航天", "code": "159227", "shares": 4000, "price": 1.256, "mv": 5024.00},
    {"name": "AI 智能", "code": "159819", "shares": 5700, "price": 1.477, "mv": 8418.90},
    {"name": "创业板 50", "code": "159949", "shares": 1000, "price": 1.558, "mv": 1558.00},
    {"name": "半导体", "code": "512480", "shares": 3300, "price": 1.462, "mv": 4824.60},
    {"name": "卫星 ETF", "code": "159206", "shares": 4300, "price": 1.592, "mv": 6845.60},
    {"name": "机床", "code": "159663", "shares": 3200, "price": 1.735, "mv": 5552.00},
    {"name": "纳指 100", "code": "513110", "shares": 4500, "price": 1.921, "mv": 8644.50},
    {"name": "储能电池", "code": "159566", "shares": 6200, "price": 2.250, "mv": 13950.00},
    {"name": "标普 500", "code": "513500", "shares": 4600, "price": 2.200, "mv": 10120.00},
    {"name": "红利 ETF", "code": "510880", "shares": 2100, "price": 3.250, "mv": 6825.00},
    {"name": "300ETF", "code": "510300", "shares": 3000, "price": 4.501, "mv": 13503.00},
    {"name": "500ETF", "code": "510500", "shares": 900, "price": 7.769, "mv": 6992.10},
    {"name": "黄金 9999", "code": "159937", "shares": 1700, "price": 9.412, "mv": 16000.40},
]

total_value = 169037.00
target_cash = total_value * 0.225  # 38,033 元

# 清仓 10 只
SELL_ALL = ["159770", "512660", "159937", "512480", "159243", "515790", "159241", "513110", "513500", "510300"]
# 减仓 5 只
REDUCE = {"159399": 0.50, "159566": 0.30, "159363": 0.30, "159819": 0.50, "510500": 0.50}

holdings_map = {h["code"]: h for h in holdings}

# 计算回款
sell_proceeds = sum(holdings_map[c]["mv"] for c in SELL_ALL)
reduce_proceeds = sum(holdings_map[c]["mv"] * pct for c, pct in REDUCE.items())
total_proceeds = sell_proceeds + reduce_proceeds

# 建仓计划（优化现金占比）
# 目标：现金 38,033 元，所以建仓 = total_proceeds - 38033 = 54,131 元
build_target = total_proceeds - target_cash  # 54,131 元

# 建仓分配
# 1. 红利 ETF: 28,000 元（老板指定）
# 2. 科创 50ETF: 10,000 元（科技成长）
# 3. 医药 ETF 加仓：8,000 元（低位布局）
# 4. 创业板 50 加仓：8,131 元（弹性配置）

BUILD_PLAN = [
    {"code": "510880", "name": "红利 ETF", "price": 3.250, "target": 28000},
    {"code": "588000", "name": "科创 50", "price": 1.050, "target": 10000},  # 估计价
    {"code": "512010", "name": "医药 ETF", "price": 0.361, "target": 8000},
    {"code": "159949", "name": "创业板 50", "price": 1.558, "target": 8131},
]

print("=" * 90)
print("ETF 调仓计划 v2 - 优化现金占比至 22.5%")
print(f"计算时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  当前总市值：¥{total_value:,.2f}")
print("=" * 90)

# 清仓
print("\n【一、清仓】10 只")
print("-" * 90)
for code in SELL_ALL:
    h = holdings_map[code]
    print(f"  {code} {h['name']:<10} 卖出 {h['shares']:>6,} 份 @ ¥{h['price']:.3f} = ¥{h['mv']:>10,.2f}")
print(f"  清仓小计：¥{sell_proceeds:,.2f}")

# 减仓
print("\n【二、减仓】5 只")
print("-" * 90)
for code, pct in REDUCE.items():
    h = holdings_map[code]
    shares_sell = int(h["shares"] * pct)
    proceeds = shares_sell * h["price"]
    print(f"  {code} {h['name']:<10} 卖出 {shares_sell:>6,} 份 ({pct:.0%}) @ ¥{h['price']:.3f} = ¥{proceeds:>10,.2f}")
    print(f"           → 剩余 {h['shares'] - shares_sell:,} 份")
print(f"  减仓小计：¥{reduce_proceeds:,.2f}")

print(f"\n【三、可用资金】¥{total_proceeds:,.2f}")

# 建仓
print("\n【四、建仓】4 只")
print("-" * 90)
build_total = 0
for item in BUILD_PLAN:
    shares = int(item["target"] / item["price"] / 100) * 100
    cost = shares * item["price"]
    build_total += cost
    # 检查是否是加仓
    if item["code"] in holdings_map:
        old_shares = holdings_map[item["code"]]["shares"]
        print(f"  {item['code']} {item['name']:<10} 买入 {shares:>6,} 份 + 原有 {old_shares:>6,} 份 = {old_shares + shares:,} 份 @ ¥{item['price']:.3f} = ¥{cost:>10,.2f}")
    else:
        print(f"  {item['code']} {item['name']:<10} 买入 {shares:>6,} 份 @ ¥{item['price']:.3f} = ¥{cost:>10,.2f}  [新建]")
print(f"  建仓小计：¥{build_total:,.2f}")

# 现金
remaining_cash = total_proceeds - build_total
print(f"\n【五、现金】¥{remaining_cash:,.2f}  目标 22.5%=¥{target_cash:,.2f}  实际占比 {remaining_cash / (total_value - build_total + build_total):.1f}%")

# 调仓后持仓
print("\n【六、调仓后持仓汇总】")
print(f"  {'代码':<8} {'名称':<10} {'操作':>8} {'份额':>10} {'价格':>8} {'市值':>12} {'权重':>8}")
print("-" * 90)

new_holdings = {}
for h in holdings:
    code = h["code"]
    if code in SELL_ALL:
        continue
    if code in REDUCE:
        new_shares = int(h["shares"] * (1 - REDUCE[code]))
        action = "减仓"
    else:
        new_shares = h["shares"]
        action = "持有"
    new_holdings[code] = {"shares": new_shares, "price": h["price"], "name": h["name"], "action": action}

# 加仓
for item in BUILD_PLAN:
    code = item["code"]
    shares_buy = int(item["target"] / item["price"] / 100) * 100
    if code in new_holdings:
        new_holdings[code]["shares"] += shares_buy
        new_holdings[code]["action"] = "加仓"
    else:
        new_holdings[code] = {"shares": shares_buy, "price": item["price"], "name": item["name"], "action": "新建"}

# 输出
new_value = 0
for code, h in sorted(new_holdings.items()):
    mv = h["shares"] * h["price"]
    new_value += mv
    weight = mv / (new_value + remaining_cash) * 100
    print(f"  {code} {h['name']:<10} {h['action']:>8} {h['shares']:>10,} ¥{h['price']:>7.3f} ¥{mv:>11,.2f} {weight:>7.1f}%")

print("-" * 90)
print(f"  持仓市值：¥{new_value:,.2f}  现金：¥{remaining_cash:,.2f}  总计：¥{new_value + remaining_cash:,.2f}")
print(f"  现金占比：{remaining_cash / (new_value + remaining_cash) * 100:.1f}%  目标：22.5%")
