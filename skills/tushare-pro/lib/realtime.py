#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 实时行情模块
整合 ETF/指数/期货实时数据
"""

from .base import get_tushare_data
from datetime import datetime, timedelta

def get_etf_realtime_daily(etf_codes):
    """
    获取 ETF 实时日线
    接口：rt_etf_k (doc_400)
    """
    print(f"\n获取 ETF 实时日线...")
    
    if isinstance(etf_codes, str):
        etf_codes = [etf_codes]
    
    ts_code_str = ','.join(etf_codes)
    data = get_tushare_data("rt_etf_k", ts_code=ts_code_str)
    
    if data and "items" in data:
        fields = data.get("fields", [])
        result = {}
        for item in data["items"]:
            row = dict(zip(fields, item))
            code = row.get("ts_code", "")
            result[code] = {
                'name': row.get("name", ""),
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'vol': row.get("vol", 0),
                'amount': row.get("amount", 0),
                'trade_time': row.get("trade_time", "")
            }
            print(f"  ✅ {code}: ¥{row.get('close', 0):.3f} ({row.get('pct_change', 0):+.2f}%)")
        return result
    return {}

def get_etf_realtime_minute(etf_codes, freq='5MIN'):
    """
    获取 ETF 实时分钟线
    接口：rt_min (doc_416)
    freq: 1MIN/5MIN/15MIN/30MIN/60MIN
    """
    print(f"\n获取 ETF 实时分钟线 ({freq})...")
    
    if isinstance(etf_codes, str):
        etf_codes = [etf_codes]
    
    result = {}
    for code in etf_codes:
        data = get_tushare_data("rt_min", ts_code=code, freq=freq)
        if data and "items" in data:
            fields = data.get("fields", [])
            latest = dict(zip(fields, data["items"][-1]))
            result[code] = {
                'close': latest.get("close", 0),
                'pct_change': latest.get("pct_change", 0),
                'vol': latest.get("vol", 0),
                'trade_time': latest.get("trade_time", "")
            }
            print(f"  ✅ {code}: {latest.get('close', 0):.3f} ({latest.get('pct_change', 0):+.2f}%)")
    return result

def get_index_realtime_daily(index_codes):
    """
    获取指数实时日线
    接口：rt_idx_k (doc_403)
    """
    print(f"\n获取指数实时日线...")
    
    if isinstance(index_codes, str):
        index_codes = [index_codes]
    
    ts_code_str = ','.join(index_codes)
    data = get_tushare_data("rt_idx_k", ts_code=ts_code_str)
    
    if data and "items" in data:
        fields = data.get("fields", [])
        result = {}
        for item in data["items"]:
            row = dict(zip(fields, item))
            code = row.get("ts_code", "")
            result[code] = {
                'name': row.get("name", ""),
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'vol': row.get("vol", 0),
                'trade_time': row.get("trade_time", "")
            }
            print(f"  ✅ {row.get('name', '')}: {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
        return result
    return {}

def get_futures_realtime(fut_codes, freq='5MIN'):
    """
    获取期货实时分钟线
    接口：rt_fut_min (doc_340)
    """
    print(f"\n获取期货实时数据 ({freq})...")
    
    if isinstance(fut_codes, str):
        fut_codes = [fut_codes]
    
    result = {}
    for code in fut_codes:
        data = get_tushare_data("rt_fut_min", ts_code=code, freq=freq)
        if data and "items" in data:
            fields = data.get("fields", [])
            latest = dict(zip(fields, data["items"][-1]))
            
            open_price = latest.get("open", 0)
            current = latest.get("close", 0)
            change = (current - open_price) / open_price * 100 if open_price > 0 else 0
            
            result[code] = {
                'name': code,
                'current': current,
                'change': change,
                'vol': latest.get("vol", 0),
                'oi': latest.get("oi", 0),
                'trade_time': latest.get("time", "")
            }
            signal = "📈" if change > 0.5 else ("📉" if change < -0.5 else "➖")
            print(f"  {signal} {code}: {current:.2f} ({change:+.2f}%)")
    return result
