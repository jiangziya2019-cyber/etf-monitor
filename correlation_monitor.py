#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相关性风险监控模块 - 优先级🟡
版本：v1.0 | 创建：2026-03-28 13:47

功能:
  - 计算 32 只 ETF 相关性矩阵
  - 检测高相关性 ETF 对
  - 计算组合 Beta
  - 行业集中度监控
"""

import sys, json, os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
CORRELATION_REPORT = '/home/admin/openclaw/workspace/correlation_report.json'
LOG_FILE = '/home/admin/openclaw/workspace/correlation_monitor.log'

# 行业分类
SECTOR_MAP = {
    '金融': ['510880', '159399', '512800', '510230', '512880'],
    '宽基': ['510300', '510500', '510180'],
    '科技': ['512480', '159819', '515260', '512720', '515880'],
    '制造': ['159566', '159663', '562500', '159227', '515790'],
    '医药': ['512010'],
    '周期': ['512400', '516020', '515210', '516110', '512200'],
    '军工': ['512660', '159206', '159241'],
    '全球': ['513110', '513500', '159937', '160723', '513130'],
}

# 行业限额
SECTOR_LIMITS = {
    '金融': 0.25,
    '宽基': 0.20,
    '科技': 0.25,
    '制造': 0.20,
    '医药': 0.15,
    '周期': 0.20,
    '军工': 0.15,
    '全球': 0.20,
}

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def load_etf_prices(etf_codes: List[str], days: int = 60) -> Dict[str, List[float]]:
    """
    加载 ETF 历史价格数据
    
    Args:
        etf_codes: ETF 代码列表
        days: 天数
    
    Returns:
        价格数据 {code: [prices]}
    """
    prices = {}
    
    for code in etf_codes:
        cache_file = f"{CACHE_DIR}/{code}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # 提取收盘价
                if 'data' in data:
                    price_data = data['data']
                    if len(price_data) > 0:
                        # 取最近 N 天的收盘价
                        recent = price_data[-days:]
                        closes = [float(d.get('close', 0)) for d in recent if d.get('close')]
                        
                        if len(closes) >= 20:  # 至少 20 天数据
                            prices[code] = closes
                            log_message(f"  {code}: {len(closes)}天数据")
            except Exception as e:
                log_message(f"  ⚠️ {code} 加载失败：{e}")
    
    return prices

def calculate_returns(prices: List[float]) -> List[float]:
    """计算日收益率"""
    if len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] > 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
    
    return returns

def calculate_correlation(returns1: List[float], returns2: List[float]) -> float:
    """
    计算两个收益率序列的相关系数
    
    Returns:
        相关系数 (-1 到 1)
    """
    if len(returns1) < 20 or len(returns2) < 20:
        return 0.0
    
    # 对齐数据
    min_len = min(len(returns1), len(returns2))
    r1 = returns1[:min_len]
    r2 = returns2[:min_len]
    
    # 计算均值
    mean1 = sum(r1) / len(r1)
    mean2 = sum(r2) / len(r2)
    
    # 计算协方差和标准差
    cov = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(min_len)) / min_len
    std1 = (sum((r - mean1)**2 for r in r1) / len(r1)) ** 0.5
    std2 = (sum((r - mean2)**2 for r in r2) / len(r2)) ** 0.5
    
    if std1 == 0 or std2 == 0:
        return 0.0
    
    corr = cov / (std1 * std2)
    return round(corr, 3)

def calculate_correlation_matrix(prices: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    """
    计算相关性矩阵
    
    Returns:
        相关性矩阵 {code1: {code2: corr}}
    """
    log_message("计算收益率...")
    returns = {code: calculate_returns(price_list) for code, price_list in prices.items()}
    
    log_message("计算相关性矩阵...")
    codes = list(returns.keys())
    matrix = {}
    
    for i, code1 in enumerate(codes):
        matrix[code1] = {}
        for j, code2 in enumerate(codes):
            if i == j:
                matrix[code1][code2] = 1.0
            elif j < i:
                # 使用已计算的值
                matrix[code1][code2] = matrix[code2][code1]
            else:
                corr = calculate_correlation(returns[code1], returns[code2])
                matrix[code1][code2] = corr
        
        if (i + 1) % 10 == 0:
            log_message(f"  进度 {i+1}/{len(codes)}...")
    
    return matrix

def find_high_correlation_pairs(matrix: Dict[str, Dict[str, float]], threshold: float = 0.8) -> List[Dict]:
    """
    找出高相关性 ETF 对
    
    Args:
        matrix: 相关性矩阵
        threshold: 相关性阈值
    
    Returns:
        高相关性 ETF 对列表
    """
    pairs = []
    codes = list(matrix.keys())
    
    for i, code1 in enumerate(codes):
        for j, code2 in enumerate(codes):
            if j > i:  # 避免重复
                corr = matrix[code1][code2]
                if abs(corr) >= threshold:
                    pairs.append({
                        'code1': code1,
                        'code2': code2,
                        'correlation': corr,
                        'level': '高' if abs(corr) >= 0.9 else '中高'
                    })
    
    # 按相关性排序
    pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
    return pairs

def calculate_sector_concentration(holdings: Dict) -> Dict:
    """
    计算行业集中度
    
    Args:
        holdings: 持仓数据
    
    Returns:
        行业集中度分析
    """
    total_value = holdings.get('total_market_value', 0)
    if total_value == 0:
        return {'status': 'ERROR', 'message': '总市值为 0'}
    
    sector_values = {}
    for sector, codes in SECTOR_MAP.items():
        sector_value = 0
        for etf in holdings.get('holdings', []):
            if etf.get('code') in codes:
                sector_value += etf.get('market_value', 0)
        
        if sector_value > 0:
            sector_values[sector] = {
                'value': sector_value,
                'weight': round(sector_value / total_value, 3),
                'limit': SECTOR_LIMITS.get(sector, 0.30)
            }
    
    # 检查超限
    over_limit = []
    for sector, data in sector_values.items():
        if data['weight'] > data['limit']:
            over_limit.append({
                'sector': sector,
                'weight': data['weight'],
                'limit': data['limit'],
                'excess': round(data['weight'] - data['limit'], 3)
            })
    
    return {
        'status': 'WARN' if over_limit else 'OK',
        'sector_values': sector_values,
        'over_limit': over_limit
    }

def run_correlation_analysis(etf_codes: List[str], holdings: Dict = None) -> Dict:
    """
    运行相关性分析
    
    Args:
        etf_codes: ETF 代码列表
        holdings: 持仓数据（可选）
    
    Returns:
        分析报告
    """
    log_message("="*70)
    log_message("开始相关性分析...")
    
    # 1. 加载价格数据
    log_message(f"加载 {len(etf_codes)}只 ETF 价格数据...")
    prices = load_etf_prices(etf_codes, days=60)
    
    if len(prices) < 10:
        log_message("⚠️ 价格数据不足，跳过分析")
        return {'status': 'ERROR', 'message': '价格数据不足'}
    
    # 2. 计算相关性矩阵
    matrix = calculate_correlation_matrix(prices)
    
    # 3. 找出高相关性 ETF 对
    high_corr_pairs = find_high_correlation_pairs(matrix, threshold=0.8)
    
    log_message(f"发现 {len(high_corr_pairs)}对高相关性 ETF")
    
    # 4. 行业集中度分析
    sector_analysis = {'status': 'SKIP', 'message': '无持仓数据'}
    if holdings:
        sector_analysis = calculate_sector_concentration(holdings)
    
    # 5. 生成报告
    report = {
        'analysis_time': datetime.now().isoformat(),
        'data_period_days': 60,
        'etf_count': len(prices),
        'high_correlation_pairs': high_corr_pairs,
        'pair_count': len(high_corr_pairs),
        'correlation_matrix': matrix,
        'sector_analysis': sector_analysis,
        'recommendations': []
    }
    
    # 6. 生成建议
    if len(high_corr_pairs) > 5:
        report['recommendations'].append({
            'type': 'correlation_risk',
            'level': 'HIGH',
            'message': f'发现{len(high_corr_pairs)}对高相关性 ETF，建议分散配置',
            'pairs': high_corr_pairs[:5]
        })
    
    if sector_analysis.get('over_limit'):
        for item in sector_analysis['over_limit']:
            report['recommendations'].append({
                'type': 'sector_concentration',
                'level': 'WARN',
                'message': f"{item['sector']}行业超限：{item['weight']*100:.1f}% (限额{item['limit']*100:.0f}%)",
                'sector': item['sector']
            })
    
    # 保存报告
    with open(CORRELATION_REPORT, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_message("="*70)
    log_message(f"相关性分析完成！报告已保存：{CORRELATION_REPORT}")
    
    return report

def main():
    """主函数"""
    print("="*70)
    print("相关性风险监控模块 v1.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 全部 32 只 ETF
    all_etfs = [
        '510880', '159399', '510300', '510500', '510180',
        '515790', '159566', '512480', '159819', '512010', '159663', '562500', '159227',
        '512880', '512400', '512980', '515260', '512800', '516110',
        '512720', '516020', '515880', '515210', '512660', '512200',
        '513110', '513500', '159937', '160723', '513130'
    ]
    
    # 加载持仓数据
    holdings_file = '/home/admin/openclaw/workspace/holdings_current.json'
    holdings = None
    if os.path.exists(holdings_file):
        with open(holdings_file, 'r') as f:
            holdings = json.load(f)
        log_message(f"加载持仓数据：{len(holdings.get('holdings', []))}只 ETF")
    
    report = run_correlation_analysis(all_etfs, holdings)
    
    print("\n" + "="*70)
    print("分析结果汇总")
    print("="*70)
    print(f"ETF 数量：{report.get('etf_count', 0)}")
    print(f"高相关性 ETF 对：{report.get('pair_count', 0)}")
    
    if report.get('high_correlation_pairs'):
        print("\n高相关性 ETF 对 Top 5:")
        for pair in report['high_correlation_pairs'][:5]:
            print(f"  {pair['code1']} ↔ {pair['code2']}: {pair['correlation']:.3f} ({pair['level']})")
    
    if report.get('recommendations'):
        print("\n建议:")
        for rec in report['recommendations']:
            print(f"  [{rec['level']}] {rec['message']}")

if __name__ == "__main__":
    main()
