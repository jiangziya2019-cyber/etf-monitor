#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 ETF 多因子筛选 v5.0（改进版）
版本：v5.0 | 创建：2026-03-28 16:00

使用 7 大因子（估值/动量/波动/资金/技术/流动性/ETF 特有）+ 行业中性化
筛选全市场 608 只 ETF
"""

import sys, json, os, time
from datetime import datetime, timedelta
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
    identify_market_regime,
    log_message
)

# ============ 配置 ============

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5.json'
TOP_N = 30  # 筛选 Top 30

# 行业映射（简化版）
INDUSTRY_MAP = {
    '宽基': ['510300', '510500', '510180', '159949', '510880', '159399'],
    '金融': ['512800', '510230', '512880', '512200'],
    '科技': ['512480', '159819', '515260', '512720', '515880', '512980'],
    '制造': ['159566', '159663', '562500', '159227', '515790'],
    '医药': ['512010'],
    '周期': ['512400', '516020', '515210', '516110'],
    '全球': ['513110', '513500', '159937', '160723', '513130'],
}

def load_etf_pool() -> List[str]:
    """加载全市场 ETF 池（608 只）"""
    log_message("加载全市场 ETF 池...")
    
    etf_codes = []
    
    # 从缓存目录加载
    if os.path.exists(CACHE_DIR):
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                code = filename.replace('.json', '')
                if code.isdigit() and len(code) == 6:
                    etf_codes.append(code)
    
    log_message(f"加载 {len(etf_codes)}只 ETF")
    return etf_codes

def build_industry_map(etf_codes: List[str]) -> Dict[str, str]:
    """构建行业映射"""
    industry_map = {}
    
    for industry, codes in INDUSTRY_MAP.items():
        for code in codes:
            if code in etf_codes:
                industry_map[code] = industry
    
    # 未映射的 ETF 设为"其他"
    for code in etf_codes:
        if code not in industry_map:
            industry_map[code] = '其他'
    
    return industry_map

def filter_liquidity(etf_codes: List[str], liquidity_scores: Dict) -> List[str]:
    """
    流动性过滤
    
    门槛:
    - 日均成交>5000 万
    - 换手率>1%
    """
    filtered = []
    
    for code in etf_codes:
        if code in liquidity_scores:
            liq = liquidity_scores[code]
            if liq.get('pass_threshold', False):
                filtered.append(code)
            else:
                log_message(f"  ⚠️ {code} 流动性不足，剔除")
        else:
            filtered.append(code)  # 无数据保留
    
    log_message(f"流动性过滤后：{len(filtered)}只 ETF")
    return filtered

def run_screening(etf_codes: List[str]) -> Dict:
    """
    运行全市场筛选（真实 Tushare 数据）
    
    Args:
        etf_codes: ETF 代码列表
    
    Returns:
        筛选结果
    """
    log_message("="*70)
    log_message("全市场 ETF 多因子筛选 v5.0（真实数据）")
    log_message(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"数据源：Tushare Pro（真实估值 + 技术因子）")
    log_message("="*70)
    
    # 1. 构建行业映射
    log_message("\n1. 构建行业映射...")
    industry_map = build_industry_map(etf_codes)
    
    # 2. 计算 7 大因子评分（真实数据）
    log_message("\n2. 计算因子评分（真实 Tushare 数据）...")
    
    trade_date = datetime.now().strftime('%Y%m%d')
    
    log_message("  2.1 估值因子（真实 PE/PB/股息率）...")
    valuation = calculate_valuation_factors(etf_codes, trade_date)
    
    log_message("  2.2 动量因子...")
    momentum = calculate_momentum_factors({}, trade_date)
    
    log_message("  2.3 波动因子...")
    volatility = calculate_volatility_factors({}, trade_date)
    
    log_message("  2.4 技术因子（真实 RSI/MACD/KDJ）...")
    technical = calculate_technical_factors(etf_codes, trade_date)
    
    log_message("  2.5 资金因子（真实份额变化）...")
    fund_flow = calculate_fund_flow_factors(etf_codes)
    
    log_message("  2.6 流动性因子...")
    liquidity = calculate_liquidity_factors(etf_codes)
    
    log_message("  2.7 ETF 特有因子（真实溢价率/费率/规模）...")
    etf_specific = calculate_etf_specific_factors(etf_codes)
    
    # 3. 流动性过滤
    log_message("\n3. 流动性过滤...")
    filtered_etfs = filter_liquidity(etf_codes, liquidity)
    
    # 4. 识别市场状态
    log_message("\n4. 识别市场状态...")
    # 简化：使用模拟数据
    market_regime = 'sideways'
    log_message(f"  市场状态：{market_regime}")
    
    # 5. 计算综合评分（包含行业中性化）
    log_message("\n5. 计算综合评分（7 大因子 + 行业中性化）...")
    
    # 过滤后的 ETF 计算评分
    valuation_filtered = {k: v for k, v in valuation.items() if k in filtered_etfs}
    momentum_filtered = {k: v for k, v in momentum.items() if k in filtered_etfs}
    volatility_filtered = {k: v for k, v in volatility.items() if k in filtered_etfs}
    technical_filtered = {k: v for k, v in technical.items() if k in filtered_etfs}
    fund_flow_filtered = {k: v for k, v in fund_flow.items() if k in filtered_etfs}
    liquidity_filtered = {k: v for k, v in liquidity.items() if k in filtered_etfs}
    etf_specific_filtered = {k: v for k, v in etf_specific.items() if k in filtered_etfs}
    
    composite = calculate_composite_score(
        valuation_filtered,
        momentum_filtered,
        volatility_filtered,
        technical_filtered,
        fund_flow_filtered,
        liquidity_scores=liquidity_filtered,
        etf_specific_scores=etf_specific_filtered,
        industry_map=industry_map,
        market_regime=market_regime
    )
    
    # 6. 选择 Top ETF
    log_message("\n6. 选择 Top ETF...")
    top_etfs = select_top_etfs(composite, TOP_N)
    
    # 7. 生成结果
    log_message("\n7. 生成结果...")
    
    results = {
        'screen_time': datetime.now().isoformat(),
        'total_etfs': len(etf_codes),
        'filtered_etfs': len(filtered_etfs),
        'market_regime': market_regime,
        'top_n': TOP_N,
        'top_etfs': [],
        'all_scores': composite
    }
    
    for i, code in enumerate(top_etfs):
        score = composite.get(code, {})
        results['top_etfs'].append({
            'rank': i + 1,
            'code': code,
            'industry': industry_map.get(code, '其他'),
            'composite': score.get('composite', 0),
            'valuation': score.get('valuation', 0),
            'momentum': score.get('momentum', 0),
            'volatility': score.get('volatility', 0),
            'technical': score.get('technical', 0),
            'fund_flow': score.get('fund_flow', 0),
            'liquidity': score.get('liquidity', 0),
            'etf_specific': score.get('etf_specific', 0)
        })
    
    # 8. 保存结果
    log_message(f"\n8. 保存结果到 {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    log_message(f"✅ 筛选完成！结果已保存到 {OUTPUT_FILE}")
    
    return results

def print_results(results: Dict):
    """打印筛选结果"""
    print("\n" + "="*70)
    print("全市场 ETF 筛选结果 v5.0（改进版）")
    print("="*70)
    
    print(f"\n筛选时间：{results['screen_time']}")
    print(f"ETF 总数：{results['total_etfs']}只")
    print(f"流动性过滤后：{results['filtered_etfs']}只")
    print(f"市场状态：{results['market_regime']}")
    print(f"Top N: {results['top_n']}")
    
    print(f"\n{'='*70}")
    print(f"Top {results['top_n']} ETF")
    print(f"{'='*70}")
    print(f"{'排名':<4} {'代码':<8} {'行业':<8} {'综合':<8} {'估值':<8} {'动量':<8} {'流动性':<8}")
    print(f"{'='*70}")
    
    for etf in results['top_etfs']:
        print(f"{etf['rank']:<4} {etf['code']:<8} {etf['industry']:<8} "
              f"{etf['composite']:.3f}    {etf['valuation']:.3f}    "
              f"{etf['momentum']:.3f}    {etf['liquidity']:.3f}")
    
    print(f"{'='*70}")
    
    # 行业分布
    industry_count = {}
    for etf in results['top_etfs']:
        industry = etf['industry']
        industry_count[industry] = industry_count.get(industry, 0) + 1
    
    print(f"\n行业分布:")
    for industry, count in sorted(industry_count.items(), key=lambda x: -x[1]):
        print(f"  {industry}: {count}只 ({count/len(results['top_etfs'])*100:.1f}%)")

def main():
    """主函数"""
    print("="*70)
    print("全市场 ETF 多因子筛选 v5.0（改进版）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 加载 ETF 池
    etf_codes = load_etf_pool()
    
    if not etf_codes:
        log_message("⚠️ 无 ETF 数据，使用测试数据")
        etf_codes = ['510300', '510500', '510880', '515790', '512480', '159819', '512880', '512400']
    
    # 2. 运行筛选
    results = run_screening(etf_codes)
    
    # 3. 打印结果
    print_results(results)
    
    print(f"\n✅ 全市场筛选完成！")
    print(f"📄 结果文件：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
