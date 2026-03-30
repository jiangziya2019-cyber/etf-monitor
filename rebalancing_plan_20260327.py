#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 调仓计划计算器 - 具体份额计算
"""

import json
from datetime import datetime

# 持仓数据
holdings = [
    {"name": "医药 ETF", "code": "512010", "shares": 7700, "price": 0.361, "market_value": 2779.70},
    {"name": "机器人 AI", "code": "159770", "shares": 500, "price": 0.959, "market_value": 479.50},
    {"name": "创业板 AI", "code": "159363", "shares": 10000, "price": 1.067, "market_value": 10670.00},
    {"name": "创业智能", "code": "159243", "shares": 6000, "price": 1.078, "market_value": 6468.00},
    {"name": "光伏 ETF", "code": "515790", "shares": 3800, "price": 1.102, "market_value": 4187.60},
    {"name": "现金流", "code": "159399", "shares": 18400, "price": 1.117, "market_value": 20552.80},
    {"name": "军工 ETF", "code": "512660", "shares": 300, "price": 1.291, "market_value": 387.30},
    {"name": "航空 TH", "code": "159241", "shares": 1700, "price": 1.283, "market_value": 2181.10},
    {"name": "嘉实原油", "code": "160723", "shares": 2300, "price": 2.710, "market_value": 6233.00},
    {"name": "航空航天", "code": "159227", "shares": 4000, "price": 1.256, "market_value": 5024.00},
    {"name": "AI 智能", "code": "159819", "shares": 5700, "price": 1.477, "market_value": 8418.90},
    {"name": "创业板 50", "code": "159949", "shares": 1000, "price": 1.558, "market_value": 1558.00},
    {"name": "半导体", "code": "512480", "shares": 3300, "price": 1.462, "market_value": 4824.60},
    {"name": "卫星 ETF", "code": "159206", "shares": 4300, "price": 1.592, "market_value": 6845.60},
    {"name": "机床", "code": "159663", "shares": 3200, "price": 1.735, "market_value": 5552.00},
    {"name": "纳指 100", "code": "513110", "shares": 4500, "price": 1.921, "market_value": 8644.50},
    {"name": "储能电池", "code": "159566", "shares": 6200, "price": 2.250, "market_value": 13950.00},
    {"name": "标普 500", "code": "513500", "shares": 4600, "price": 2.200, "market_value": 10120.00},
    {"name": "红利 ETF", "code": "510880", "shares": 2100, "price": 3.250, "market_value": 6825.00},
    {"name": "300ETF", "code": "510300", "shares": 3000, "price": 4.501, "market_value": 13503.00},
    {"name": "500ETF", "code": "510500", "shares": 900, "price": 7.769, "market_value": 6992.10},
    {"name": "黄金 9999", "code": "159937", "shares": 1700, "price": 9.412, "market_value": 16000.40},
]

total_value = 169037.00

# 调仓决策
SELL_ALL = ["159770", "512660", "159937", "512480", "159243", "515790", "159241", "513110", "513500", "510300"]
REDUCE = {"159399": 0.50, "159566": 0.30, "159363": 0.30, "159819": 0.50, "510500": 0.50}

holdings_map = {h["code"]: h for h in holdings}

print("=" * 85)
print("ETF 调仓计划 - 具体份额计算")
print(f"计算时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  当前总市值：¥{total_value:,.2f}")
print("=" * 85)

# 清仓
print("\n【一、清仓】10 只")
print("-" * 85)
sell_proceeds = 0
for code in SELL_ALL:
    h = holdings_map[code]
    proceeds = h["market_value"]
    sell_proceeds += proceeds
    print(f"  {code} {h['name']:<10} 卖出 {h['shares']:>6,} 份 @ ¥{h['price']:.3f} = ¥{proceeds:>10,.2f}")
print(f"  清仓小计：¥{sell_proceeds:,.2f}")

# 减仓
print("\n【二、减仓】5 只")
print("-" * 85)
reduce_proceeds = 0
for code, pct in REDUCE.items():
    h = holdings_map[code]
    shares_sell = int(h["shares"] * pct)
    proceeds = shares_sell * h["price"]
    reduce_proceeds += proceeds
    print(f"  {code} {h['name']:<10} 卖出 {shares_sell:>6,} 份 ({pct:.0%}) @ ¥{h['price']:.3f} = ¥{proceeds:>10,.2f}")
    print(f"           → 剩余 {h['shares'] - shares_sell:,} 份，市值 ¥{(h['shares'] - shares_sell) * h['price']:,.2f}")
print(f"  减仓小计：¥{reduce_proceeds:,.2f}")

# 资金汇总
total_proceeds = sell_proceeds + reduce_proceeds
print(f"\n【三、可用资金】¥{total_proceeds:,.2f}")

# 建仓
redial_price = 3.250
target_redial = 28000
redial_shares = int(target_redial / redial_price / 100) * 100
redial_cost = redial_shares * redial_price
print(f"\n【四、建仓】红利 ETF 加仓")
print(f"  510880 红利 ETF   买入 {redial_shares:,} 份 @ ¥{redial_price:.3f} = ¥{redial_cost:,.2f}")
print(f"  加仓后：{2100 + redial_shares:,} 份，市值 ¥{(2100 + redial_shares) * redial_price:,.2f}")

# 现金
remaining_cash = total_proceeds - redial_cost
target_cash = total_value * 0.225
print(f"\n【五、现金】剩余 ¥{remaining_cash:,.2f}  目标 22.5%=¥{target_cash:,.2f}  {'✅' if remaining_cash >= target_cash else '⚠️'}")

# 调仓后持仓
print("\n【六、调仓后持仓】")
print(f"  {'代码':<8} {'名称':<10} {'份额':>10} {'价格':>8} {'市值':>12} {'权重':>8}")
print("-" * 85)

new_value = 0
for h in holdings:
    code = h["code"]
    if code in SELL_ALL:
        continue
    if code in REDUCE:
        new_shares = int(h["shares"] * (1 - REDUCE[code]))
    else:
        new_shares = h["shares"]
    if code == "510880":
        new_shares += redial_shares
    
    new_mv = new_shares * h["price"]
    new_value += new_mv
    weight = new_mv / (new_value + remaining_cash) * 100
    print(f"  {code} {h['name']:<10} {new_shares:>10,} ¥{h['price']:>7.3f} ¥{new_mv:>11,.2f} {weight:>7.1f}%")

print("-" * 85)
print(f"  持仓市值：¥{new_value:,.2f}  现金：¥{remaining_cash:,.2f}  总计：¥{new_value + remaining_cash:,.2f}")
print(f"  现金占比：{remaining_cash / (new_value + remaining_cash) * 100:.1f}%")
