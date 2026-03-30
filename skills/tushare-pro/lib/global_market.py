#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 全球市场模块
整合美股/港股/全球指数数据
"""

from .base import get_tushare_data
from datetime import datetime, timedelta

def get_us_daily(us_codes, trade_date=None):
    """
    获取美股日线数据
    接口：us_daily (doc_254)
    """
    print(f"\n获取美股数据...")
    
    if trade_date is None:
        # 如果是周一，获取上周五数据
        today = datetime.now()
        if today.weekday() == 0:  # 周一
            trade_date = (today - timedelta(days=3)).strftime('%Y%m%d')
        else:
            trade_date = (today - timedelta(days=1)).strftime('%Y%m%d')
    
    if isinstance(us_codes, str):
        us_codes = [us_codes]
    
    result = {}
    for code in us_codes:
        data = get_tushare_data("us_daily", ts_code=code, start_date=trade_date, end_date=trade_date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            result[code] = {
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'vol': row.get("vol", 0),
                'trade_date': row.get("trade_date", "")
            }
            print(f"  ✅ {code}: {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
        else:
            print(f"  ⚠️ {code}: 无数据 (可能休市)")
    return result

def get_global_index(index_codes, trade_date=None):
    """
    获取全球指数数据
    接口：index_global (doc_211)
    """
    print(f"\n获取全球指数数据...")
    
    if trade_date is None:
        today = datetime.now()
        if today.weekday() == 0:
            trade_date = (today - timedelta(days=3)).strftime('%Y%m%d')
        else:
            trade_date = (today - timedelta(days=1)).strftime('%Y%m%d')
    
    if isinstance(index_codes, str):
        index_codes = [index_codes]
    
    result = {}
    for code in index_codes:
        data = get_tushare_data("index_global", ts_code=code, start_date=trade_date, end_date=trade_date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            result[code] = {
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'trade_date': row.get("trade_date", "")
            }
            print(f"  ✅ {code}: {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
    return result

def get_hk_daily(hk_codes, trade_date=None):
    """
    获取港股日线数据
    接口：hk_daily
    """
    print(f"\n获取港股数据...")
    
    if trade_date is None:
        today = datetime.now()
        if today.weekday() == 0:
            trade_date = (today - timedelta(days=3)).strftime('%Y%m%d')
        else:
            trade_date = (today - timedelta(days=1)).strftime('%Y%m%d')
    
    if isinstance(hk_codes, str):
        hk_codes = [hk_codes]
    
    result = {}
    for code in hk_codes:
        data = get_tushare_data("hk_daily", ts_code=code, start_date=trade_date, end_date=trade_date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            result[code] = {
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'vol': row.get("vol", 0)
            }
            print(f"  ✅ {code}: {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
    return result
