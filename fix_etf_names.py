#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 ETF 名称 - 从 Tushare 获取真实名称（分批处理，避免速率限制）
"""

import json
import time
from tushare_finance_data import get_etf_basic, get_pro

# 读取筛选结果
with open('/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5_修复版.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"加载 {len(data.get('all_scores', []))} 只 ETF")

# 获取 ETF 基础信息（分批，每批 50 只）
print("\n从 Tushare 获取 ETF 名称（分批处理）...")
etf_codes = [etf['code'] for etf in data['all_scores']]
etf_info = {}

# 分批获取，每批 50 只，间隔 1.5 秒
batch_size = 50
for i in range(0, len(etf_codes), batch_size):
    batch = etf_codes[i:i+batch_size]
    try:
        batch_info = get_etf_basic(batch)
        if batch_info:
            etf_info.update(batch_info)
            print(f"  已获取 {i+len(batch_info)}/{len(etf_codes)} 只")
        time.sleep(1.5)  # 避免速率限制
    except Exception as e:
        print(f"  批次 {i//batch_size+1} 失败：{e}")
        time.sleep(2)

print(f"\n获取到 {len(etf_info)} 条 ETF 信息")

# 更新名称
updated = 0
for etf in data['all_scores']:
    code = etf['code']
    if code in etf_info:
        old_name = etf['name']
        new_name = etf_info[code].get('csname', '未知')
        if new_name and new_name != '未知':
            etf['name'] = new_name
            updated += 1

# 更新 Top 30
data['top_30'] = data['all_scores'][:30]

# 保存结果
with open('/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5_修复版_含名称.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 更新了 {updated} 只 ETF 的名称")
print(f"\nTop 10 ETF（修复后）:")
for i, etf in enumerate(data['top_30'][:10]):
    print(f"  {i+1}. {etf['code']} {etf['name']} ({etf['composite']:.3f})")
