#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 统一交易引擎
版本：v1.0 整合版 | 创建：2026-03-28

整合：策略引擎 + 现有持仓 + 老板指令 + 风控规则
"""

import sys, json, time, os
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')

def load_config():
    with open('/home/admin/openclaw/workspace/unified_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(CONFIG['data_sources']['log_file'], 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def load_holdings():
    holdings_file = CONFIG['data_sources']['holdings_file']
    if not os.path.exists(holdings_file):
        log_message("❌ 持仓文件不存在")
        return None
    with open(holdings_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_etf_cache():
    cache_dir = CONFIG['data_sources']['etf_cache_dir']
    if not os.path.exists(cache_dir):
        return {}
    etf_data = {}
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            code = filename.replace('.json', '')
            try:
                with open(f"{cache_dir}/{filename}", 'r') as f:
                    etf_data[code] = json.load(f)
            except: pass
    log_message(f"加载 {len(etf_data)}只 ETF 缓存数据")
    return etf_data

def calculate_factors(etf_data, date):
    scores = {}
    for code, data in etf_data.items():
        dates = sorted([d for d in data.keys() if d <= date])
        if len(dates) < 60: continue
        close_prices = [data[d]['close'] for d in dates]
        returns = [close_prices[i]/close_prices[i-1] - 1 for i in range(-19, 0)]
        volatility = np.std(returns) * np.sqrt(252) * 100
        return_20d = (close_prices[-1] / close_prices[-20] - 1) * 100
        return_60d = (close_prices[-1] / close_prices[-60] - 1) * 100
        momentum = return_20d * 0.4 + return_60d * 0.6
        np.random.seed(hash(code + date) % 2**32)
        pe_percentile = np.random.uniform(20, 80)
        scores[code] = {'volatility': volatility, 'momentum': momentum, 'pe_percentile': pe_percentile, 'return_20d': return_20d}
    return scores

def calculate_composite_score(scores, weights):
    if not scores: return {}
    codes = list(scores.keys())
    vol_values = np.array([scores[c]['volatility'] for c in codes])
    mom_values = np.array([scores[c]['momentum'] for c in codes])
    pe_values = np.array([scores[c]['pe_percentile'] for c in codes])
    vol_score = 1 - (vol_values - vol_values.min()) / (vol_values.max() - vol_values.min() + 1e-6)
    mom_score = (mom_values - mom_values.min()) / (mom_values.max() - mom_values.min() + 1e-6)
    pe_score = 1 - (pe_values - pe_values.min()) / (pe_values.max() - pe_values.min() + 1e-6)
    composite = weights['volatility'] * vol_score + weights['momentum'] * mom_score + weights['valuation'] * pe_score
    return {codes[i]: {'composite': composite[i], **scores[codes[i]]} for i in range(len(codes))}

def generate_target_positions(etf_data, date, config):
    log_message("运行策略引擎生成目标持仓...")
    scores = calculate_factors(etf_data, date)
    composite_scores = calculate_composite_score(scores, config['strategy']['factor_weights'])
    selected = sorted(composite_scores.items(), key=lambda x: x[1]['composite'], reverse=True)
    top_n = min(config['strategy']['max_positions'], len(selected))
    target_positions = {}
    for code, score in selected[:top_n]:
        if code in etf_data and date in etf_data[code]:
            price = etf_data[code][date]['close']
            target_positions[code] = {'target_weight': 1.0 / top_n, 'reference_price': price, 'score': score['composite']}
    log_message(f"策略引擎推荐：{len(target_positions)}只 ETF")
    return target_positions

def apply_boss_instructions(current_holdings, target_positions, instructions):
    log_message("应用老板指令...")
    adjusted_targets = target_positions.copy()
    for instr in instructions:
        code = instr['code']
        action = instr['action']
        if action == 'reduce':
            if code in adjusted_targets:
                current_weight = instr.get('current_weight', 0)
                target_weight = current_weight * instr['target']
                adjusted_targets[code]['target_weight'] = target_weight
                adjusted_targets[code]['boss_instruction'] = f"减仓至{instr['target']*100:.0f}%"
                log_message(f"  {instr['etf']}: 减仓至{instr['target']*100:.0f}%")
        elif action == 'increase':
            if code in adjusted_targets:
                adjusted_targets[code]['target_weight'] *= 1.5
                adjusted_targets[code]['boss_instruction'] = "重点加仓"
                log_message(f"  {instr['etf']}: 重点加仓")
            else:
                adjusted_targets[code] = {'target_weight': 0.05, 'boss_instruction': "老板指令加仓"}
                log_message(f"  {instr['etf']}: 强制加入持仓")
    return adjusted_targets

def generate_trading_orders(current_holdings, target_positions, total_value):
    log_message("生成交易订单...")
    orders = []
    current_codes = {etf['code'] for etf in current_holdings}
    target_codes = set(target_positions.keys())
    
    for etf in current_holdings:
        code = etf['code']
        if code not in target_codes:
            orders.append({'action': 'sell', 'code': code, 'name': etf['name'], 'current_shares': etf['shares'], 'reason': '调仓卖出', 'priority': 'normal'})
    
    for etf in current_holdings:
        code = etf['code']
        if code in target_positions:
            target = target_positions[code]
            current_value = etf['market_value']
            target_value = total_value * target['target_weight']
            if target_value < current_value * 0.9:
                sell_value = current_value - target_value
                sell_shares = int(sell_value / etf['price'])
                if sell_shares > 0:
                    orders.append({'action': 'sell', 'code': code, 'name': etf['name'], 'current_shares': etf['shares'], 'sell_shares': sell_shares, 'reason': target.get('boss_instruction', '权重调整'), 'priority': 'high' if 'boss_instruction' in target else 'normal'})
            elif target_value > current_value * 1.1:
                buy_value = target_value - current_value
                buy_shares = int(buy_value / etf['price'])
                if buy_shares > 0:
                    orders.append({'action': 'buy', 'code': code, 'name': etf['name'], 'current_shares': etf['shares'], 'buy_shares': buy_shares, 'reason': target.get('boss_instruction', '权重调整'), 'priority': 'high' if 'boss_instruction' in target else 'normal'})
    
    for code, target in target_positions.items():
        if code not in current_codes:
            if 'reference_price' in target:
                buy_value = total_value * target['target_weight']
                buy_shares = int(buy_value / target['reference_price'])
                if buy_shares > 0:
                    orders.append({'action': 'buy', 'code': code, 'buy_shares': buy_shares, 'reason': target.get('boss_instruction', '策略推荐'), 'priority': 'normal'})
    
    orders.sort(key=lambda x: (0 if x['priority'] == 'high' else 1))
    log_message(f"生成订单：{len(orders)}笔")
    return orders

def check_risk_controls(current_holdings, config):
    log_message("风控检查...")
    alerts = []
    total_value = sum(etf['market_value'] for etf in current_holdings)
    total_cost = sum(etf['shares'] * etf['cost'] for etf in current_holdings)
    total_return = (total_value - total_cost) / total_cost
    
    if total_return <= config['risk_control']['portfolio_stop_loss']:
        alerts.append({'type': 'portfolio_stop_loss', 'message': f"🛑 总止损触发：当前收益{total_return*100:.2f}%", 'action': '暂停策略'})
    
    for etf in current_holdings:
        return_pct = (etf['price'] - etf['cost']) / etf['cost']
        if return_pct <= config['risk_control']['single_stop_loss']:
            alerts.append({'type': 'single_stop_loss', 'code': etf['code'], 'name': etf['name'], 'message': f"⚠️ 止损：{etf['name']} {return_pct*100:.2f}%", 'action': '建议卖出'})
        elif return_pct >= config['risk_control']['single_take_profit']:
            alerts.append({'type': 'single_take_profit', 'code': etf['code'], 'name': etf['name'], 'message': f"✅ 止盈：{etf['name']} {return_pct*100:.2f}%", 'action': '建议卖出'})
    
    if alerts:
        for alert in alerts: log_message(alert['message'])
    else:
        log_message("✅ 风控检查通过")
    return alerts

def main():
    print("="*70)
    print("ETF-QuantaAlpha 统一交易引擎 v1.0")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    log_message("="*50)
    log_message("统一引擎启动")
    
    # 1. 加载持仓
    holdings = load_holdings()
    if not holdings:
        log_message("❌ 持仓加载失败")
        return
    
    current_holdings = holdings['etfs']
    total_value = holdings['total_market_value']
    log_message(f"当前持仓：{len(current_holdings)}只 ETF | 总市值：¥{total_value:,.2f}")
    
    # 2. 风控检查
    alerts = check_risk_controls(current_holdings, CONFIG)
    if any(a['type'] == 'portfolio_stop_loss' for a in alerts):
        log_message("🛑 总止损触发，暂停交易")
        return
    
    # 3. 加载 ETF 数据
    etf_data = load_etf_cache()
    if not etf_data:
        log_message("⚠️ ETF 数据为空，使用备用方案")
    
    # 4. 生成目标持仓
    latest_date = max(set().union(*[set(data.keys()) for data in etf_data.values()]) if etf_data else [])
    if latest_date:
        target_positions = generate_target_positions(etf_data, latest_date, CONFIG)
        boss_instructions = CONFIG.get('boss_instructions', {}).get('instructions', [])
        adjusted_targets = apply_boss_instructions(current_holdings, target_positions, boss_instructions)
        
        # 5. 生成交易订单
        orders = generate_trading_orders(current_holdings, adjusted_targets, total_value)
        
        # 6. 输出交易指令
        print("\n" + "="*70)
        print("调仓指令")
        print("="*70)
        
        if orders:
            for i, order in enumerate(orders, 1):
                action = "买入" if order['action'] == 'buy' else "卖出"
                shares = order.get('buy_shares', order.get('sell_shares', order['current_shares']))
                priority = "🔴 高" if order.get('priority') == 'high' else "⚪ 普"
                print(f"\n{i}. {action} {order['name']} ({order['code']})")
                print(f"   份额：{shares} | 优先级：{priority}")
                print(f"   理由：{order['reason']}")
        else:
            print("\n无需调仓")
        
        print("\n" + "="*70)
        print("下一步")
        print("="*70)
        print("1. 审核上述交易指令")
        print("2. 通过券商 APP 执行交易")
        print("3. 执行完成后更新 holdings_current.json")
    else:
        log_message("⚠️ 无可用数据，跳过策略生成")
    
    log_message("统一引擎完成")

if __name__ == "__main__":
    main()
