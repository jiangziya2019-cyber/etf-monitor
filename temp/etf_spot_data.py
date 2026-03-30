#!/usr/bin/env python3
"""
Fetch real-time ETF spot data for specified codes.
"""

import akshare as ak
import pandas as pd
from datetime import datetime

# ETF codes to query
liquidate_etfs = ['159770', '512660', '512690', '512880', '588000', '159930', '517520', '518880']
buy_etfs = ['510880', '510300', '510500', '513500']

all_etfs = liquidate_etfs + buy_etfs

def main():
    print(f"Fetching ETF data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Get all ETF spot data at once
    try:
        df = ak.fund_etf_spot_em()
        print(f"Total ETFs in market: {len(df)}")
        
        # Filter for our ETFs
        results = []
        for code in all_etfs:
            etf_data = df[df['代码'] == code]
            if not etf_data.empty:
                row = etf_data.iloc[0]
                results.append({
                    'code': code,
                    'name': row.get('名称', 'N/A'),
                    'price': row.get('最新价', 0),
                    'change_pct': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'turnover': row.get('成交额', 0),
                    'type': 'liquidate' if code in liquidate_etfs else 'buy'
                })
            else:
                results.append({
                    'code': code,
                    'name': 'Not Found',
                    'price': 'N/A',
                    'change_pct': 'N/A',
                    'volume': 'N/A',
                    'turnover': 'N/A',
                    'type': 'liquidate' if code in liquidate_etfs else 'buy'
                })
        
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
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
