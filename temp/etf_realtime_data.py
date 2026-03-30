#!/usr/bin/env python3
"""
Fetch real-time ETF data for specified codes.
Data includes: latest price, change percentage, volume.
"""

import akshare as ak
import pandas as pd
from datetime import datetime

# ETF codes to query
liquidate_etfs = ['159770', '512660', '512690', '512880', '588000', '159930', '517520', '518880']
buy_etfs = ['510880', '510300', '510500', '513500']

all_etfs = liquidate_etfs + buy_etfs

def get_etf_data(code):
    """Fetch real-time data for a single ETF."""
    try:
        # Get real-time data for ETF
        # Using fund_etf_spot_em for real-time ETF data
        df = ak.fund_etf_spot_em()
        
        # Filter for the specific ETF code
        etf_data = df[df['代码'] == code]
        
        if etf_data.empty:
            return None
        
        row = etf_data.iloc[0]
        return {
            'code': code,
            'name': row.get('名称', 'N/A'),
            'price': row.get('最新价', 0),
            'change_pct': row.get('涨跌幅', 0),
            'volume': row.get('成交量', 0),
            'turnover': row.get('成交额', 0),
            'type': 'liquidate' if code in liquidate_etfs else 'buy'
        }
    except Exception as e:
        print(f"Error fetching {code}: {e}")
        return {
            'code': code,
            'name': 'Error',
            'price': 'N/A',
            'change_pct': 'N/A',
            'volume': 'N/A',
            'turnover': 'N/A',
            'type': 'liquidate' if code in liquidate_etfs else 'buy'
        }

def main():
    print(f"Fetching ETF data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Fetch all ETF data
    results = []
    for code in all_etfs:
        print(f"Fetching {code}...")
        data = get_etf_data(code)
        if data:
            results.append(data)
    
    # Display results
    print("\n" + "=" * 100)
    print(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Liquidate ETFs
    print("\n【清仓清单】")
    print("-" * 100)
    print(f"{'代码':<10} {'名称':<15} {'最新价':<12} {'涨跌幅':<12} {'成交量':<20} {'成交额':<20}")
    print("-" * 100)
    
    for item in results:
        if item['type'] == 'liquidate':
            print(f"{item['code']:<10} {item['name']:<15} {item['price']:<12} {item['change_pct']:<12} {item['volume']:<20} {item['turnover']:<20}")
    
    # Buy ETFs
    print("\n【新建仓/加仓清单】")
    print("-" * 100)
    print(f"{'代码':<10} {'名称':<15} {'最新价':<12} {'涨跌幅':<12} {'成交量':<20} {'成交额':<20}")
    print("-" * 100)
    
    for item in results:
        if item['type'] == 'buy':
            print(f"{item['code']:<10} {item['name']:<15} {item['price']:<12} {item['change_pct']:<12} {item['volume']:<20} {item['turnover']:<20}")
    
    print("\n" + "=" * 100)
    print("注：数据可能有 15 分钟延迟，仅供参考，不构成投资建议。")
    print("=" * 100)

if __name__ == "__main__":
    main()
