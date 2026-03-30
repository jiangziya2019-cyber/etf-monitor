#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro ETF 专题模块
"""

from .base import get_tushare_data

def get_etf_basic():
    """获取 ETF 基础信息 (etf_basic, doc_385)"""
    print("获取 ETF 基础信息...")
    data = get_tushare_data("etf_basic")
    return data

def get_etf_share_size(trade_date=None):
    """获取 ETF 份额规模 (etf_share_size, doc_408)"""
    from datetime import datetime
    if trade_date is None:
        trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    print(f"获取 ETF 份额规模 ({trade_date})...")
    data = get_tushare_data("etf_share_size", trade_date=trade_date)
    return data
