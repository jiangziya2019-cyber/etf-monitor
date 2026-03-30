#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 统一接口 - 向后兼容脚本
所有旧脚本可以继续使用这个入口
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/skills/tushare-pro')

from lib import *

# 向后兼容：保留旧的函数名
get_etf_realtime_daily = realtime.get_etf_realtime_daily
get_etf_realtime_minute = realtime.get_etf_realtime_minute
get_futures_realtime = realtime.get_futures_realtime
get_us_daily = global_market.get_us_daily
get_industry_moneyflow = moneyflow.get_industry_moneyflow
get_concept_moneyflow = moneyflow.get_concept_moneyflow

print("✅ Tushare Pro 统一接口已加载")
print("   所有数据获取现在使用 tushare-pro 技能")
