#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四层仓位管理系统 v1.0
基于融合筛选结果的智能仓位分配

四层定义:
- Layer1 战略仓位 (40%): 宽基 ETF + 核心行业，长期持有
- Layer2 核心仓位 (30%): 优质行业 ETF，季度调仓
- Layer3 卫星仓位 (20%): 高弹性行业，月度调仓
- Layer4 现金仓位 (10%): 备用资金，应急/抄底
"""

import sys, json, requests, numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/admin/openclaw/workspace')

# 四层仓位定义
POSITION_LAYERS = {
    'layer1': {'name': '战略仓位', 'target_pct': 0.40, 'description': '核心持仓，长期持有', 'rebalance': '半年'},
    'layer2': {'name': '核心仓位', 'target_pct': 0.30, 'description': '优质行业，季度调仓', 'rebalance': '季度'},
    'layer3': {'name': '卫星仓位', 'target_pct': 0.20, 'description': '高弹性行业，月度调仓', 'rebalance': '月度'},
    'layer4': {'name': '现金仓位', 'target_pct': 0.10, 'description': '备用资金，应急/抄底', 'rebalance': '灵活'}
}

# ETF 分类
WIDE_BASE_ETF = ['510300', '510500', '513110', '513500', '159915', '510180', '515180']
INDUSTRY_ETF = ['512480', '512010', '515790', '512200', '515030', '518880', '159663', '159937', '160723', '510880']

ETF_NAMES = {
    '510300': '沪深 300ETF', '510500': '中证 500ETF', '512480': '半导体 ETF',
    '510880': '红利 ETF', '513110': '纳指 100ETF', '513500': '标普 500ETF',
    '512010': '医药 ETF', '515790': '光伏 ETF', '512200': '房地产 ETF',
    '515030': '消费 ETF', '518880': '黄金 9999', '159915': '创业板 ETF',
    '159663': '储能电池 ETF', '159937': '黄金 9999', '160723': '嘉实原油',
    '510180': '180ETF', '515180': '1000ETF'
}

def load_fusion_results():
    """加载融合筛选结果"""
    try:
        with open('/home/admin/openclaw/workspace/fusion_result.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 无法加载融合结果：{e}")
        return None

def allocate_positions(fusion_results, total_capital=1000000):
    """
    四层仓位分配规则
    
    Layer1 (战略 40%):
    - 宽基 ETF TOP2 (评分>0.55): 20% + 15%
    - 行业 ETF TOP1 (评分>0.65): 5%
    
    Layer2 (核心 30%):
    - 行业 ETF TOP3 (评分>0.60): 10% × 3
    
    Layer3 (卫星 20%):
    - 行业 ETF TOP5 (评分>0.55): 4% × 5
    
    Layer4 (现金 10%):
    - 现金/货基/逆回购
    """
    if not fusion_results:
        return None
    
    results = fusion_results.get('results', {})
    sorted_etfs = sorted(results.items(), key=lambda x: x[1]['composite'], reverse=True)
    
    layers = {
        'layer1': {'etfs': [], 'capital': total_capital * 0.40, 'target_weight': 0.40},
        'layer2': {'etfs': [], 'capital': total_capital * 0.30, 'target_weight': 0.30},
        'layer3': {'etfs': [], 'capital': total_capital * 0.20, 'target_weight': 0.20},
        'layer4': {'etfs': [{'code': 'CASH', 'name': '现金/货基', 'allocation': total_capital * 0.10, 'weight': 1.0, 'score': 0}], 'capital': total_capital * 0.10, 'target_weight': 0.10}
    }
    
    # Layer1: 战略仓位 (40%)
    print("\n分配 Layer1 (战略仓位 40%)...")
    wide_selected = []
    industry_selected = []
    
    # 先选宽基 ETF TOP2
    for code, scores in sorted_etfs:
        if code in WIDE_BASE_ETF and scores['composite'] > 0.50 and len(wide_selected) < 2:
            wide_selected.append((code, scores))
    
    # 再选行业 ETF TOP1 (高分)
    for code, scores in sorted_etfs:
        if code in INDUSTRY_ETF and scores['composite'] > 0.60 and len(industry_selected) < 1:
            industry_selected.append((code, scores))
    
    # 分配到 Layer1
    n_wide = len(wide_selected)
    n_industry = len(industry_selected)
    
    # 宽基 ETF 权重分配
    for i, (code, scores) in enumerate(wide_selected):
        if n_wide == 1:
            weight = 0.25  # 只有 1 只宽基
        elif i == 0:
            weight = 0.20  # 第 1 只
        else:
            weight = 0.15  # 第 2 只
        
        layers['layer1']['etfs'].append({
            'code': code,
            'name': ETF_NAMES.get(code, code),
            'score': scores['composite'],
            'type': 'wide_base',
            'weight': weight,
            'allocation': total_capital * 0.40 * weight / (0.20+0.15 if n_wide==2 else 0.25)
        })
        print(f"  ✅ {code} {ETF_NAMES.get(code, code)}: {weight*100:.0f}% (评分{scores['composite']:.2f})")
    
    # 行业 ETF 权重分配
    for code, scores in industry_selected:
        weight = 0.05
        layers['layer1']['etfs'].append({
            'code': code,
            'name': ETF_NAMES.get(code, code),
            'score': scores['composite'],
            'type': 'industry',
            'weight': weight,
            'allocation': total_capital * 0.40 * weight / 0.05
        })
        print(f"  ✅ {code} {ETF_NAMES.get(code, code)}: {weight*100:.0f}% (评分{scores['composite']:.2f})")
    
    # Layer2: 核心仓位 (30%)
    print("\n分配 Layer2 (核心仓位 30%)...")
    l1_codes = [etf['code'] for etf in layers['layer1']['etfs']]
    industry_for_l2 = [(c, s) for c, s in sorted_etfs if c in INDUSTRY_ETF and c not in l1_codes and s['composite'] > 0.55]
    
    for i, (code, scores) in enumerate(industry_for_l2[:3]):
        weight = 0.10
        layers['layer2']['etfs'].append({
            'code': code,
            'name': ETF_NAMES.get(code, code),
            'score': scores['composite'],
            'type': 'industry',
            'weight': weight,
            'allocation': total_capital * 0.30 * weight / 0.30
        })
        print(f"  ✅ {code} {ETF_NAMES.get(code, code)}: {weight*100:.0f}% (评分{scores['composite']:.2f})")
    
    # Layer3: 卫星仓位 (20%)
    print("\n分配 Layer3 (卫星仓位 20%)...")
    l2_codes = [etf['code'] for etf in layers['layer2']['etfs']]
    used_codes = l1_codes + l2_codes
    industry_for_l3 = [(c, s) for c, s in sorted_etfs if c in INDUSTRY_ETF and c not in used_codes and s['composite'] > 0.50]
    
    for i, (code, scores) in enumerate(industry_for_l3[:5]):
        weight = 0.04
        layers['layer3']['etfs'].append({
            'code': code,
            'name': ETF_NAMES.get(code, code),
            'score': scores['composite'],
            'type': 'industry',
            'weight': weight,
            'allocation': total_capital * 0.20 * weight / 0.20
        })
        print(f"  ✅ {code} {ETF_NAMES.get(code, code)}: {weight*100:.0f}% (评分{scores['composite']:.2f})")
    
    # 如果 Layer3 不足 5 只，用剩余资金补充
    if len(layers['layer3']['etfs']) < 5:
        remaining_weight = 0.20 - sum(etf['weight'] for etf in layers['layer3']['etfs'])
        if remaining_weight > 0 and layers['layer3']['etfs']:
            # 平均增加已有 ETF 权重
            for etf in layers['layer3']['etfs']:
                etf['weight'] += remaining_weight / len(layers['layer3']['etfs'])
                etf['allocation'] = total_capital * 0.20 * etf['weight'] / 0.20
    
    return layers

def generate_position_report(layers, total_capital=1000000):
    """生成仓位报告"""
    lines = ["📊 四层仓位配置报告 v1.0", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", f"总资金：¥{total_capital:,.0f}", ""]
    
    for layer_key, layer_data in layers.items():
        layer_info = POSITION_LAYERS[layer_key]
        actual_pct = layer_data['capital'] / total_capital * 100
        
        lines.append(f"━━━ {layer_info['name']} ({layer_key}) ━━━")
        lines.append(f"目标仓位：{layer_info['target_pct']*100:.0f}% | 实际：{actual_pct:.1f}%")
        lines.append(f"分配资金：¥{layer_data['capital']:,.0f}")
        lines.append(f"调仓频率：{layer_info['rebalance']}")
        lines.append(f"说明：{layer_info['description']}")
        lines.append("")
        
        if layer_data['etfs']:
            lines.append(f"{'代码':<8} {'名称':<15} {'评分':>6} {'权重':>7} {'金额':>12}")
            lines.append("-" * 55)
            
            for etf in layer_data['etfs']:
                if etf['code'] == 'CASH':
                    lines.append(f"{etf['code']:<8} {etf['name']:<15} {'-':>6} {etf['weight']*100:>6.1f}% ¥{etf['allocation']:>10,.0f}")
                else:
                    lines.append(f"{etf['code']:<8} {etf['name']:<15} {etf['score']:>6.2f} {etf['weight']*100:>6.1f}% ¥{etf['allocation']:>10,.0f}")
        else:
            lines.append("  (无符合配置的 ETF)")
        
        lines.append("")
    
    # 汇总
    lines.append("━━━ 仓位汇总 ━━━")
    total_equity = 0
    for layer_key in ['layer1', 'layer2', 'layer3']:
        layer_data = layers[layer_key]
        layer_pct = layer_data['capital'] / total_capital * 100
        n_etfs = len(layer_data['etfs'])
        lines.append(f"{POSITION_LAYERS[layer_key]['name']}: ¥{layer_data['capital']:>10,.0f} ({layer_pct:>5.1f}%) - {n_etfs}只 ETF")
        total_equity += layer_data['capital']
    
    cash = layers['layer4']['capital']
    lines.append(f"{POSITION_LAYERS['layer4']['name']}: ¥{cash:>10,.0f} ({cash/total_capital*100:>5.1f}%) - 现金/货基")
    lines.append(f"{'总计':>20}: ¥{total_capital:>10,.0f} (100.0%)")
    lines.append("")
    lines.append("⚠️ 投资有风险，决策需谨慎")
    
    return "\n".join(lines)

def main():
    print("="*70)
    print("四层仓位管理系统 v1.0")
    print("基于融合筛选结果的智能仓位分配")
    print("="*70)
    
    # 加载融合结果
    print("\n加载融合筛选结果...")
    fusion_results = load_fusion_results()
    
    if not fusion_results:
        print("❌ 未找到融合筛选结果，请先运行 sector_etf_fusion.py")
        return
    
    n_etfs = len(fusion_results.get('results', {}))
    print(f"✅ 加载成功：{n_etfs} 只 ETF")
    
    # 仓位分配
    print("\n进行四层仓位分配...")
    layers = allocate_positions(fusion_results, total_capital=1000000)
    
    if not layers:
        print("❌ 仓位分配失败")
        return
    
    print("\n✅ 四层仓位分配完成")
    
    # 生成报告
    report = generate_position_report(layers, total_capital=1000000)
    print("\n" + report)
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_capital': 1000000,
        'layers': layers,
        'position_layers': POSITION_LAYERS,
        'fusion_version': fusion_results.get('timestamp', 'unknown')
    }
    
    with open('/home/admin/openclaw/workspace/four_layer_positions.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 仓位配置已保存至 four_layer_positions.json")

if __name__ == "__main__":
    main()
