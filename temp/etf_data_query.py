#!/usr/bin/env python3
"""
ETF Real-time Data Query Script
Fetches real-time data for 27 ETFs, market indices, sector performance, and fund flows.
"""

import json
import sys
from datetime import datetime

try:
    import akshare as ak
    import pandas as pd
except ImportError as e:
    print(json.dumps({"error": f"Missing dependency: {e}", "message": "Run: pip3 install akshare pandas"}))
    sys.exit(1)

# Target ETFs
TARGET_ETFS = [
    "512010", "512690", "159363", "512880", "515790", "512660", "588000",
    "159949", "512480", "159930", "513110", "513500", "517520", "510300",
    "510500", "518880", "159770", "159243", "159399", "159241", "160723",
    "159227", "159819", "159206", "159663", "159566", "159937"
]

# Market indices
MARKET_INDICES = {
    "沪深 300": "000300",
    "创业板指": "399006",
    "科创 50": "000688",
    "上证指数": "000001",
    "深证成指": "399001",
    "中证 500": "000905",
    "中证 1000": "000852",
    "恒生指数": "HSI",
    "恒生科技": "HSTECH"
}

def get_etf_spot_data(etf_codes):
    """Get real-time ETF spot data"""
    try:
        df = ak.fund_etf_spot_em()
        if df is None or len(df) == 0:
            return []
        
        # Filter for target ETFs
        result = []
        for code in etf_codes:
            row = df[df['代码'] == code]
            if len(row) > 0:
                r = row.iloc[0]
                result.append({
                    "代码": code,
                    "名称": r.get("名称", ""),
                    "最新价": float(r.get("最新价", 0)) if r.get("最新价") else 0,
                    "涨跌额": float(r.get("涨跌额", 0)) if r.get("涨跌额") else 0,
                    "涨跌幅": float(r.get("涨跌幅", 0)) if r.get("涨跌幅") else 0,
                    "成交量": int(r.get("成交量", 0)) if r.get("成交量") else 0,
                    "成交额": float(r.get("成交额", 0)) if r.get("成交额") else 0,
                    "IOPV 实时估值": float(r.get("IOPV 实时估值", 0)) if r.get("IOPV 实时估值") else 0,
                    "基金折价率": float(r.get("基金折价率", 0)) if r.get("基金折价率") else 0,
                    "主力净流入": float(r.get("主力净流入 - 净额", 0)) if r.get("主力净流入 - 净额") else 0,
                    "主力净流入占比": float(r.get("主力净流入 - 净占比", 0)) if r.get("主力净流入 - 净占比") else 0,
                    "超大单净流入": float(r.get("超大单净流入 - 净额", 0)) if r.get("超大单净流入 - 净额") else 0,
                    "大单净流入": float(r.get("大单净流入 - 净额", 0)) if r.get("大单净流入 - 净额") else 0,
                    "中单净流入": float(r.get("中单净流入 - 净额", 0)) if r.get("中单净流入 - 净额") else 0,
                    "小单净流入": float(r.get("小单净流入 - 净额", 0)) if r.get("小单净流入 - 净额") else 0,
                    "换手率": float(r.get("换手率", 0)) if r.get("换手率") else 0,
                    "总市值": float(r.get("总市值", 0)) if r.get("总市值") else 0,
                    "数据日期": str(r.get("数据日期", "")),
                    "更新时间": str(r.get("更新时间", ""))
                })
        return result
    except Exception as e:
        print(f"Error getting ETF spot data: {e}", file=sys.stderr)
        return []

def get_index_data():
    """Get market index data"""
    try:
        # A-share indices
        df = ak.stock_zh_index_spot_em()
        result = {}
        for name, code in MARKET_INDICES.items():
            if code.startswith("H"):  # HK indices
                continue
            row = df[df['代码'] == code]
            if len(row) > 0:
                r = row.iloc[0]
                result[name] = {
                    "代码": code,
                    "最新价": float(r.get("最新价", 0)) if r.get("最新价") else 0,
                    "涨跌额": float(r.get("涨跌额", 0)) if r.get("涨跌额") else 0,
                    "涨跌幅": float(r.get("涨跌幅", 0)) if r.get("涨跌幅") else 0,
                    "开盘": float(r.get("今开", 0)) if r.get("今开") else 0,
                    "最高": float(r.get("最高", 0)) if r.get("最高") else 0,
                    "最低": float(r.get("最低", 0)) if r.get("最低") else 0,
                    "昨收": float(r.get("昨收", 0)) if r.get("昨收") else 0,
                }
        
        # HK indices
        try:
            hk_df = ak.stock_hk_index_spot_em()
            for name, code in MARKET_INDICES.items():
                if not code.startswith("H"):
                    continue
                row = hk_df[hk_df['代码'] == code]
                if len(row) > 0:
                    r = row.iloc[0]
                    result[name] = {
                        "代码": code,
                        "最新价": float(r.get("最新价", 0)) if r.get("最新价") else 0,
                        "涨跌额": float(r.get("涨跌额", 0)) if r.get("涨跌额") else 0,
                        "涨跌幅": float(r.get("涨跌幅", 0)) if r.get("涨跌幅") else 0,
                    }
        except Exception as e:
            print(f"Error getting HK indices: {e}", file=sys.stderr)
        
        return result
    except Exception as e:
        print(f"Error getting index data: {e}", file=sys.stderr)
        return {}

def get_sector_performance():
    """Get sector/industry performance data"""
    try:
        # Try to get sector concept performance
        # Use stock_board_concept_name_em to get concept sectors
        try:
            df = ak.stock_board_concept_name_em()
            if df is None or len(df) == 0:
                return []
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "行业": row.get("板块名称", ""),
                    "行业指数": float(row.get("板块指数", 0)) if row.get("板块指数") else 0,
                    "涨跌幅": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "主力净流入": 0,
                    "主力净流入占比": 0,
                    "上涨家数": 0,
                    "下跌家数": 0,
                })
            # Sort by change_pct and return top 20
            result.sort(key=lambda x: x.get('涨跌幅', 0), reverse=True)
            return result[:20]
        except:
            pass
        
        return []
    except Exception as e:
        print(f"Error getting sector performance: {e}", file=sys.stderr)
        return []

def get_market_fund_flow():
    """Get overall market fund flow"""
    try:
        # Try to get market fund flow data
        df = ak.stock_market_fund_flow()
        if df is None or len(df) == 0:
            return {}
        
        # Check column names
        cols = df.columns.tolist()
        
        row = df.iloc[0]
        result = {
            "日期": str(row.get("日期", "")),
        }
        
        # Map possible column names
        for field in ["主力净流入", "主力净流入-净额", "主力资金净流入"]:
            if field in cols:
                result["主力净流入"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        for field in ["主力净流入占比", "主力净流入-净占比"]:
            if field in cols:
                result["主力净流入占比"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        for field in ["超大单净流入", "超大单净流入-净额"]:
            if field in cols:
                result["超大单净流入"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        for field in ["大单净流入", "大单净流入 - 净额"]:
            if field in cols:
                result["大单净流入"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        for field in ["中单净流入", "中单净流入 - 净额"]:
            if field in cols:
                result["中单净流入"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        for field in ["小单净流入", "小单净流入 - 净额"]:
            if field in cols:
                result["小单净流入"] = float(row.get(field, 0)) if row.get(field) else 0
                break
        
        return result
    except Exception as e:
        print(f"Error getting market fund flow: {e}", file=sys.stderr)
        return {}

def main():
    print("=" * 80)
    print("ETF 实时行情数据扫描")
    print(f"扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. Get ETF data
    print("\n【1】目标 ETF 实时行情")
    print("-" * 80)
    etf_data = get_etf_spot_data(TARGET_ETFS)
    
    if etf_data:
        # Print header
        print(f"{'代码':<8} {'名称':<15} {'最新价':>8} {'涨跌幅':>8} {'成交量':>12} {'成交额 (亿)':>10} {'主力净流入 (万)':>12} {'更新时间':<20}")
        print("-" * 80)
        
        for etf in etf_data:
            code = etf['代码']
            name = etf['名称'][:12]
            price = etf['最新价']
            change_pct = etf['涨跌幅']
            volume = etf['成交量']
            turnover = etf['成交额'] / 1e8  # Convert to 亿
            main_flow = etf['主力净流入'] / 1e4  # Convert to 万
            update_time = etf['更新时间']
            
            # Color coding for change_pct
            if change_pct > 0:
                change_str = f"+{change_pct:.2f}%"
            elif change_pct < 0:
                change_str = f"{change_pct:.2f}%"
            else:
                change_str = "0.00%"
            
            print(f"{code:<8} {name:<15} {price:>8.3f} {change_str:>8} {volume:>12,.0f} {turnover:>10.2f} {main_flow:>12.2f} {update_time:<20}")
    else:
        print("未获取到 ETF 数据")
    
    # 2. Get market indices
    print("\n【2】主要市场指数走势")
    print("-" * 80)
    index_data = get_index_data()
    
    if index_data:
        print(f"{'指数名称':<12} {'代码':<10} {'最新价':>12} {'涨跌额':>10} {'涨跌幅':>10}")
        print("-" * 80)
        
        for name, data in index_data.items():
            price = data.get('最新价', 0)
            change = data.get('涨跌额', 0)
            change_pct = data.get('涨跌幅', 0)
            
            if change_pct > 0:
                change_str = f"+{change_pct:.2f}%"
            elif change_pct < 0:
                change_str = f"{change_pct:.2f}%"
            else:
                change_str = "0.00%"
            
            print(f"{name:<12} {data.get('代码', ''):<10} {price:>12.2f} {change:>+10.2f} {change_str:>10}")
    else:
        print("未获取到指数数据")
    
    # 3. Get sector performance
    print("\n【3】行业板块今日表现 (Top 10)")
    print("-" * 80)
    sector_data = get_sector_performance()
    
    if sector_data:
        # Sort by change_pct
        sector_data.sort(key=lambda x: x.get('涨跌幅', 0), reverse=True)
        
        print(f"{'排名':<4} {'行业':<15} {'行业指数':>10} {'涨跌幅':>10} {'主力净流入 (亿)':>14} {'上涨/下跌':>10}")
        print("-" * 80)
        
        for i, sector in enumerate(sector_data[:10], 1):
            name = sector['行业'][:12]
            index_val = sector.get('行业指数', 0)
            change_pct = sector.get('涨跌幅', 0)
            main_flow = sector.get('主力净流入', 0) / 1e8  # Convert to 亿
            up = sector.get('上涨家数', 0)
            down = sector.get('下跌家数', 0)
            
            if change_pct > 0:
                change_str = f"+{change_pct:.2f}%"
            elif change_pct < 0:
                change_str = f"{change_pct:.2f}%"
            else:
                change_str = "0.00%"
            
            print(f"{i:<4} {name:<15} {index_val:>10.2f} {change_str:>10} {main_flow:>14.2f} {up}/{down:>8}")
    else:
        print("未获取到行业板块数据")
    
    # 4. Get market fund flow
    print("\n【4】市场整体资金流向")
    print("-" * 80)
    market_flow = get_market_fund_flow()
    
    if market_flow:
        print(f"日期：{market_flow.get('日期', 'N/A')}")
        print(f"主力净流入：{market_flow.get('主力净流入', 0) / 1e8:.2f} 亿 ({market_flow.get('主力净流入占比', 0):.2f}%)")
        print(f"超大单净流入：{market_flow.get('超大单净流入', 0) / 1e8:.2f} 亿")
        print(f"大单净流入：{market_flow.get('大单净流入', 0) / 1e8:.2f} 亿")
        print(f"中单净流入：{market_flow.get('中单净流入', 0) / 1e8:.2f} 亿")
        print(f"小单净流入：{market_flow.get('小单净流入', 0) / 1e8:.2f} 亿")
    else:
        print("未获取到市场资金流向数据")
    
    # 5. Detailed ETF data (JSON output for reference)
    print("\n【5】详细数据 (JSON 格式)")
    print("-" * 80)
    detailed_output = {
        "扫描时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "数据来源": "akshare (东方财富)",
        "ETF 数据": etf_data,
        "市场指数": index_data,
        "行业板块": sector_data,
        "市场资金流向": market_flow
    }
    print(json.dumps(detailed_output, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 80)
    print("数据扫描完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
