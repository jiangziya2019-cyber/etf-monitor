#!/usr/bin/env python3
"""
ETF Market Data Scanner
Fetches:
1. Mainstream dividend ETF real-time quotes (510880, 515180, 519674, etc.)
2. All-market ETF volume ranking / gain ranking
3. Market sentiment indicators
"""

import sys
import json
from datetime import datetime

try:
    import akshare as ak
    import pandas as pd
except ImportError as e:
    print(json.dumps({"error": f"Missing dependency: {e}", "message": "Run: pip3 install akshare pandas -U"}))
    sys.exit(1)

def get_dividend_etf_quotes():
    """Get real-time quotes for mainstream dividend ETFs"""
    dividend_etf_codes = ["510880", "515180", "519674", "515300", "512530", "510890"]
    
    try:
        # Get all ETF data
        all_etf_data = ak.fund_etf_spot_em()
        
        if all_etf_data is None or len(all_etf_data) == 0:
            return {"error": "No ETF data available"}
        
        # Filter for dividend ETFs
        results = []
        for code in dividend_etf_codes:
            matching = all_etf_data[all_etf_data["代码"] == code]
            if len(matching) > 0:
                row = matching.iloc[0]
                results.append({
                    "代码": code,
                    "名称": str(row.get("名称", "")),
                    "最新价": float(row.get("最新价", 0)),
                    "涨跌幅": f"{float(row.get('涨跌幅', 0)):.2f}%",
                    "涨跌额": float(row.get("涨跌额", 0)),
                    "成交量": int(row.get("成交量", 0)),
                    "成交额 (亿)": float(row.get("成交额", 0)) / 100000000,
                    "IOPV 估值": float(row.get("IOPV 实时估值", 0)),
                    "折价率": f"{float(row.get('基金折价率', 0)):.2f}%",
                })
        
        return results
    except Exception as e:
        return {"error": f"Failed to fetch dividend ETFs: {e}"}

def get_etf_volume_ranking(top_n=20):
    """Get ETF volume ranking for today"""
    try:
        data = ak.fund_etf_spot_em()
        if data is None or len(data) == 0:
            return {"error": "No ETF data available"}
        
        # Sort by volume
        data_sorted = data.sort_values(by="成交量", ascending=False).head(top_n)
        
        results = []
        for _, row in data_sorted.iterrows():
            results.append({
                "排名": len(results) + 1,
                "代码": str(row.get("代码", "")),
                "名称": str(row.get("名称", "")),
                "最新价": float(row.get("最新价", 0)),
                "涨跌幅": f"{float(row.get('涨跌幅', 0)):.2f}%",
                "成交量": int(row.get("成交量", 0)),
                "成交额 (亿)": float(row.get("成交额", 0)) / 100000000,
            })
        
        return results
    except Exception as e:
        return {"error": f"Failed to fetch ETF volume ranking: {e}"}

def get_etf_gain_ranking(top_n=20):
    """Get ETF gain ranking for today"""
    try:
        data = ak.fund_etf_spot_em()
        if data is None or len(data) == 0:
            return {"error": "No ETF data available"}
        
        # Sort by gain percentage
        data_sorted = data.sort_values(by="涨跌幅", ascending=False).head(top_n)
        
        results = []
        for _, row in data_sorted.iterrows():
            results.append({
                "排名": len(results) + 1,
                "代码": str(row.get("代码", "")),
                "名称": str(row.get("名称", "")),
                "最新价": float(row.get("最新价", 0)),
                "涨跌幅": f"{float(row.get('涨跌幅', 0)):.2f}%",
                "成交量": int(row.get("成交量", 0)),
                "成交额 (亿)": float(row.get("成交额", 0)) / 100000000,
            })
        
        return results
    except Exception as e:
        return {"error": f"Failed to fetch ETF gain ranking: {e}"}

def get_market_sentiment():
    """Get market sentiment indicators"""
    try:
        # Get A-share market overview
        market_data = ak.stock_zh_a_spot_em()
        
        if market_data is None or len(market_data) == 0:
            return {"error": "No market data available"}
        
        # Calculate market statistics
        total_stocks = len(market_data)
        rising = len(market_data[market_data["涨跌幅"] > 0])
        falling = len(market_data[market_data["涨跌幅"] < 0])
        flat = len(market_data[market_data["涨跌幅"] == 0])
        
        # Limit up / Limit down
        limit_up = len(market_data[market_data["涨跌幅"] >= 9.8])
        limit_down = len(market_data[market_data["涨跌幅"] <= -9.8])
        
        # Average gain
        avg_gain = market_data["涨跌幅"].mean()
        
        # Total volume and turnover
        total_volume = market_data["成交量"].sum()
        total_turnover = market_data["成交额"].sum() / 100000000  # Convert to 亿
        
        # Market breadth ratio
        breadth_ratio = rising / falling if falling > 0 else float('inf')
        
        return {
            "市场概览": {
                "上涨家数": rising,
                "下跌家数": falling,
                "平盘家数": flat,
                "总股票数": total_stocks,
                "涨跌比": f"{breadth_ratio:.2f}" if breadth_ratio != float('inf') else "N/A",
            },
            "涨停跌停": {
                "涨停家数": limit_up,
                "跌停家数": limit_down,
            },
            "市场情绪": {
                "平均涨跌幅": f"{avg_gain:.2f}%",
                "总成交量 (手)": int(total_volume),
                "总成交额 (亿)": f"{total_turnover:.2f}",
            },
            "情绪判断": "偏多" if rising > falling else "偏空" if falling > rising else "中性",
        }
    except Exception as e:
        return {"error": f"Failed to fetch market sentiment: {e}"}

def format_table(data, title):
    """Format data as markdown table"""
    if isinstance(data, dict) and "error" in data:
        return f"### {title}\n❌ {data['error']}\n"
    
    if not data:
        return f"### {title}\n暂无数据\n"
    
    # Nested dict case (for market sentiment)
    if isinstance(data, dict):
        lines = [f"### {title}\n"]
        for section, items in data.items():
            if isinstance(items, dict):
                lines.append(f"**{section}**:")
                for key, value in items.items():
                    lines.append(f"- {key}: {value}")
                lines.append("")
            else:
                lines.append(f"{section}: {items}")
        return "\n".join(lines)
    
    # List of dicts case
    lines = [f"### {title}\n"]
    
    # Get headers
    headers = list(data[0].keys())
    
    # Create table header
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    
    # Create table rows
    for row in data:
        row_values = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(row_values) + " |")
    
    return "\n".join(lines)

def main():
    print("=" * 80)
    print("ETF 市场数据扫描报告")
    print(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Asia/Shanghai)")
    print("数据来源：akshare (东方财富)")
    print("=" * 80)
    print()
    
    # 1. Dividend ETF quotes
    print("【1】主流红利 ETF 实时行情")
    print("-" * 80)
    dividend_etfs = get_dividend_etf_quotes()
    print(format_table(dividend_etfs, "红利 ETF 行情"))
    print()
    
    # 2. ETF volume ranking
    print("【2】全市场 ETF 成交量排行 TOP20")
    print("-" * 80)
    volume_ranking = get_etf_volume_ranking(20)
    print(format_table(volume_ranking, "ETF 成交量排行"))
    print()
    
    # 3. ETF gain ranking
    print("【3】全市场 ETF 涨幅排行 TOP20")
    print("-" * 80)
    gain_ranking = get_etf_gain_ranking(20)
    print(format_table(gain_ranking, "ETF 涨幅排行"))
    print()
    
    # 4. Market sentiment
    print("【4】市场整体情绪指标")
    print("-" * 80)
    sentiment = get_market_sentiment()
    print(format_table(sentiment, "市场情绪"))
    print()
    
    # Analysis summary
    print("=" * 80)
    print("【分析结论】")
    print("=" * 80)
    
    if dividend_etfs and isinstance(dividend_etfs, list) and len(dividend_etfs) > 0:
        try:
            avg_dividend_change = sum([float(row.get("涨跌幅", "0%").replace("%", "")) 
                                       for row in dividend_etfs]) / len(dividend_etfs)
            print(f"1. 红利 ETF 整体表现：平均涨跌幅 {avg_dividend_change:.2f}%")
            if avg_dividend_change > 0.5:
                print("   → 红利板块今日表现偏强，防御性资金流入明显")
            elif avg_dividend_change < -0.5:
                print("   → 红利板块今日表现偏弱，资金流出或市场风险偏好上升")
            else:
                print("   → 红利板块表现中性，涨跌幅在±0.5% 以内")
        except:
            print("1. 红利 ETF 整体表现：数据计算中...")
    
    if volume_ranking and isinstance(volume_ranking, list) and len(volume_ranking) > 0:
        top_volume = volume_ranking[0]
        print(f"2. 成交最活跃 ETF: {top_volume.get('名称', 'N/A')} ({top_volume.get('代码', 'N/A')})")
        print(f"   成交额：{top_volume.get('成交额 (亿)', 'N/A')} 亿")
        print(f"   涨跌幅：{top_volume.get('涨跌幅', 'N/A')}")
    
    if gain_ranking and isinstance(gain_ranking, list) and len(gain_ranking) > 0:
        top_gain = gain_ranking[0]
        print(f"3. 涨幅最大 ETF: {top_gain.get('名称', 'N/A')} ({top_gain.get('代码', 'N/A')})")
        print(f"   涨幅：{top_gain.get('涨跌幅', 'N/A')}")
    
    if sentiment and isinstance(sentiment, dict) and "情绪判断" in sentiment:
        sentiment_judge = sentiment.get("情绪判断", "N/A")
        print(f"4. 市场整体情绪：{sentiment_judge}")
        if "市场概览" in sentiment:
            rising = sentiment["市场概览"].get("上涨家数", 0)
            falling = sentiment["市场概览"].get("下跌家数", 0)
            print(f"   上涨/下跌比：{rising}:{falling}")
            if sentiment_judge == "偏空":
                print("   → 市场普跌，注意控制仓位风险")
            elif sentiment_judge == "偏多":
                print("   → 市场普涨，赚钱效应较好")
            else:
                print("   → 市场分化，结构性行情为主")
    
    print()
    print("=" * 80)
    print("⚠️ 免责声明：数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。")
    print("=" * 80)

if __name__ == "__main__":
    main()
