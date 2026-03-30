#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 宏观经济模块
"""

from .base import get_tushare_data

def get_cpi():
    """获取 CPI 数据 (cn_cpi, doc_228)"""
    print("获取 CPI 数据...")
    return get_tushare_data("cn_cpi")

def get_pmi():
    """获取 PMI 数据 (cn_pmi, doc_325)"""
    print("获取 PMI 数据...")
    return get_tushare_data("cn_pmi")

def get_gdp():
    """获取 GDP 数据 (cn_gdp, doc_227)"""
    print("获取 GDP 数据...")
    return get_tushare_data("cn_gdp")

def get_news(start_date=None, end_date=None):
    """获取财经新闻 (news, doc_143)"""
    from datetime import datetime, timedelta
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"获取财经新闻...")
    return get_tushare_data("news", start_date=start_date, end_date=end_date)
