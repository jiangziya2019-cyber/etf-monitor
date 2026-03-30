#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 ETF 完整 7 大因子筛选 v5.0（分批版）
版本：v5.0 | 创建：2026-03-28 16:50

分批处理避免 Tushare 速率限制（每批 50 只，间隔 60 秒）
"""

import sys, json, os, glob, time
from datetime import datetime
from typing import Dict, List
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')
from multi_factor_v5 import (
    calculate_valuation_factors,
    calculate_momentum_factors,
    calculate_volatility_factors,
    calculate_technical_factors,
    calculate_fund_flow_factors,
    calculate_liquidity_factors,
    calculate_etf_specific_factors,
    calculate_composite_score,
    select_top_etfs,
    log_message
)

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 完整筛选结果_v5.json'
REPORT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 完整筛选报告_v5.md'
BATCH_SIZE = 30
BATCH_INTERVAL = 60
TOP_N = 30

INDUSTRY_KEYWORDS = {
    '宽基': ['300', '500', '50', '180', '红利', '央企', '大盘', '中小', '创业', '科创'],
    '科技': ['科技', '电子', '半导体', '芯片', '计算机', '通信', '5G', '人工智能', '光伏', '新能源', '电池'],
    '金融': ['金融', '银行', '证券', '保险', '券商'],
    '制造': ['制造', '机械', '装备', '机器人', '机床', '储能'],
    '医药': ['医药', '医疗', '生物', '创新药', '中药', '健康'],
    '周期': ['周期', '有色', '金属', '煤炭', '钢铁', '化工', '建材'],
    '消费': ['消费', '食品', '饮料', '家电', '汽车', '旅游', '农业'],
    '全球': ['纳指', '标普', '恒生', '港股', '美国', '全球', '国际', '日经'],
}

ETF_NAMES = {
    '510300': '沪深 300ETF', '510500': '中证 500ETF', '510880': '红利 ETF',
    '515790': '光伏 ETF', '512480': '半导体 ETF', '512880': '证券 ETF',
    '512400': '有色 ETF', '512800': '银行 ETF', '512980': '传媒 ETF',
    '159819': '人工智能 AI', '515260': '电子 ETF', '510180': '180ETF',
    '159949': '创业板 50', '513110': '纳指 ETF', '513500': '标普 500',
    '512010': '医药 ETF', '512690': '酒 ETF', '515220': '煤炭 ETF',
    '515880': '通信 ETF', '513980': '消费 ETF',
}

def load_etf_codes():
    print(f"从 {CACHE_DIR} 加载 ETF 代码...")
    codes = []
    json_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    for filepath in json_files:
        code = os.path.basename(filepath).replace('.json', '')
        if code.isdigit() and len(code) == 6:
            codes.append(code)
    print(f"✅ 加载 {len(codes)} 只 ETF")
    return sorted(codes)

def infer_industry(code):
    name = ETF_NAMES.get(code, '')
    text = code + name
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return industry
    return '其他'

def process_batch(batch_codes, batch_idx, total_batches):
    log_message(f"\n{'='*70}")
    log_message(f"处理批次 {batch_idx+1}/{total_batches} ({len(batch_codes)}只 ETF)")
    log_message(f"{'='*70}")
    
    trade_date = datetime.now().strftime('%Y%m%d')
    
    log_message("  1. 估值因子（真实 PE/PB/股息率）...")
    try:
        valuation = calculate_valuation_factors(batch_codes, trade_date)
        log_message(f"    ✅ 完成 {len(valuation)}只")
    except Exception as e:
        log_message(f"    ⚠️ 失败：{e}")
        valuation = {}
    
    log_message("  2. 动量因子（真实历史数据）...")
    try:
        momentum = calculate_momentum_factors(historical_data, trade_date)
        momentum = {k: v for k, v in momentum.items() if k in batch_codes}
        log_message(f"    ✅ 完成 {len(momentum)}只")
    except Exception as e:
        log_message(f"    ⚠️ 失败：{e}")
        momentum = {}
    
    log_message("  3. 波动因子（真实历史数据）...")
    try:
        volatility = calculate_volatility_factors(historical_data, trade_date)
        volatility = {k: v for k, v in volatility.items() if k in batch_codes}
        log_message(f"    ✅ 完成 {len(volatility)}只")
    except Exception as e:
        log_message(f"    ⚠️ 失败：{e}")
        volatility = {}
    
    log_message("  4. 技术因子（真实 RSI/MACD/KDJ）...")
    try:
        technical = calculate_technical_factors(batch_codes, trade_date)
        log_message(f"    ✅ 完成 {len(technical)}只")
    except Exception as e:
        log_message(f"    ⚠️ 失败：{e}")
        technical = {}
    
    log_message("  5. 资金因子（真实份额变化）...")
    try:
        fund_flow = calculate_fund_flow_factors(batch_codes)
        log_message(f"    ✅ 完成 {len(fund_flow)}只")
    except Exception as e:
        log_message(f"    ⚠️ 失败：{e}")
        fund_flow = {}
    
    log_message("  6. 流动性因子...")
    liquidity = calculate_liquidity_factors(batch_codes)
    log_message(f"    ✅ 完成 {len(liquidity)}只")
    
    log_message("  7. ETF 特有因子...")
    etf_specific = calculate_etf_specific_factors(batch_codes)
    log_message(f"    ✅ 完成 {len(etf_specific)}只")
    
    log_message("  8. 计算综合评分...")
    industry_map = {code: infer_industry(code) for code in batch_codes}
    
    composite = calculate_composite_score(
        valuation, momentum, volatility, technical, fund_flow,
        liquidity_scores=liquidity,
        etf_specific_scores=etf_specific,
        industry_map=industry_map,
        market_regime='sideways'
    )
    
    batch_results = {}
    for code in batch_codes:
        score = composite.get(code, {})
        batch_results[code] = {
            'code': code,
            'name': ETF_NAMES.get(code, '未知'),
            'industry': industry_map.get(code, '其他'),
            'composite': score.get('composite', 0),
            'valuation': score.get('valuation', 0),
            'momentum': score.get('momentum', 0),
            'volatility': score.get('volatility', 0),
            'technical': score.get('technical', 0),
            'fund_flow': score.get('fund_flow', 0),
            'liquidity': score.get('liquidity', 0),
            'etf_specific': score.get('etf_specific', 0)
        }
    
    return batch_results

def generate_report(all_results, top_etfs):
    print(f"\n生成报告...")
    
    industry_count = {}
    for etf in top_etfs:
        ind = etf['industry']
        industry_count[ind] = industry_count.get(ind, 0) + 1
    
    report = f"""# 📊 全市场 ETF 完整筛选报告 v5.0（7 大因子）

**筛选时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**策略版本**: v5.0（改进版）  
**数据源**: Tushare Pro（真实估值 + 技术因子）

---

## 一、筛选概况

- **ETF 总数**: {len(all_results)} 只
- **筛选因子**: 7 大类（估值/动量/波动/资金/技术/流动性/ETF 特有）
- **Top N**: {len(top_etfs)}

---

## 二、Top {len(top_etfs)} ETF 名单

| 排名 | 代码 | 名称 | 行业 | 综合分 | 估值 | 动量 | 流动性 |
|------|------|------|------|--------|------|------|--------|
"""
    
    for i, etf in enumerate(top_etfs):
        report += f"| {i+1} | {etf['code']} | {etf['name']} | {etf['industry']} | {etf['composite']:.3f} | {etf['valuation']:.3f} | {etf['momentum']:.3f} | {etf['liquidity']:.3f} |\n"
    
    report += f"""
---

## 三、行业分布

| 行业 | 数量 | 占比 |
|------|------|------|
"""
    
    for ind, count in sorted(industry_count.items(), key=lambda x: -x[1]):
        pct = count / len(top_etfs) * 100
        report += f"| {ind} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 四、分层推荐

### 第一层：防守型
"""
    defensive = sorted([e for e in top_etfs if e['industry'] in ['宽基', '金融', '红利']], key=lambda x: -x['composite'])[:5]
    for etf in defensive:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    if not defensive:
        report += "- 暂无\n"
    
    report += f"""
### 第二层：成长型
"""
    growth = sorted([e for e in top_etfs if e['industry'] in ['科技', '制造', '医药']], key=lambda x: -x['composite'])[:5]
    for etf in growth:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    if not growth:
        report += "- 暂无\n"
    
    report += f"""
### 第三层：交易型
"""
    trading = sorted([e for e in top_etfs if e['industry'] in ['周期', '消费', '其他']], key=lambda x: -x['liquidity'])[:5]
    for etf in trading:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    if not trading:
        report += "- 暂无\n"
    
    report += f"""
---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{REPORT_FILE}")

def main():
    print("="*70)
    print("全市场 ETF 完整 7 大因子筛选 v5.0（分批版）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    etf_codes = load_etf_codes()
    if not etf_codes:
        print("⚠️ 无 ETF 数据，退出")
        return
    
    total_batches = (len(etf_codes) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n总 ETF 数：{len(etf_codes)}只")
    print(f"分批：{total_batches}批，每批{BATCH_SIZE}只，间隔{BATCH_INTERVAL}秒")
    print(f"预计耗时：{(total_batches-1)*BATCH_INTERVAL/60:.1f}分钟")
    
    all_results = {}
    
    for i in range(total_batches):
        start_idx = i * BATCH_SIZE
        end_idx = min((i + 1) * BATCH_SIZE, len(etf_codes))
        batch_codes = etf_codes[start_idx:end_idx]
        
        batch_results = process_batch(batch_codes, i, total_batches)
        all_results.update(batch_results)
        
        if i < total_batches - 1:
            print(f"\n⏳ 等待{BATCH_INTERVAL}秒（避免 Tushare 速率限制）...")
            time.sleep(BATCH_INTERVAL)
    
    print(f"\n{'='*70}")
    print("选择 Top ETF...")
    print(f"{'='*70}")
    
    sorted_etfs = sorted(all_results.values(), key=lambda x: -x['composite'])
    top_etfs = sorted_etfs[:TOP_N]
    
    print(f"\n{'='*70}")
    print(f"Top {TOP_N} ETF")
    print(f"{'='*70}")
    print(f"{'排名':<4} {'代码':<8} {'名称':<12} {'行业':<8} {'综合':<8} {'估值':<8} {'动量':<8}")
    print(f"{'='*70}")
    
    for i, etf in enumerate(top_etfs):
        print(f"{i+1:<4} {etf['code']:<8} {etf['name']:<12} {etf['industry']:<8} {etf['composite']:.3f}    {etf['valuation']:.3f}    {etf['momentum']:.3f}")
    
    results = {
        'screen_time': datetime.now().isoformat(),
        'total_etfs': len(all_results),
        'top_n': TOP_N,
        'top_etfs': top_etfs,
        'all_scores': all_results
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存：{OUTPUT_FILE}")
    generate_report(all_results, top_etfs)
    
    print("\n" + "="*70)
    print("✅ 全市场完整筛选完成！")
    print("="*70)

if __name__ == "__main__":
    main()
