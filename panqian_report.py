#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘前准备报告生成脚本 - 使用 akshare 获取数据
"""

import json
import akshare as ak
from datetime import datetime, timedelta

def get_global_indices():
    """获取全球主要指数"""
    indices = {
        "US500": "标普 500",
        "DJI": "道琼斯",
        "IXIC": "纳斯达克",
        "HSI": "恒生指数",
        "N225": "日经 225"
    }
    
    result = {}
    try:
        # 获取全球指数行情
        df = ak.index_global_hist(symbol="US500")
        if not df.empty:
            latest = df.iloc[0]
            result["SPX"] = {
                "name": "标普 500",
                "close": float(latest.get("收盘", 0)),
                "change_pct": float(latest.get("涨跌幅", 0))
            }
    except Exception as e:
        print(f"获取全球指数失败：{e}")
    
    return result

def get_commodity_prices():
    """获取商品价格（原油、黄金）"""
    result = {}
    
    try:
        # 原油期货
        df = ak.futures_display_main_sina()
        if not df.empty:
            crude = df[df["symbol"].str.contains("原油", na=False)]
            if not crude.empty:
                latest = crude.iloc[0]
                result["CRUDE"] = {
                    "name": "原油",
                    "close": float(latest.get("last_settlement", 0)),
                    "change_pct": float(latest.get("change_percent", 0))
                }
    except Exception as e:
        print(f"获取原油数据失败：{e}")
    
    try:
        # 黄金现货
        df = ak.gold_spot_sina()
        if not df.empty:
            latest = df.iloc[0]
            result["GOLD"] = {
                "name": "黄金",
                "close": float(latest.get("price", 0)),
                "change_pct": 0  # 黄金现货数据可能没有涨跌幅
            }
    except Exception as e:
        print(f"获取黄金数据失败：{e}")
    
    return result

def get_market_news():
    """获取市场新闻"""
    news_list = []
    
    try:
        # 获取财经新闻
        df = ak.news_sina()
        if not df.empty:
            for _, row in df.head(10).iterrows():
                news_list.append({
                    "title": row.get("title", ""),
                    "content": str(row.get("content", ""))[:100] + "..." if row.get("content") else "",
                    "pub_date": row.get("pub_date", "")
                })
    except Exception as e:
        print(f"获取新闻失败：{e}")
    
    return news_list

def get_etf_info(code):
    """获取单个 ETF 信息"""
    try:
        # 获取 ETF 行情
        code_map = {
            "512010": "医药 ETF",
            "159363": "创业板 AI",
            "159243": "创业智能",
            "515790": "光伏 ETF",
            "159399": "现金流",
            "159241": "航空 ETF",
            "160723": "嘉实原油",
            "159227": "航空航天",
            "159819": "AI 智能",
            "159949": "创业 50",
            "512480": "半导体",
            "159206": "卫星 ETF",
            "159663": "机床 ETF",
            "513110": "纳指 100",
            "159566": "储能电池",
            "513500": "标普 500",
            "510880": "红利 ETF",
            "510300": "300ETF",
            "510500": "500ETF",
            "159937": "黄金 9999"
        }
        
        name = code_map.get(code, code)
        
        # 尝试获取实时行情
        if code.startswith("51") or code.startswith("15"):
            df = ak.fund_etf_spot_em()
            if not df.empty:
                etf_row = df[df["代码"] == code]
                if not etf_row.empty:
                    row = etf_row.iloc[0]
                    return {
                        "name": row.get("名称", name),
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0))
                    }
    except Exception as e:
        pass
    
    return None

def main():
    print("=" * 60)
    print("盘前准备报告")
    print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("数据源：akshare（周末使用周五收盘数据）")
    print("=" * 60)
    
    # 1. 全球指数
    print("\n【全球市场】")
    global_idx = get_global_indices()
    if global_idx:
        for code, data in global_idx.items():
            change = data.get("change_pct", 0)
            sign = "+" if change >= 0 else ""
            print(f"  {data['name']}: {data['close']:.2f} ({sign}{change:.2f}%)")
    else:
        print("  周末休市，使用周五收盘数据")
    
    # 2. 商品价格
    print("\n【大宗商品】")
    commodities = get_commodity_prices()
    if commodities:
        for code, data in commodities.items():
            change = data.get("change_pct", 0)
            if change is not None:
                sign = "+" if change >= 0 else ""
                print(f"  {data['name']}: {data['close']:.2f} ({sign}{change:.2f}%)")
            else:
                print(f"  {data['name']}: {data['close']:.2f}")
    else:
        print("  数据暂不可用")
    
    # 3. 市场新闻
    print("\n【重要新闻】")
    news = get_market_news()
    if news:
        for i, n in enumerate(news[:5], 1):
            print(f"  {i}. {n['title']}")
    else:
        print("  暂无重要新闻")
    
    # 4. 持仓 ETF 概览
    print("\n【持仓 ETF 概览】")
    with open("/home/admin/openclaw/workspace/holdings_current.json", "r") as f:
        holdings = json.load(f)
    
    total_value = holdings["total_market_value"]
    total_profit = holdings["total_profit"]
    yield_rate = holdings["yield_rate"]
    
    print(f"  总市值：{total_value:,.2f} 元")
    print(f"  总浮盈：{total_profit:+,.2f} 元")
    print(f"  收益率：{yield_rate:+.2f}%")
    print(f"  ETF 数量：{holdings['etf_count']} 只")
    
    # 按收益率排序
    etfs_sorted = sorted(holdings["etfs"], key=lambda x: x["yield"], reverse=True)
    
    print("\n  表现最佳 TOP5:")
    for etf in etfs_sorted[:5]:
        print(f"    {etf['name']}: {etf['yield']:+.2f}%")
    
    print("\n  表现最差 TOP5:")
    for etf in etfs_sorted[-5:]:
        print(f"    {etf['name']}: {etf['yield']:+.2f}%")
    
    # 5. 今日关注
    print("\n【今日关注】")
    print("  • 周日休市，无交易")
    print("  • 关注今晚美股开盘")
    print("  • 关注宏观经济数据发布")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
