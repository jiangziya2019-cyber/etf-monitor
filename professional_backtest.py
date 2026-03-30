#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级回测系统 v2.0
长周期 + 交易成本 + 压力测试
"""

import sys, json, requests, numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, '/home/admin/openclaw/workspace')

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

ETF_POOL = {
    'industry': ['512480', '510880', '159663', '512010', '515790', '518880'],
    'wide_base': ['510300', '510500', '513110', '513500', '159915']
}

ETF_NAMES = {
    '510300': '沪深 300ETF', '510500': '中证 500ETF', '512480': '半导体 ETF',
    '510880': '红利 ETF', '513110': '纳指 100ETF', '513500': '标普 500ETF',
    '512010': '医药 ETF', '515790': '光伏 ETF', '518880': '黄金 9999',
    '159663': '储能电池 ETF', '159915': '创业板 ETF'
}

TRANSACTION_COST = {'stamp_tax': 0.001, 'commission': 0.0003, 'slippage': 0.001}

STRESS_SCENARIOS = {
    'normal': {'name': '正常市场', 'drop': 0, 'vol_mult': 1.0},
    'correction': {'name': '回调 10%', 'drop': -0.10, 'vol_mult': 1.5},
    'bear': {'name': '熊市 30%', 'drop': -0.30, 'vol_mult': 2.0},
    'crash': {'name': '崩盘 50%', 'drop': -0.50, 'vol_mult': 3.0}
}

def get_tushare_data(api_name, **params):
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = resp.json()
        return result.get("data", {}) if result.get("code") == 0 else None
    except: return None

def fetch_etf_prices(etf_codes, days=250):
    print(f"\n获取 ETF 历史数据 (最近{days}天)...")
    price_data = {}
    
    for code in etf_codes:
        suffix = ".SH" if code.startswith("5") else ".SZ"
        data = get_tushare_data("fund_daily", ts_code=code+suffix)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            prices = []
            for item in data["items"][:days]:
                row = dict(zip(fields, item))
                prices.append({'date': row.get('trade_date', ''), 'close': float(row.get('close', 0))})
            prices.sort(key=lambda x: x['date'])
            price_data[code] = prices
            print(f"  ✅ {code} {ETF_NAMES.get(code, code)}: {len(prices)}天")
    
    return price_data

def run_backtest(price_data, strategy='fusion', initial_capital=1000000, rebalance_days=30):
    print(f"\n运行回测 (策略：{strategy})...")
    
    if strategy == 'fusion':
        etf_pool = ETF_POOL['industry'][:3] + ETF_POOL['wide_base'][:2]
    elif strategy == 'wide_base_only':
        etf_pool = ETF_POOL['wide_base']
    else:
        etf_pool = ETF_POOL['industry'][:5]
    
    weights = {code: 1.0/len(etf_pool) for code in etf_pool}
    
    # 获取所有交易日
    all_dates = set()
    for code in etf_pool:
        if code in price_data:
            for p in price_data[code]:
                all_dates.add(p['date'])
    all_dates = sorted(all_dates)
    
    if not all_dates:
        return None
    
    # 简化回测：计算组合收益
    portfolio_returns = []
    last_rebalance_date = None
    current_weights = {}
    
    for date in all_dates:
        # 调仓
        if last_rebalance_date is None or (int(date) - int(last_rebalance_date)) >= rebalance_days:
            current_weights = weights.copy()
            last_rebalance_date = date
        
        # 计算当日组合收益
        daily_return = 0
        for code in etf_pool:
            if code in price_data and len(price_data[code]) >= 2:
                # 找到当日和前一日价格
                curr_price = None
                prev_price = None
                for i, p in enumerate(price_data[code]):
                    if p['date'] <= date:
                        curr_price = p['close']
                        if i > 0:
                            prev_price = price_data[code][i-1]['close']
                
                if curr_price and prev_price and prev_price > 0:
                    ret = (curr_price - prev_price) / prev_price
                    daily_return += ret * current_weights.get(code, 0)
        
        portfolio_returns.append(daily_return)
    
    # 计算绩效
    cumulative = 1
    values = [initial_capital]
    for ret in portfolio_returns:
        # 扣除交易成本（简化：每次调仓扣除）
        cumulative *= (1 + ret)
        values.append(initial_capital * cumulative)
    
    # 计算交易成本
    n_rebalances = len(all_dates) // rebalance_days
    avg_trade_value = initial_capital / len(etf_pool)
    cost_per_trade = avg_trade_value * (TRANSACTION_COST['stamp_tax'] + TRANSACTION_COST['commission'] + TRANSACTION_COST['slippage'])
    total_cost = n_rebalances * len(etf_pool) * cost_per_trade * 2  # 买入 + 卖出
    
    final_value = values[-1] - total_cost
    total_return = ((final_value / initial_capital) - 1) * 100
    n_days = len(portfolio_returns)
    annual_return = ((final_value / initial_capital) ** (252/n_days) - 1) * 100 if n_days > 0 else 0
    
    volatility = np.std(portfolio_returns) * np.sqrt(252) * 100 if portfolio_returns else 0
    sharpe = (annual_return - 3) / volatility if volatility > 0 else 0
    
    # 最大回撤
    peak = initial_capital
    max_dd = 0
    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
    max_drawdown = -max_dd * 100
    
    win_rate = (sum(1 for r in portfolio_returns if r > 0) / len(portfolio_returns)) * 100 if portfolio_returns else 0
    
    return {
        'strategy': strategy,
        'initial_capital': initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'n_trades': n_rebalances * len(etf_pool) * 2,
        'total_cost': total_cost,
        'n_days': n_days
    }

def run_stress_test(price_data, strategy='fusion'):
    print("\n运行压力测试...")
    results = {}
    
    for scenario_id, scenario in STRESS_SCENARIOS.items():
        print(f"  测试：{scenario['name']}...")
        
        # 应用压力
        stressed_prices = {}
        for code, prices in price_data.items():
            stressed_prices[code] = []
            for i, p in enumerate(prices):
                drop = scenario['drop'] * (i / len(prices))
                adjusted = p['close'] * (1 + drop)
                stressed_prices[code].append({'date': p['date'], 'close': adjusted})
        
        result = run_backtest(stressed_prices, strategy)
        if result:
            result['scenario'] = scenario['name']
            results[scenario_id] = result
    
    return results

def main():
    print("="*70)
    print("专业级回测系统 v2.0")
    print("长周期 + 交易成本 + 压力测试")
    print("="*70)
    
    # 获取数据
    all_etfs = ETF_POOL['industry'] + ETF_POOL['wide_base']
    price_data = fetch_etf_prices(all_etfs, days=250)
    
    if not price_data:
        print("❌ 无法获取数据")
        return
    
    # 回测
    results = {}
    results['fusion'] = run_backtest(price_data, 'fusion')
    results['industry_only'] = run_backtest(price_data, 'industry_only')
    results['wide_base_only'] = run_backtest(price_data, 'wide_base_only')
    
    # 压力测试
    stress_results = run_stress_test(price_data, 'fusion')
    
    # 报告
    print("\n" + "="*70)
    print("回测结果")
    print("="*70)
    print(f"\n{'策略':<15} {'总收益':>10} {'年化':>10} {'夏普':>8} {'回撤':>10} {'胜率':>8}")
    print("-"*65)
    for strategy in ['fusion', 'industry_only', 'wide_base_only']:
        r = results[strategy]
        print(f"{strategy:<15} {r['total_return']:>9.1f}% {r['annual_return']:>9.1f}% {r['sharpe']:>8.2f} {r['max_drawdown']:>9.1f}% {r['win_rate']:>7.1f}%")
    
    print("\n压力测试:")
    print(f"{'场景':<15} {'总收益':>10} {'年化':>10} {'夏普':>8} {'回撤':>10}")
    print("-"*55)
    for scenario_id, result in stress_results.items():
        print(f"{result['scenario']:<15} {result['total_return']:>9.1f}% {result['annual_return']:>9.1f}% {result['sharpe']:>8.2f} {result['max_drawdown']:>9.1f}%")
    
    # 保存
    output = {
        'version': 'v2.0',
        'timestamp': datetime.now().isoformat(),
        'period_days': 250,
        'transaction_costs': TRANSACTION_COST,
        'results': results,
        'stress_test': stress_results
    }
    
    with open('/home/admin/openclaw/workspace/backtest_v2_professional.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 结果已保存至 backtest_v2_professional.json")

if __name__ == "__main__":
    main()
