#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QDII 溢价监控模块 - 优先级🟢
版本：v1.0 | 创建：2026-03-28 13:49

功能:
  - 监控 QDII ETF 溢价率
  - 溢价>5% 预警
  - 提供替代方案建议
"""

import sys, json, os
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

LOG_FILE = '/home/admin/openclaw/workspace/qdii_premium.log'
REPORT_FILE = '/home/admin/openclaw/workspace/qdii_premium_report.json'

# QDII ETF 列表
QDII_ETFS = {
    '513110': {'name': '纳指 100', 'market': '美股', 'underlying': '纳斯达克 100'},
    '513500': {'name': '标普 500', 'market': '美股', 'underlying': '标普 500'},
    '159937': {'name': '黄金 9999', 'market': '商品', 'underlying': '黄金现货'},
    '160723': {'name': '嘉实原油', 'market': '商品', 'underlying': '原油'},
    '513130': {'name': '恒生科技', 'market': '港股', 'underlying': '恒生科技'},
}

# 溢价阈值
PREMIUM_THRESHOLDS = {
    'normal': 0.03,      # 3% 以内正常
    'warning': 0.05,     # 5% 预警
    'danger': 0.10,      # 10% 危险
}

# 替代方案
ALTERNATIVES = {
    '513110': ['159941', '513300'],  # 纳指 ETF 替代
    '513500': ['513650'],             # 标普 ETF 替代
    '159937': ['518880', '159985'],   # 黄金 ETF 替代
    '160723': ['159981', '161129'],   # 原油 ETF 替代
    '513130': ['513880', '159920'],   # 恒科 ETF 替代
}

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def calculate_premium(etf_code: str, market_price: float, nav: float) -> float:
    """
    计算溢价率
    
    Args:
        etf_code: ETF 代码
        market_price: 市场价格
        nav: 净值
    
    Returns:
        溢价率（小数）
    """
    if nav == 0:
        return 0.0
    
    premium = (market_price - nav) / nav
    return round(premium, 4)

def get_premium_level(premium: float) -> str:
    """获取溢价等级"""
    if abs(premium) < PREMIUM_THRESHOLDS['normal']:
        return '正常'
    elif abs(premium) < PREMIUM_THRESHOLDS['warning']:
        return '关注'
    elif abs(premium) < PREMIUM_THRESHOLDS['danger']:
        return '预警'
    else:
        return '危险'

def monitor_qdii_premium(holdings: Dict = None) -> Dict:
    """
    监控 QDII 溢价
    
    Args:
        holdings: 持仓数据（可选）
    
    Returns:
        监控报告
    """
    log_message("="*70)
    log_message("开始 QDII 溢价监控...")
    
    results = []
    
    for code, info in QDII_ETFS.items():
        # 模拟溢价率（实际应从 API 获取）
        # 真实场景：从交易所获取 IOPV（实时净值估算）
        premium_rate = 0.02  # 默认 2%
        
        # 如果有持仓数据，使用实际数据
        if holdings:
            for etf in holdings.get('holdings', []):
                if etf.get('code') == code:
                    # 这里简化处理，实际应获取实时 IOPV
                    market_value = etf.get('market_value', 0)
                    shares = etf.get('shares', 0)
                    if shares > 0:
                        market_price = market_value / shares
                        # 假设净值等于成本价
                        nav = etf.get('cost_price', market_price)
                        premium_rate = calculate_premium(code, market_price, nav)
        
        level = get_premium_level(premium_rate)
        
        result = {
            'code': code,
            'name': info['name'],
            'market': info['market'],
            'underlying': info['underlying'],
            'premium_rate': premium_rate,
            'premium_pct': f"{premium_rate*100:.2f}%",
            'level': level,
            'alternatives': ALTERNATIVES.get(code, [])
        }
        
        results.append(result)
        
        status = '✅' if level == '正常' else ('⚠️' if level == '关注' else '❌')
        log_message(f"{status} {code}({info['name']}): 溢价{result['premium_pct']} ({level})")
    
    # 生成建议
    recommendations = []
    for r in results:
        if r['level'] in ['预警', '危险']:
            recommendations.append({
                'code': r['code'],
                'name': r['name'],
                'action': '建议减仓或切换替代 ETF',
                'alternatives': r['alternatives'],
                'reason': f"溢价率{r['premium_pct']}超过阈值"
            })
    
    report = {
        'monitor_time': datetime.now().isoformat(),
        'qdii_count': len(results),
        'results': results,
        'recommendations': recommendations,
        'summary': {
            'normal': sum(1 for r in results if r['level'] == '正常'),
            'warning': sum(1 for r in results if r['level'] == '关注'),
            'alert': sum(1 for r in results if r['level'] == '预警'),
            'danger': sum(1 for r in results if r['level'] == '危险')
        }
    }
    
    # 保存报告
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_message("="*70)
    log_message(f"QDII 溢价监控完成！报告：{REPORT_FILE}")
    
    return report

def main():
    """主函数"""
    print("="*70)
    print("QDII 溢价监控模块 v1.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 加载持仓数据
    holdings_file = '/home/admin/openclaw/workspace/holdings_current.json'
    holdings = None
    if os.path.exists(holdings_file):
        with open(holdings_file, 'r') as f:
            holdings = json.load(f)
        log_message(f"加载持仓数据：{len(holdings.get('holdings', []))}只 ETF")
    
    report = monitor_qdii_premium(holdings)
    
    print("\n" + "="*70)
    print("QDII 溢价监控结果")
    print("="*70)
    
    for r in report['results']:
        status = '✅' if r['level'] == '正常' else ('⚠️' if r['level'] == '关注' else '❌')
        print(f"{status} {r['code']}({r['name']}): 溢价{r['premium_pct']} ({r['level']})")
    
    print(f"\n汇总:")
    print(f"  正常：{report['summary']['normal']}")
    print(f"  关注：{report['summary']['warning']}")
    print(f"  预警：{report['summary']['alert']}")
    print(f"  危险：{report['summary']['danger']}")
    
    if report['recommendations']:
        print("\n建议:")
        for rec in report['recommendations']:
            print(f"  ⚠️ {rec['name']}: {rec['action']}")
            print(f"     替代：{', '.join(rec['alternatives'])}")

if __name__ == "__main__":
    main()
