#!/usr/bin/env python3
"""
Fetch ETF data for portfolio analysis using akshare fund_etf_spot_em.
"""

import sys
import json
import akshare as ak
from datetime import datetime

# ETF lists
PORTFOLIO_ETFS = [
    "512010", "515790", "512480", "513110", "517520", 
    "510300", "510500", "518880", "159770", "159243", 
    "159399", "159241", "160723", "159227", "159819", 
    "159206", "159663", "159566", "159937"
]

NEW_ADDITIONS = [
    "510880",  # 红利 ETF
    "510300",  # 300ETF (already in portfolio)
    "510500",  # 500ETF (already in portfolio)
    "513500"   # 标普 500
]

# ETF names mapping
ETF_NAMES = {
    "512010": "医药 ETF",
    "515790": "光伏 ETF",
    "512480": "半导体 ETF",
    "513110": "纳指 ETF",
    "517520": "新能源车 ETF",
    "510300": "300ETF",
    "510500": "500ETF",
    "518880": "黄金 ETF",
    "159770": "芯片 ETF",
    "159243": "科创 50ETF",
    "159399": "现金流 ETF",
    "159241": "恒生科技 ETF",
    "160723": "原油 ETF",
    "159227": "碳中和 ETF",
    "159819": "人工智能 ETF",
    "159206": "消费电子 ETF",
    "159663": "科创芯片 ETF",
    "159566": "红利低波 ETF",
    "159937": "医药生物 ETF",
    "510880": "红利 ETF",
    "513500": "标普 500ETF"
}

def fetch_all_etf_data():
    """Fetch all ETF spot data at once"""
    try:
        df = ak.fund_etf_spot_em()
        return df
    except Exception as e:
        print(f"Error fetching ETF data: {e}", file=sys.stderr)
        return None

def main():
    print(f"=== ETF 持仓数据刷新 ===")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch all ETF data
    print("正在获取 ETF 实时行情数据...")
    df = fetch_all_etf_data()
    
    if df is None:
        print("获取数据失败!")
        sys.exit(1)
    
    print(f"成功获取 {len(df)} 只 ETF 数据")
    print()
    
    # Check available columns
    # print("Available columns:", df.columns.tolist())
    
    # Create a dictionary for quick lookup
    etf_dict = {}
    for idx, row in df.iterrows():
        code = str(row.get('代码', ''))
        etf_dict[code] = row
    
    # Output portfolio ETFs
    print("="*100)
    print("=== 持仓 19 只 ETF 实时数据 ===")
    print("="*100)
    print(f"{'代码':<8} {'名称':<14} {'最新价':>10} {'涨跌额':>10} {'涨跌%':>10} {'成交量 (手)':>14} {'成交额 (万)':>14}")
    print("-"*100)
    
    results = {}
    for code in PORTFOLIO_ETFS:
        name = ETF_NAMES.get(code, "未知")
        if code in etf_dict:
            row = etf_dict[code]
            price = row.get('最新价', None)
            change = row.get('涨跌额', None)
            change_pct = row.get('涨跌幅', None)
            volume = row.get('成交量', None)
            amount = row.get('成交额', None)
            
            results[code] = {
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": volume,
                "amount": amount
            }
            
            price_str = f"{price:.3f}" if price is not None else "-"
            change_str = f"{change:.3f}" if change is not None else "-"
            change_pct_str = f"{change_pct:.2f}%" if change_pct is not None else "-"
            volume_str = f"{volume:,.0f}" if volume is not None else "-"
            amount_str = f"{amount:,.0f}" if amount is not None else "-"
            
            print(f"{code:<8} {name:<14} {price_str:>10} {change_str:>10} {change_pct_str:>10} {volume_str:>14} {amount_str:>14}")
        else:
            results[code] = {"name": name, "error": "not found"}
            print(f"{code:<8} {name:<14} {'未找到':>10} {'-':>10} {'-':>10} {'-':>14} {'-':>14}")
    
    print()
    print("="*100)
    print("=== 今日新建仓/加仓品种 ===")
    print("="*100)
    print(f"{'代码':<8} {'名称':<14} {'最新价':>10} {'涨跌额':>10} {'涨跌%':>10} {'成交量 (手)':>14} {'成交额 (万)':>14}")
    print("-"*100)
    
    for code in NEW_ADDITIONS:
        name = ETF_NAMES.get(code, "未知")
        if code in etf_dict:
            row = etf_dict[code]
            price = row.get('最新价', None)
            change = row.get('涨跌额', None)
            change_pct = row.get('涨跌幅', None)
            volume = row.get('成交量', None)
            amount = row.get('成交额', None)
            
            results[code] = {
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": volume,
                "amount": amount
            }
            
            price_str = f"{price:.3f}" if price is not None else "-"
            change_str = f"{change:.3f}" if change is not None else "-"
            change_pct_str = f"{change_pct:.2f}%" if change_pct is not None else "-"
            volume_str = f"{volume:,.0f}" if volume is not None else "-"
            amount_str = f"{amount:,.0f}" if amount is not None else "-"
            
            print(f"{code:<8} {name:<14} {price_str:>10} {change_str:>10} {change_pct_str:>10} {volume_str:>14} {amount_str:>14}")
        else:
            results[code] = {"name": name, "error": "not found"}
            print(f"{code:<8} {name:<14} {'未找到':>10} {'-':>10} {'-':>10} {'-':>14} {'-':>14}")
    
    # Save raw data
    with open("/home/admin/openclaw/workspace/etf_raw_data.json", "w") as f:
        # Convert to serializable format
        serializable_results = {}
        for code, data in results.items():
            serializable_results[code] = {}
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    serializable_results[code][k] = v
                else:
                    serializable_results[code][k] = str(v) if v is not None else None
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n原始数据已保存到：/home/admin/openclaw/workspace/etf_raw_data.json")

if __name__ == "__main__":
    main()
