#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 融合分析框架 - 主运行脚本
版本：v0.1 | 创建：2026-03-27

功能：
1. 初始化 6 大方向筛选规则
2. 运行进化迭代优化规则
3. 输出观察池推荐列表
4. 对接现有触发器系统
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
from etf_quanta_framework import (
    MiningTrajectory, ScreeningHypothesis, FilterRule,
    RuleType, MarketRegime, ActionStatus,
    generate_id, current_timestamp
)
from etf_quanta_eval import EvolutionEngine


def load_etf_pool():
    """加载 ETF 池（从真实数据源）"""
    try:
        # 1. 获取价格数据
        from data_fetcher import get_etf_prices
        prices = get_etf_prices(use_cache=True)
        
        # 2. 获取估值数据
        from data_fetcher_extended import get_etf_valuation_data
        valuations = get_etf_valuation_data()
        
        # 3. 合并数据
        etf_pool = []
        for code, price_data in prices.items():
            # 获取估值数据（可能为 None）
            val_data = valuations.get(code, {})
            
            # 计算技术指标（简化：使用涨跌幅估算）
            change_pct = price_data.get('change_pct', 0)
            pe_pct = val_data.get('pe_percentile')
            pb_pct = val_data.get('pb_percentile')
            
            etf = {
                'code': code,
                'name': price_data.get('name', val_data.get('note', '')),
                'price': price_data.get('price', 0),
                'change_pct': change_pct,
                'volume': price_data.get('volume', 0),
                # 估值数据
                'pe_percentile': pe_pct if pe_pct is not None else 50.0,  # 默认中位数
                'pb_percentile': pb_pct if pb_pct is not None else 50.0,
                'pe_ttm': val_data.get('pe_ttm'),
                'pb_mrq': val_data.get('pb_mrq'),
                # 技术指标（简化估算）
                'return_20d': change_pct * 5 if change_pct else 0,
                'return_60d': change_pct * 10 if change_pct else 0,
                'volatility_20d': abs(change_pct) / 100 if change_pct else 0.015,
                # 其他
                'net_inflow': 0,
                'turnover_rate': 0.02,
                'premium_rate': 0,
                'data_source': price_data.get('source', 'unknown')
            }
            etf_pool.append(etf)
        
        print(f"[数据] 加载 {len(etf_pool)} 只 ETF（真实数据）")
        return etf_pool
    
    except Exception as e:
        print(f"[警告] 加载真实数据失败：{e}")
        print(f"[降级] 使用缓存 + 模拟估值数据")
        
        try:
            with open('etf_price_cache.json', 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            etf_pool = []
            for code, data in cache.get('prices', {}).items():
                etf = {
                    'code': code,
                    'name': data.get('name', ''),
                    'price': data.get('price', 0),
                    'change_pct': data.get('change_pct', 0),
                    'volume': data.get('volume', 0),
                    'pe_percentile': 50.0,
                    'pb_percentile': 50.0,
                    'return_20d': data.get('change_pct', 0) * 5,
                    'return_60d': data.get('change_pct', 0) * 10,
                    'volatility_20d': abs(data.get('change_pct', 0)) / 100,
                    'net_inflow': 0,
                    'turnover_rate': 0.02,
                    'premium_rate': 0
                }
                etf_pool.append(etf)
            
            print(f"[数据] 加载 {len(etf_pool)} 只 ETF（缓存）")
            return etf_pool
        except:
            pass
        
        # 最后降级：模拟数据
        print(f"[降级] 使用模拟数据")
        return [
            {'code': '510300', 'name': '沪深 300ETF', 'pe_percentile': 35.0, 'return_20d': 5.2, 'volatility_20d': 0.018, 'change_pct': 0.5},
            {'code': '510500', 'name': '中证 500ETF', 'pe_percentile': 25.0, 'return_20d': 3.8, 'volatility_20d': 0.015, 'change_pct': 0.3},
            {'code': '159915', 'name': '创业板 ETF', 'pe_percentile': 45.0, 'return_20d': 8.1, 'volatility_20d': 0.025, 'change_pct': 1.2},
            {'code': '518880', 'name': '黄金 9999', 'pe_percentile': None, 'return_20d': -5.2, 'volatility_20d': 0.012, 'change_pct': -0.8},
            {'code': '160723', 'name': '嘉实原油', 'pe_percentile': None, 'return_20d': 15.3, 'volatility_20d': 0.035, 'change_pct': 2.4},
        ] * 100


def detect_market_regime(etf_pool):
    """检测市场状态"""
    avg_return = sum(e.get('return_20d', 0) for e in etf_pool) / len(etf_pool) if etf_pool else 0
    
    if avg_return > 5:
        return MarketRegime.BULL
    elif avg_return < -5:
        return MarketRegime.BEAR
    else:
        return MarketRegime.SIDEWAYS


def run_quanta_screening(iterations: int = 3, top_n: int = 15):
    """
    运行 QuantaAlpha 筛选
    
    Args:
        iterations: 进化迭代次数
        top_n: 输出 Top N 只 ETF
        
    Returns:
        筛选结果字典
    """
    print("="*70)
    print("ETF-QuantaAlpha 智能筛选系统")
    print(f"迭代次数：{iterations} | 输出数量：{top_n}")
    print("="*70)
    
    # 1. 加载数据
    etf_pool = load_etf_pool()
    
    # 2. 检测市场状态
    regime = detect_market_regime(etf_pool)
    print(f"[市场状态] {regime.value}")
    
    # 3. 运行进化
    engine = EvolutionEngine()
    
    for i in range(iterations):
        result = engine.run_iteration(etf_pool)
        print(f"\n[迭代 {i+1}/{iterations}] 轨迹数={result['count']}, 最佳奖励={result['top_reward']:.4f}")
    
    # 4. 聚合最优规则选出的 ETF
    print(f"\n[聚合] 合并最优规则结果...")
    
    all_selected = {}
    for traj in engine.trajectories[:5]:  # Top 5 规则
        if traj.result:
            for code in traj.result.selected_etfs:
                if code not in all_selected:
                    all_selected[code] = {'count': 0, 'trajectories': []}
                all_selected[code]['count'] += 1
                all_selected[code]['trajectories'].append(traj.hypothesis.name)
    
    # 5. 排序并输出
    sorted_etfs = sorted(all_selected.items(), key=lambda x: x[1]['count'], reverse=True)
    
    output = {
        'timestamp': current_timestamp(),
        'market_regime': regime.value,
        'iterations': iterations,
        'total_rules': len(engine.rule_pool.rules),
        'selected_etfs': []
    }
    
    print(f"\n{'='*70}")
    print(f"观察池推荐 (Top {top_n})")
    print(f"{'='*70}")
    
    for code, info in sorted_etfs[:top_n]:
        # 查找 ETF 详细信息
        etf_info = next((e for e in etf_pool if e['code'] == code), {})
        
        entry = {
            'code': code,
            'name': etf_info.get('name', 'Unknown'),
            'selected_by': info['count'],
            'rules': info['trajectories'],
            'price': etf_info.get('price', 0),
            'change_pct': etf_info.get('change_pct', 0)
        }
        output['selected_etfs'].append(entry)
        
        print(f"  {code}: {etf_info.get('name', 'Unknown')}")
        print(f"    选中 {info['count']} 次 | 规则：{', '.join(info['trajectories'][:3])}")
    
    print(f"\n{'='*70}")
    print(f"完成时间：{output['timestamp']}")
    print(f"{'='*70}")
    
    return output


def export_results(results: Dict, filename: str = 'quanta_screening_result.json'):
    """导出结果"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[导出] 结果已保存到 {filename}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF-QuantaAlpha 智能筛选')
    parser.add_argument('--iterations', type=int, default=3, help='进化迭代次数')
    parser.add_argument('--top-n', type=int, default=15, help='输出 ETF 数量')
    parser.add_argument('--output', type=str, default='quanta_screening_result.json', help='输出文件名')
    
    args = parser.parse_args()
    
    # 运行筛选
    results = run_quanta_screening(iterations=args.iterations, top_n=args.top_n)
    
    # 导出结果
    export_results(results, args.output)
    
    print(f"\n✅ 筛选完成！")
    print(f"   - 观察池 ETF: {len(results['selected_etfs'])} 只")
    print(f"   - 使用规则：{results['total_rules']} 条")
    print(f"   - 市场状态：{results['market_regime']}")
