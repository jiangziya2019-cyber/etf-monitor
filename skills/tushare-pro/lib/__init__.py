#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 统一技能 - 核心模块
整合所有 Tushare 数据接口
"""

from .base import get_tushare_data, TUSHARE_TOKEN, TUSHARE_URL
from .realtime import (
    get_etf_realtime_daily,
    get_etf_realtime_minute,
    get_index_realtime_daily,
    get_futures_realtime
)
from .etf import get_etf_basic, get_etf_share_size
from .index import get_index_techfactor, get_index_valuation
from .global_market import get_us_daily, get_global_index, get_hk_daily
from .moneyflow import get_industry_moneyflow, get_concept_moneyflow
from .macro import get_cpi, get_pmi, get_gdp, get_news

__version__ = '1.0'
__all__ = [
    'get_tushare_data',
    'get_etf_realtime_daily',
    'get_etf_realtime_minute',
    'get_index_realtime_daily',
    'get_futures_realtime',
    'get_etf_basic',
    'get_etf_share_size',
    'get_index_techfactor',
    'get_index_valuation',
    'get_us_daily',
    'get_global_index',
    'get_hk_daily',
    'get_industry_moneyflow',
    'get_concept_moneyflow',
    'get_cpi',
    'get_pmi',
    'get_gdp',
    'get_news'
]
