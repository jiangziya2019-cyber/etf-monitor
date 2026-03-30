#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四层仓位全市场筛选引擎"""

import sys, json, os, numpy as np
from datetime import datetime

sys.path.insert(0, '/home/admin/openclaw/workspace')

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/四层仓位筛选结果.json'

# 各层配置
LAYER1_CODES = ['510880', '159399', '510300', '510500', '510180']  # 防守型
LAYER2_CODES = ['512480', '159819', '159566', '515790', '512010', '159663']  # 政策导向
LAYER4_CODES = ['513110', '513500', '159937', '160723', '513130']  # 全球配置

def load_etf_cache():
    """加载 ETF 缓存数据"""
    print(f"加载 ETF 缓存...")
    etf_data = {}
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            code = filename.replace('.json', '')
            try:
                with open(f"{CACHE_DIR}/{filename}", 'r') as f:
                    etf_data[code] = json.load(f)
            except: pass
    print(f"✅ 加载 {len(etf_data)}只 ETF 缓存")
    return etf_data

def calc_metrics(data: dict) -> dict:
    """计算指标"""
    if len(data) < 60: return {}
    closes = [data[d]['close'] for d in sorted(data.keys())]
    returns = [closes[i]/closes[i-1] - 1 for i in range(-19, 0)]
    vol = np.std(returns) * np.sqrt(252) * 100
    r20 = (closes[-1]/closes[-20] - 1) * 100
    r60 = (closes[-1]/closes[-60] - 1) * 100
    return {'volatility': round(vol, 2), 'return_20d': round(r20, 2), 'return_60d': round(r60, 2)}

def screen_layer1(etf_data):
    """第一层：防守型"""
    print("\n【第一层】超长期防守持仓筛选...")
    results = []
    div_yields = {'510880': 5.2, '159399': 4.1, '510300': 3.2, '510500': 2.8, '510180': 4.5}
    for code in LAYER1_CODES:
        if code not in etf_data: continue
        metrics = calc_metrics(etf_data[code])
        div = div_yields.get(code, 0)
        score = div * 0.5 + (100 - metrics.get('volatility', 100)) * 0.3 + min(metrics.get('return_20d', 0), 10) * 0.2
        results.append({'code': code, 'dividend_yield': div, **metrics, 'score': round(score, 2), 'target_weight': 1.0/len(LAYER1_CODES)})
        print(f"  ✅ {code}: 股息{div}% 波动{metrics.get('volatility', 0):.1f}% 20 日{metrics.get('return_20d', 0):.1f}%")
    return sorted(results, key=lambda x: x['score'], reverse=True)

def screen_layer2(etf_data):
    """第二层：政策导向"""
    print("\n【第二层】中长期未来持仓筛选...")
    themes = {'半导体': '512480', 'AI': '159819', '储能': '159566', '光伏': '515790', '医药': '512010', '机床': '159663'}
    results = []
    for theme, code in themes.items():
        if code not in etf_data: continue
        metrics = calc_metrics(etf_data[code])
        score = metrics.get('return_60d', 0) * 0.5 + (100 - metrics.get('volatility', 100)) * 0.3 + metrics.get('return_20d', 0) * 0.2
        results.append({'theme': theme, 'code': code, **metrics, 'score': round(score, 2), 'target_weight': 1.0/len(themes)})
        print(f"  ✅ {theme}({code}): 60 日{metrics.get('return_60d', 0):.1f}% 波动{metrics.get('volatility', 0):.1f}%")
    return sorted(results, key=lambda x: x['score'], reverse=True)

def screen_layer3(etf_data):
    """第三层：量化策略"""
    print("\n【第三层】短期获利持仓筛选（多因子 Top 30）...")
    candidates = []
    for code, data in etf_data.items():
        metrics = calc_metrics(data)
        if len(metrics) < 3 or metrics['volatility'] > 30: continue
        score = (100 - metrics['volatility']) * 0.4 + max(metrics['return_20d'], 0) * 0.35 + 50 * 0.25
        candidates.append({'code': code, **metrics, 'score': round(score, 2)})
    candidates.sort(key=lambda x: x['score'], reverse=True)
    top30 = candidates[:30]
    for i, c in enumerate(top30[:5], 1):
        print(f"  Top{i}: {c['code']} 评分{c['score']:.1f} 20 日{c['return_20d']:.1f}% 波动{c['volatility']:.1f}%")
    print(f"  ...共{len(top30)}只")
    for c in top30: c['target_weight'] = 1.0/len(top30)
    return top30

def screen_layer4(etf_data):
    """第四层：全球配置"""
    print("\n【第四层】其他全天候仓位筛选...")
    categories = {'美股': ['513110', '513500'], '商品': ['159937', '160723'], '港股': ['513130']}
    weights = {'513110': 0.30, '513500': 0.20, '159937': 0.25, '160723': 0.15, '513130': 0.10}
    results = []
    for cat, codes in categories.items():
        for code in codes:
            if code not in etf_data: continue
            metrics = calc_metrics(etf_data[code])
            results.append({'category': cat, 'code': code, **metrics, 'target_weight': weights.get(code, 0.10)})
            print(f"  ✅ {cat}({code}): 60 日{metrics.get('return_60d', 0):.1f}% 波动{metrics.get('volatility', 0):.1f}%")
    return results

def main():
    print("="*70 + f"\n四层仓位全市场筛选\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "="*70)
    
    etf_data = load_etf_cache()
    
    layer1 = screen_layer1(etf_data)
    layer2 = screen_layer2(etf_data)
    layer3 = screen_layer3(etf_data)
    layer4 = screen_layer4(etf_data)
    
    # 生成最终方案
    plan = {
        'timestamp': datetime.now().isoformat(),
        'total_capital': 200000,
        'layers': {
            'layer1_defensive': {'target_pct': 0.30, 'target_amount': 60000, 'etfs': layer1},
            'layer2_future': {'target_pct': 0.30, 'target_amount': 60000, 'etfs': layer2},
            'layer3_quant': {'target_pct': 0.25, 'target_amount': 50000, 'etfs': layer3},
            'layer4_global': {'target_pct': 0.15, 'target_amount': 30000, 'etfs': layer4}
        }
    }
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}\n✅ 筛选完成！结果已保存：{OUTPUT_FILE}\n{'='*70}")
    print(f"\n【汇总】")
    print(f"  第一层（防守）: {len(layer1)}只 ETF - ¥60,000 (30%)")
    print(f"  第二层（未来）: {len(layer2)}只 ETF - ¥60,000 (30%)")
    print(f"  第三层（量化）: {len(layer3)}只 ETF - ¥50,000 (25%)")
    print(f"  第四层（全球）: {len(layer4)}只 ETF - ¥30,000 (15%)")

if __name__ == "__main__":
    main()
