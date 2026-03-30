#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 阶段 3 优化脚本 - 完整版
版本：v1.0 | 创建：2026-03-28
"""

import sys, os, json, time
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')
from etf_quanta_framework import ScreeningHypothesis, FilterRule, RuleType, MarketRegime, generate_id, current_timestamp

BACKTEST_START_DATE = "20200101"
BACKTEST_END_DATE = "20260328"
INITIAL_CAPITAL = 1000000
TRANSACTION_COST = 0.001
CORE_ETFS = ['510300', '510500', '159915', '518880', '512480', '513110', '510880', '513500', '159919', '159920', '513100', '510180', '512010', '515790', '159841', '512880', '512690', '515030', '159995', '515880', '516160']

def get_historical_data(etf_codes, start_date, end_date):
    print(f"\n{'='*70}\n获取历史数据：{len(etf_codes)}只 ETF\n{'='*70}")
    historical_data = {}
    try:
        import tushare as ts
        ts.set_token('7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75')
        pro = ts.pro_api()
        for i, code in enumerate(etf_codes, 1):
            print(f"[{i}/{len(etf_codes)}] {code}...", end=" ")
            ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
            try:
                df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    data = {row['trade_date']: {'close': float(row.get('close', 0)), 'volume': float(row.get('vol', 0))} for _, row in df.iterrows()}
                    historical_data[code] = data
                    print(f"✅ {len(data)}条")
                else:
                    print("⚠️ 无数据")
            except Exception as e:
                print(f"❌ {e}")
            time.sleep(0.1)
        print(f"\n✅ Tushare Pro 完成：{len(historical_data)}/{len(etf_codes)}")
    except Exception as e:
        print(f"❌ Tushare 失败：{e}")
    return historical_data

def apply_filters(historical_data, date, hypothesis):
    selected = []
    for code, data in historical_data.items():
        if date not in data: continue
        close_prices = [data[d]['close'] for d in sorted(data.keys()) if d <= date]
        return_20d = (close_prices[-1] / close_prices[-20] - 1) * 100 if len(close_prices) >= 20 else 0
        return_60d = (close_prices[-1] / close_prices[-60] - 1) * 100 if len(close_prices) >= 60 else 0
        volatility = np.std([close_prices[i]/close_prices[i-1] - 1 for i in range(-19, 0)]) * np.sqrt(252) * 100 if len(close_prices) >= 20 else 0
        passed = True
        for rule in hypothesis.filters:
            field_map = {'return_20d': return_20d, 'return_60d': return_60d, 'volatility_20d': volatility, 'pe_percentile': 40.0, 'volume': data[date].get('volume', 1e7)}
            if rule.field in field_map:
                value = field_map[rule.field]
                if rule.operator == '<' and not (value < rule.value): passed = False
                elif rule.operator == '>' and not (value > rule.value): passed = False
            if not passed: break
        if passed: selected.append(code)
    return selected

def run_backtest(historical_data, hypothesis, rebalance_period=20, stop_loss=-8.0, take_profit=20.0, max_positions=10):
    all_dates = sorted(set().union(*[set(data.keys()) for data in historical_data.values()]))
    if len(all_dates) < rebalance_period * 2: return None
    capital = INITIAL_CAPITAL
    positions = {}
    portfolio_values = []
    trades = []
    stop_loss_count = take_profit_count = 0
    rebalance_dates = all_dates[::rebalance_period]
    
    for date in rebalance_dates:
        for code, pos in list(positions.items()):
            if code in historical_data and date in historical_data[code]:
                current_price = historical_data[code][date]['close']
                return_pct = (current_price - pos['buy_price']) / pos['buy_price'] * 100
                if return_pct <= stop_loss:
                    sale_value = pos['shares'] * current_price * (1 - TRANSACTION_COST)
                    capital += sale_value
                    trades.append({'date': date, 'code': code, 'action': 'stop_loss', 'return_pct': return_pct})
                    stop_loss_count += 1
                    del positions[code]
                elif return_pct >= take_profit:
                    sale_value = pos['shares'] * current_price * (1 - TRANSACTION_COST)
                    capital += sale_value
                    trades.append({'date': date, 'code': code, 'action': 'take_profit', 'return_pct': return_pct})
                    take_profit_count += 1
                    del positions[code]
        
        current_value = capital + sum(pos['shares'] * historical_data[code][date]['close'] for code, pos in positions.items() if code in historical_data and date in historical_data[code])
        portfolio_values.append({'date': date, 'value': current_value})
        
        if len(positions) < max_positions:
            selected = apply_filters(historical_data, date, hypothesis)[:max_positions - len(positions)]
            if selected and capital > 0:
                alloc = capital / len(selected)
                for code in selected:
                    if code not in positions and date in historical_data.get(code, {}):
                        price = historical_data[code][date]['close']
                        shares = int((alloc * (1 - TRANSACTION_COST)) / price)
                        if shares > 0:
                            capital -= shares * price * (1 + TRANSACTION_COST)
                            positions[code] = {'shares': shares, 'buy_price': price}
                            trades.append({'date': date, 'code': code, 'action': 'buy'})
    
    final_date = all_dates[-1]
    final_value = capital + sum(pos['shares'] * historical_data[code][final_date]['close'] for code, pos in positions.items() if code in historical_data and final_date in historical_data[code])
    portfolio_values.append({'date': final_date, 'value': final_value})
    
    values = [pv['value'] for pv in portfolio_values]
    returns = [(values[i] / values[i-1] - 1) * 100 for i in range(1, len(values))]
    total_days = (datetime.strptime(final_date, '%Y%m%d') - datetime.strptime(all_dates[0], '%Y%m%d')).days
    total_return = (values[-1] - values[0]) / values[0]
    arr = ((1 + total_return) ** (365 / total_days) - 1) * 100 if total_days > 0 else 0
    peak = values[0]
    max_drawdown = max((peak - (peak := max(peak, v))) / peak * 100 for v in values)
    sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 and np.std(returns) > 0 else 0
    
    return {'hypothesis': hypothesis.name, 'initial_capital': INITIAL_CAPITAL, 'final_value': final_value, 'total_return': total_return * 100, 'arr': arr, 'mdd': max_drawdown, 'sharpe': sharpe, 'stop_loss_count': stop_loss_count, 'take_profit_count': take_profit_count, 'trade_count': len(trades), 'rebalance_period': rebalance_period}

def generate_optimized_hypotheses():
    hypotheses = []
    regime = MarketRegime.SIDEWAYS
    hypotheses.append(ScreeningHypothesis(id=generate_id("hyp_"), name="短期动量增强", description="20 日>3% + 放量", rule_type=RuleType.MOMENTUM, market_regime=regime, filters=[FilterRule('return_20d', '>', 3.0), FilterRule('volume', '>', 1e6)], sort_by='return_20d', ascending=False, created_at=current_timestamp()))
    hypotheses.append(ScreeningHypothesis(id=generate_id("hyp_"), name="低估值增强", description="PE<40% + 正动量", rule_type=RuleType.VALUE, market_regime=regime, filters=[FilterRule('pe_percentile', '<', 40.0), FilterRule('return_20d', '>', 0)], sort_by='pe_percentile', ascending=True, created_at=current_timestamp()))
    hypotheses.append(ScreeningHypothesis(id=generate_id("hyp_"), name="行业轮动", description="60 日>8% + 20 日>2%", rule_type=RuleType.MOMENTUM, market_regime=regime, filters=[FilterRule('return_60d', '>', 8.0), FilterRule('return_20d', '>', 2.0)], sort_by='return_60d', ascending=False, created_at=current_timestamp()))
    hypotheses.append(ScreeningHypothesis(id=generate_id("hyp_"), name="估值动量融合", description="PE<50% + 20 日>3%", rule_type=RuleType.VALUE, market_regime=regime, filters=[FilterRule('pe_percentile', '<', 50.0), FilterRule('return_20d', '>', 3.0)], sort_by='return_20d', ascending=False, created_at=current_timestamp()))
    hypotheses.append(ScreeningHypothesis(id=generate_id("hyp_"), name="低波动增强", description="波动率<2.5%", rule_type=RuleType.VOLATILITY, market_regime=regime, filters=[FilterRule('volatility_20d', '<', 0.025)], sort_by='volatility_20d', ascending=True, created_at=current_timestamp()))
    print(f"\n✅ 生成 {len(hypotheses)} 个优化策略")
    return hypotheses

def main():
    print("="*70 + f"\nETF-QuantaAlpha 阶段 3 优化回测\n时间：{current_timestamp()}\n" + "="*70)
    historical_data = get_historical_data(CORE_ETFS, BACKTEST_START_DATE, BACKTEST_END_DATE)
    if not historical_data: return
    hypotheses = generate_optimized_hypotheses()
    
    print(f"\n{'='*70}\n测试不同调仓周期\n{'='*70}")
    all_results = []
    for period in [10, 20, 30]:
        print(f"\n{'='*50}\n调仓周期：{period}交易日\n{'='*50}")
        for h in hypotheses:
            result = run_backtest(historical_data, h, rebalance_period=period, stop_loss=-8.0, take_profit=20.0, max_positions=10)
            if result:
                result['rebalance_period'] = period
                all_results.append(result)
                print(f"\n  {h.name}: ARR={result['arr']:.2f}% | MDD={result['mdd']:.2f}% | Sharpe={result['sharpe']:.3f} | 止损{result['stop_loss_count']}次 | 止盈{result['take_profit_count']}次")
    
    print(f"\n{'='*70}\n阶段 3 优化结果汇总\n{'='*70}")
    if all_results:
        all_results.sort(key=lambda x: x['arr'], reverse=True)
        print(f"\n【Top 5 策略】")
        for i, r in enumerate(all_results[:5], 1):
            print(f"\n{i}. {r['hypothesis']} (调仓{r['rebalance_period']}日): ARR={r['arr']:.2f}% | MDD={r['mdd']:.2f}% | Sharpe={r['sharpe']:.3f}")
        
        print(f"\n【对比阶段 2】最佳 ARR: 2.91% → {all_results[0]['arr']:.2f}% ({'+' if all_results[0]['arr'] > 2.91 else ''}{all_results[0]['arr'] - 2.91:.2f}%)")
        
        with open('/home/admin/openclaw/workspace/stage3_backtest_result.json', 'w', encoding='utf-8') as f:
            json.dump({'timestamp': current_timestamp(), 'stage': 3, 'results': all_results}, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n✅ 结果已保存：stage3_backtest_result.json")
    
    print(f"\n{'='*70}\n✅ 阶段 3 优化完成\n{'='*70}")

if __name__ == "__main__":
    main()
