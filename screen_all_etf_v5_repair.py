#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 ETF 筛选 v5.0（修复版）
修复：动量/波动因子使用真实历史数据
"""

import sys, json, glob, time, os
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
from tushare_finance_data import get_fund_daily
from etf_name_map import get_etf_name

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5_修复版.json'

INDUSTRY_KEYWORDS = {
    '宽基': ['300', '500', '50', '180', '红利'],
    '科技': ['科技', '电子', '半导体', '芯片', '光伏', '新能源', '人工智能'],
    '金融': ['金融', '银行', '证券', '保险'],
    '周期': ['周期', '有色', '金属', '煤炭', '化工'],
}

def load_etf_codes():
    codes = []
    for f in glob.glob(os.path.join(CACHE_DIR, '*.json')):
        code = os.path.basename(f).replace('.json', '')
        if code.isdigit() and len(code) == 6:
            codes.append(code)
    return sorted(codes)

def load_historical_data(etf_codes):
    """加载历史数据用于动量/波动因子"""
    log_message(f"加载 {len(etf_codes)}只 ETF 历史数据...")
    historical_data = {}
    
    for i, code in enumerate(etf_codes):
        try:
            ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
            df = get_fund_daily(ts_code=ts_code, start_date='20250101', end_date='20260328')
            
            if df is not None and len(df) > 0:
                # Tushare 返回倒序数据（最新在前），需要反转
                historical_data[code] = {}
                for _, row in df.iloc[::-1].iterrows():
                    historical_data[code][str(row['trade_date'])] = {
                        'close': float(row['close']),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'vol': float(row['vol'])
                    }
            
            if (i+1) % 100 == 0:
                log_message(f"  已加载 {i+1}/{len(etf_codes)}只")
            
            time.sleep(0.1)
        except:
            pass
    
    log_message(f"✅ 加载完成：{len(historical_data)}只 ETF")
    return historical_data

def infer_industry(code):
    name = get_etf_name(code)
    for ind, kws in INDUSTRY_KEYWORDS.items():
        if any(k in code+name for k in kws):
            return ind
    return '其他'

def main():
    print("="*70)
    print("全市场 ETF 筛选 v5.0（修复版）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 加载 ETF 代码
    etf_codes = load_etf_codes()
    print(f"加载 {len(etf_codes)} 只 ETF")
    
    if not etf_codes:
        print("⚠️ 无数据，退出")
        return
    
    # 2. 加载历史数据（关键修复）
    print(f"\n{'='*70}")
    print("加载历史数据（动量/波动因子）...")
    print(f"{'='*70}")
    historical_data = load_historical_data(etf_codes)
    
    # 3. 计算因子
    print(f"\n{'='*70}")
    print("计算 7 大因子...")
    print(f"{'='*70}")
    
    # 使用历史数据中的最新日期（而非当前日期，避免周末/节假日无数据）
    all_dates = set()
    for data in historical_data.values():
        all_dates.update(data.keys())
    trade_date = max(all_dates) if all_dates else datetime.now().strftime('%Y%m%d')
    log_message(f"使用交易日期：{trade_date}")
    
    log_message("1. 估值因子...")
    valuation = calculate_valuation_factors(etf_codes, trade_date)
    
    log_message("2. 动量因子（真实历史数据）...")
    momentum = calculate_momentum_factors(historical_data, trade_date)
    
    log_message("3. 波动因子（真实历史数据）...")
    volatility = calculate_volatility_factors(historical_data, trade_date)
    
    log_message("4. 技术因子...")
    technical = calculate_technical_factors(etf_codes, trade_date)
    
    log_message("5. 资金因子...")
    fund_flow = calculate_fund_flow_factors(etf_codes)
    
    log_message("6. 流动性因子...")
    liquidity = calculate_liquidity_factors(etf_codes)
    
    log_message("7. ETF 特有因子...")
    etf_specific = calculate_etf_specific_factors(etf_codes)
    
    # 4. 综合评分
    log_message("\n计算综合评分...")
    industry_map = {code: infer_industry(code) for code in etf_codes}
    
    composite = calculate_composite_score(
        valuation, momentum, volatility, technical, fund_flow,
        liquidity_scores=liquidity,
        etf_specific_scores=etf_specific,
        industry_map=industry_map,
        market_regime='sideways'
    )
    
    # 5. 整理结果
    results = []
    for code in etf_codes:
        score = composite.get(code, {})
        if score.get('composite', 0) > 0:
            results.append({
                'code': code,
                'name': get_etf_name(code),
                'industry': industry_map.get(code, '其他'),
                'composite': score.get('composite', 0),
                'valuation': score.get('valuation', 0),
                'momentum': score.get('momentum', 0),
                'volatility': score.get('volatility', 0),
            })
    
    # 6. 排序
    results.sort(key=lambda x: -x['composite'])
    top_30 = results[:30]
    
    # 7. 统计分布
    scores = [r['composite'] for r in results]
    momentum_scores = [r['momentum'] for r in results if r['momentum'] > 0]
    volatility_scores = [r['volatility'] for r in results if r['volatility'] > 0]
    
    # 8. 输出结果
    print(f"\n{'='*70}")
    print(f"Top 30 ETF")
    print(f"{'='*70}")
    print(f"{'排名':<4} {'代码':<8} {'名称':<12} {'行业':<8} {'综合':<8} {'动量':<8} {'波动':<8}")
    print(f"{'='*70}")
    
    for i, etf in enumerate(top_30):
        print(f"{i+1:<4} {etf['code']:<8} {etf['name']:<12} {etf['industry']:<8} "
              f"{etf['composite']:.3f}    {etf['momentum']:.3f}    {etf['volatility']:.3f}")
    
    print(f"\n{'='*70}")
    print(f"分数分布统计")
    print(f"{'='*70}")
    print(f"综合评分：min={min(scores):.3f}, max={max(scores):.3f}, 分差={max(scores)-min(scores):.3f}")
    print(f"综合评分：均值={np.mean(scores):.3f}, 标准差={np.std(scores):.3f}")
    print(f"\n动量因子：min={min(momentum_scores):.3f}, max={max(momentum_scores):.3f}, 分差={max(momentum_scores)-min(momentum_scores):.3f}")
    print(f"动量因子：均值={np.mean(momentum_scores):.3f}, 标准差={np.std(momentum_scores):.3f}")
    print(f"\n波动因子：min={min(volatility_scores):.3f}, max={max(volatility_scores):.3f}, 分差={max(volatility_scores)-min(volatility_scores):.3f}")
    print(f"波动因子：均值={np.mean(volatility_scores):.3f}, 标准差={np.std(volatility_scores):.3f}")
    
    # 9. 保存结果
    output = {
        'screen_time': datetime.now().isoformat(),
        'total_etfs': len(results),
        'top_30': top_30,
        'all_scores': results,
        'stats': {
            'composite': {'min': min(scores), 'max': max(scores), 'range': max(scores)-min(scores), 'mean': np.mean(scores), 'std': np.std(scores)},
            'momentum': {'min': min(momentum_scores), 'max': max(momentum_scores), 'range': max(momentum_scores)-min(momentum_scores), 'mean': np.mean(momentum_scores), 'std': np.std(momentum_scores)},
            'volatility': {'min': min(volatility_scores), 'max': max(volatility_scores), 'range': max(volatility_scores)-min(volatility_scores), 'mean': np.mean(volatility_scores), 'std': np.std(volatility_scores)}
        }
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存：{OUTPUT_FILE}")
    print(f"\n{'='*70}")
    print("✅ 修复版筛选完成！")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
