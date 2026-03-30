#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓 ETF 数据调取测试
测试 akshare 和 Tushare 双数据源
"""

import os
from datetime import datetime

# 持仓 ETF 列表（22 只）
HOLDINGS_ETF = [
    "159949", "512480", "159206", "159663", "513110", "159566", 
    "513500", "510880", "510300", "510500", "159937", "512010",
    "159770", "159363", "159243", "515790", "159399", "512660",
    "159241", "160723", "159227", "159819"
]

print("="*60)
print("持仓 ETF 数据调取测试")
print("="*60)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"测试标的：{len(HOLDINGS_ETF)} 只持仓 ETF")
print("="*60)

# ========== 测试 akshare ==========
print("\n【1】测试 akshare 数据源...")
try:
    import akshare as ak
    print("✅ akshare 模块导入成功")
    
    df = ak.fund_etf_spot_em()
    print(f"✅ akshare 获取 ETF 行情成功，共 {len(df)} 只 ETF")
    
    # 提取持仓 ETF 数据
    found = 0
    not_found = []
    prices_akshare = {}
    
    for _, row in df.iterrows():
        code = str(row['代码']).strip()
        if code in HOLDINGS_ETF:
            price = float(row['最新价'])
            change_pct = float(row['涨跌幅'])
            prices_akshare[code] = {"price": price, "change_pct": change_pct}
            found += 1
    
    for code in HOLDINGS_ETF:
        if code not in prices_akshare:
            not_found.append(code)
    
    print(f"✅ 找到持仓 ETF: {found}/{len(HOLDINGS_ETF)} 只")
    if not_found:
        print(f"⚠️ 未找到：{', '.join(not_found)}")
    
    # 显示部分数据
    print("\n📊 部分持仓 ETF 数据（akshare）:")
    print("-" * 60)
    for i, code in enumerate(list(prices_akshare.keys())[:10]):
        data = prices_akshare[code]
        symbol = df[df['代码']==code].iloc[0]['名称']
        print(f"{code} | {symbol} | {data['price']:.3f}元 | {data['change_pct']:+.2f}%")
    if len(prices_akshare) > 10:
        print(f"... 还有 {len(prices_akshare)-10} 只")
    
    AKSHARE_OK = True
    
except Exception as e:
    print(f"❌ akshare 测试失败：{e}")
    AKSHARE_OK = False

# ========== 测试 Tushare ==========
print("\n" + "="*60)
print("【2】测试 Tushare Pro 数据源...")
try:
    import tushare as ts
    token = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
    ts.set_token(token)
    pro = ts.pro_api()
    print("✅ Tushare 模块导入成功，Token 配置正确")
    
    # 测试获取 ETF 数据
    today = datetime.now().strftime('%Y%m%d')
    prices_tushare = {}
    
    # 逐个获取持仓 ETF 数据（避免一次性请求太多）
    print(f"📊 获取持仓 ETF 数据（{today}）...")
    
    for code in HOLDINGS_ETF[:5]:  # 先测试前 5 只
        try:
            # ETF 代码格式转换
            if code.startswith('15') or code.startswith('16'):
                ts_code = f"{code}.SZ"
            else:
                ts_code = f"{code}.SH"
            
            df = pro.fund_daily(ts_code=ts_code, trade_date=today)
            if len(df) > 0:
                price = float(df.iloc[0]['close'])
                prices_tushare[code] = price
                print(f"  ✅ {code} ({ts_code}): {price:.3f}元")
            else:
                print(f"  ⚠️ {code}: 今日无数据（可能休市）")
        except Exception as e:
            print(f"  ❌ {code}: {e}")
    
    if prices_tushare:
        print(f"\n✅ Tushare 成功获取 {len(prices_tushare)} 只 ETF 价格")
        TUSHARE_OK = True
    else:
        print(f"\n⚠️ Tushare 未获取到数据（可能休市或接口限制）")
        TUSHARE_OK = False
    
except Exception as e:
    print(f"❌ Tushare 测试失败：{e}")
    TUSHARE_OK = False

# ========== 测试结果总结 ==========
print("\n" + "="*60)
print("【3】测试结果总结")
print("="*60)

print(f"\n📊 数据源状态:")
print(f"  - akshare: {'✅ 可用' if AKSHARE_OK else '❌ 不可用'}")
print(f"  - Tushare Pro: {'✅ 可用' if TUSHARE_OK else '❌ 不可用'}")

if AKSHARE_OK and TUSHARE_OK:
    print(f"\n✅ 双数据源配置成功！系统可正常运行！")
    print(f"   - 主数据源：akshare")
    print(f"   - 备份数据源：Tushare Pro")
elif AKSHARE_OK:
    print(f"\n⚠️ 仅 akshare 可用，Tushare 需进一步调试")
elif TUSHARE_OK:
    print(f"\n⚠️ 仅 Tushare 可用，akshare 需进一步调试")
else:
    print(f"\n❌ 双数据源都不可用，需要检查网络或配置！")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
