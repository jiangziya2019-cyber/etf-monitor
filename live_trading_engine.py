#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 实盘交易引擎
版本：v1.0 | 创建：2026-03-28

基于阶段 8 最优策略的实盘交易系统
"""

import sys, json, time, os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 实盘配置 ============

CONFIG = {
    'initial_capital': 1000000,  # 初始资金 100 万（可调整）
    'max_positions': 30,  # 最大持仓数
    'single_position_limit': 0.10,  # 单 ETF 上限 10%
    'rebalance_period': 30,  # 调仓周期 30 交易日
    'stop_loss': -0.08,  # 单 ETF 止损 -8%
    'take_profit': 0.20,  # 单 ETF 止盈 +20%
    'portfolio_stop_loss': -0.10,  # 总止损 -10%
    'transaction_cost': 0.001,  # 交易成本 0.1%
    'etf_pool_file': '/home/admin/openclaw/workspace/etf_pool_608.json',  # ETF 池
    'holdings_file': '/home/admin/openclaw/workspace/live_holdings.json',  # 持仓记录
    'log_file': '/home/admin/openclaw/workspace/live_trading.log',  # 日志
}

# 因子权重（阶段 8 最优）
FACTOR_WEIGHTS = (0.4, 0.35, 0.25)  # 波动 40% + 动量 35% + 估值 25%

def log_message(message):
    """日志记录"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def get_current_etf_pool():
    """获取当前 ETF 池（608 只）"""
    log_message("加载 ETF 池...")
    
    # 从缓存加载
    etf_codes = []
    cache_dir = '/home/admin/openclaw/workspace/etf_data_cache'
    if os.path.exists(cache_dir):
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                code = filename.replace('.json', '')
                etf_codes.append(code)
    
    log_message(f"ETF 池规模：{len(etf_codes)}只")
    return etf_codes

def get_latest_data(etf_codes):
    """获取最新行情数据"""
    log_message("获取最新行情...")
    
    import tushare as ts
    ts.set_token('7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75')
    pro = ts.pro_api()
    
    latest_data = {}
    today = datetime.now().strftime('%Y%m%d')
    
    for i, code in enumerate(etf_codes, 1):
        if i % 100 == 0:
            log_message(f"  进度 {i}/{len(etf_codes)}...")
        
        ts_code = f"{code}.SH" if code.startswith('51') else f"{code}.SZ"
        try:
            # 获取最近 60 日数据
            df = pro.fund_daily(ts_code=ts_code, start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'), end_date=today)
            
            if df is not None and len(df) > 0:
                latest_data[code] = {row['trade_date']: {'close': float(row.get('close', 0)), 'vol': float(row.get('vol', 0))} for _, row in df.iterrows()}
        except:
            pass
    
    log_message(f"成功获取 {len(latest_data)}/{len(etf_codes)}只 ETF 数据")
    return latest_data

def calculate_factors(latest_data, date):
    """计算多因子评分"""
    scores = {}
    for code, data in latest_data.items():
        if date not in data: continue
        close_prices = [data[d]['close'] for d in sorted(data.keys()) if d <= date]
        if len(close_prices) < 60: continue
        
        # 波动率因子
        returns = [close_prices[i]/close_prices[i-1] - 1 for i in range(-19, 0)]
        volatility = np.std(returns) * np.sqrt(252) * 100
        
        # 动量因子
        return_20d = (close_prices[-1] / close_prices[-20] - 1) * 100
        return_60d = (close_prices[-1] / close_prices[-60] - 1) * 100
        momentum = return_20d * 0.4 + return_60d * 0.6
        
        # 估值因子（模拟，实际应接入真实 PE/PB 数据）
        np.random.seed(hash(code + date) % 2**32)
        pe_percentile = np.random.uniform(20, 80)
        
        scores[code] = {
            'volatility': volatility,
            'momentum': momentum,
            'pe_percentile': pe_percentile,
            'return_20d': return_20d,
            'return_60d': return_60d
        }
    return scores

def calculate_composite_score(scores, weights):
    """计算综合评分"""
    if not scores: return {}
    
    codes = list(scores.keys())
    vol_values = np.array([scores[c]['volatility'] for c in codes])
    mom_values = np.array([scores[c]['momentum'] for c in codes])
    pe_values = np.array([scores[c]['pe_percentile'] for c in codes])
    
    # 归一化
    vol_score = 1 - (vol_values - vol_values.min()) / (vol_values.max() - vol_values.min() + 1e-6)
    mom_score = (mom_values - mom_values.min()) / (mom_values.max() - mom_values.min() + 1e-6)
    pe_score = 1 - (pe_values - pe_values.min()) / (pe_values.max() - pe_values.min() + 1e-6)
    
    # 加权
    w_vol, w_mom, w_pe = weights
    composite = w_vol * vol_score + w_mom * mom_score + w_pe * pe_score
    
    return {codes[i]: {'composite': composite[i], **scores[codes[i]]} for i in range(len(codes))}

def generate_target_positions(latest_data, date, current_holdings, capital):
    """生成目标持仓"""
    log_message("生成目标持仓...")
    
    scores = calculate_factors(latest_data, date)
    composite_scores = calculate_composite_score(scores, FACTOR_WEIGHTS)
    
    # 选择综合评分最高的 ETF
    selected = sorted(composite_scores.items(), key=lambda x: x[1]['composite'], reverse=True)[:CONFIG['max_positions']]
    
    # 计算目标仓位
    target_positions = {}
    alloc_per_etf = capital / len(selected)
    
    for code, score in selected:
        if code in latest_data and date in latest_data[code]:
            price = latest_data[code][date]['close']
            target_shares = int((alloc_per_etf * (1 - CONFIG['transaction_cost'])) / price)
            if target_shares > 0:
                target_positions[code] = {
                    'shares': target_shares,
                    'target_price': price,
                    'weight': 1.0 / len(selected)
                }
    
    log_message(f"目标持仓：{len(target_positions)}只 ETF")
    return target_positions

def check_risk_controls(current_holdings, latest_data, date, total_capital):
    """风控检查"""
    log_message("风控检查...")
    
    alerts = []
    
    # 1. 总止损检查
    total_value = sum(pos['shares'] * latest_data[pos['code']][date]['close'] for pos in current_holdings if pos['code'] in latest_data and date in latest_data[pos['code']])
    total_return = (total_value - CONFIG['initial_capital']) / CONFIG['initial_capital']
    
    if total_return <= CONFIG['portfolio_stop_loss']:
        alerts.append(f"⚠️ 总止损触发：当前收益{total_return*100:.2f}% < {CONFIG['portfolio_stop_loss']*100}%")
        alerts.append("🛑 建议：暂停策略，清仓观望")
    
    # 2. 单个 ETF 止损/止盈检查
    for pos in current_holdings:
        code = pos['code']
        if code not in latest_data or date not in latest_data[code]:
            continue
        
        current_price = latest_data[code][date]['close']
        buy_price = pos['buy_price']
        return_pct = (current_price - buy_price) / buy_price
        
        if return_pct <= CONFIG['stop_loss']:
            alerts.append(f"⚠️ 止损触发：{code} 收益{return_pct*100:.2f}% < {CONFIG['stop_loss']*100}%")
        elif return_pct >= CONFIG['take_profit']:
            alerts.append(f"✅ 止盈触发：{code} 收益{return_pct*100:.2f}% > {CONFIG['take_profit']*100}%")
    
    # 3. 仓位集中度检查
    if total_value > 0:
        for pos in current_holdings:
            code = pos['code']
            if code not in latest_data or date not in latest_data[code]:
                continue
            value = pos['shares'] * latest_data[code][date]['close']
            weight = value / total_value
            if weight > CONFIG['single_position_limit'] * 1.2:  # 允许 20% 超调
                alerts.append(f"⚠️ 仓位超限：{code} 权重{weight*100:.2f}% > {CONFIG['single_position_limit']*100*1.2:.0f}%")
    
    if alerts:
        for alert in alerts:
            log_message(alert)
    else:
        log_message("✅ 风控检查通过")
    
    return alerts

def generate_trading_orders(current_holdings, target_positions, latest_data, date):
    """生成交易订单"""
    log_message("生成交易订单...")
    
    orders = []
    
    # 1. 卖出订单（不在目标持仓中的）
    current_codes = {pos['code'] for pos in current_holdings}
    target_codes = set(target_positions.keys())
    
    for pos in current_holdings:
        code = pos['code']
        if code not in target_codes:
            if code in latest_data and date in latest_data[code]:
                price = latest_data[code][date]['close']
                orders.append({
                    'action': 'sell',
                    'code': code,
                    'shares': pos['shares'],
                    'reason': '调仓卖出',
                    'reference_price': price
                })
    
    # 2. 买入订单（目标持仓中但当前没有的）
    for code, target in target_positions.items():
        if code not in current_codes:
            if code in latest_data and date in latest_data[code]:
                price = latest_data[code][date]['close']
                orders.append({
                    'action': 'buy',
                    'code': code,
                    'shares': target['shares'],
                    'reason': '调仓买入',
                    'reference_price': price,
                    'target_weight': target['weight']
                })
    
    log_message(f"生成订单：{len(orders)}笔（买入{sum(1 for o in orders if o['action']=='buy')}笔，卖出{sum(1 for o in orders if o['action']=='sell')}笔）")
    return orders

def save_holdings(holdings, capital):
    """保存持仓记录"""
    holdings_data = {
        'timestamp': datetime.now().isoformat(),
        'capital': capital,
        'holdings': holdings
    }
    
    with open(CONFIG['holdings_file'], 'w', encoding='utf-8') as f:
        json.dump(holdings_data, f, ensure_ascii=False, indent=2)
    
    log_message(f"持仓已保存：{CONFIG['holdings_file']}")

def load_holdings():
    """加载持仓记录"""
    if not os.path.exists(CONFIG['holdings_file']):
        return [], CONFIG['initial_capital']
    
    with open(CONFIG['holdings_file'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log_message(f"持仓已加载：{len(data.get('holdings', []))}只 ETF")
    return data.get('holdings', []), data.get('capital', CONFIG['initial_capital'])

def main():
    """实盘引擎主流程"""
    print("="*70)
    print("ETF-QuantaAlpha 实盘交易引擎 v1.0")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    log_message("="*50)
    log_message("实盘引擎启动")
    
    # 1. 加载 ETF 池
    etf_codes = get_current_etf_pool()
    if not etf_codes:
        log_message("❌ ETF 池加载失败")
        return
    
    # 2. 获取最新数据
    latest_data = get_latest_data(etf_codes)
    if not latest_data:
        log_message("❌ 行情数据获取失败")
        return
    
    # 3. 获取最新交易日
    latest_date = sorted(set().union(*[set(data.keys()) for data in latest_data.values()]))[-1]
    log_message(f"最新交易日：{latest_date}")
    
    # 4. 加载当前持仓
    current_holdings, capital = load_holdings()
    log_message(f"当前资金：¥{capital:,.2f}")
    log_message(f"当前持仓：{len(current_holdings)}只 ETF")
    
    # 5. 风控检查
    alerts = check_risk_controls(current_holdings, latest_data, latest_date, capital)
    
    # 如果有总止损触发，暂停交易
    if any("总止损触发" in alert for alert in alerts):
        log_message("🛑 总止损触发，暂停交易")
        return
    
    # 6. 生成目标持仓
    target_positions = generate_target_positions(latest_data, latest_date, current_holdings, capital)
    
    # 7. 生成交易订单
    orders = generate_trading_orders(current_holdings, target_positions, latest_data, latest_date)
    
    # 8. 输出交易指令
    print("\n" + "="*70)
    print("交易指令")
    print("="*70)
    
    if orders:
        for i, order in enumerate(orders, 1):
            action = "买入" if order['action'] == 'buy' else "卖出"
            print(f"\n{i}. {action} {order['code']}")
            print(f"   数量：{order['shares']}股")
            print(f"   参考价：¥{order['reference_price']:.3f}")
            if order['action'] == 'buy':
                print(f"   目标权重：{order['target_weight']*100:.1f}%")
            print(f"   原因：{order['reason']}")
    else:
        print("\n无需调仓")
    
    # 9. 保存持仓
    # 注意：实盘执行后需要手动更新持仓文件
    log_message("⚠️ 请执行交易后手动更新持仓记录")
    
    print("\n" + "="*70)
    print("下一步操作")
    print("="*70)
    print("1. 审核上述交易指令")
    print("2. 通过券商 APP 执行交易")
    print("3. 执行完成后更新持仓记录")
    print("4. 运行监控脚本跟踪净值")
    
    log_message("实盘引擎完成")

if __name__ == "__main__":
    main()
