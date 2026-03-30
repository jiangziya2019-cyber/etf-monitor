#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版上午市场分析模块 v3.0
使用统一的 tushare-pro 技能
创建：2026-03-30
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/skills/tushare-pro')

from lib.realtime import get_etf_realtime_daily, get_futures_realtime
from lib.global_market import get_us_daily
from lib.moneyflow import get_industry_moneyflow, get_concept_moneyflow
from datetime import datetime

print("=" * 80)
print("增强版上午市场分析 v3.0 (使用 tushare-pro 统一技能)")
print("=" * 80)

# 获取数据
us_data = get_us_daily(['DJI', 'SPX', 'IXIC'])
futures_data = get_futures_realtime(['AU2026.SHF', 'SC2026.INE'])
industry_data = get_industry_moneyflow()
concept_data = get_concept_moneyflow()

print("\n✅ 数据获取完成！")
print(f"   美股：{len(us_data)} 个")
print(f"   期货：{len(futures_data)} 个")
print(f"   行业：{len(industry_data)} 个")
print(f"   概念：{len(concept_data)} 个")
