#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 指数专题模块
"""

from .base import get_tushare_data

def get_index_techfactor(ts_code, start_date=None, end_date=None):
    """获取指数技术指标 (idx_techfactor, doc_358)"""
    print(f"获取指数技术指标 ({ts_code})...")
    data = get_tushare_data("idx_techfactor", ts_code=ts_code, start_date=start_date, end_date=end_date)
    return data

def get_index_valuation(index_codes):
    """获取指数估值数据 (index_dailybasic)"""
    print(f"获取指数估值...")
    if isinstance(index_codes, str):
        index_codes = [index_codes]
    result = {}
    for code in index_codes:
        data = get_tushare_data("index_dailybasic", ts_code=code)
        if data:
            result[code] = data
    return result
