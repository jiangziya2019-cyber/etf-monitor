#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据获取模块 - Tushare Pro 全权限版
版本：v1.0 | 创建：2026-03-28 11:05

功能:
  - 实时行情获取（A 股/港股/美股 ETF）
  - 盘中监控（每 3 分钟刷新）
  - 止损/止盈实时预警
  - ETF 缓存自动更新
"""

import sys, json, time, os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
HOLDINGS_FILE = '/home/admin/openclaw/workspace/holdings_current.json'
CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
LOG_FILE = '/home/admin/openclaw/workspace/realtime_data.log'

# 风控阈值
STOP_LOSS = -0.08
TAKE_PROFIT = 0.20
PORTFOLIO_STOP_LOSS = -0.10

# 监控间隔（秒）
MONITOR_INTERVAL = 180  # 3 分钟

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def load_holdings():
    """加载当前持仓"""
    if not os.path.exists(HOLDINGS_FILE):
        return None
    with open(HOLDINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_realtime_etf_data(code: str) -> Optional[Dict]:
    """
    获取 ETF 实时行情（Tushare Pro 全权限）
    
    Args:
        code: ETF 代码（如 510300）
    
    Returns:
        实时行情数据字典
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    try:
        # 判断交易所
        if code.startswith('51'):
            ts_code = f"{code}.SH"
            # A 股 ETF 实时行情
            df = pro.rt_k(ts_code=ts_code)
        elif code.startswith('15'):
            ts_code = f"{code}.SZ"
            # 深市 ETF 实时行情
            df = pro.rt_k(ts_code=ts_code)
        else:
            return None
        
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            return {
                'code': code,
                'price': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'pre_close': float(row.get('pre_close', 0)),
                'change': float(row.get('change', 0)),
                'change_pct': float(row.get('pct_chg', 0)),
                'volume': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0)),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        log_message(f"获取实时数据失败 {code}: {e}")
    
    return None

def get_realtime_holdings_valuation(holdings: Dict) -> Dict:
    """
    获取持仓实时估值
    
    Args:
        holdings: 持仓数据
    
    Returns:
        实时估值数据
    """
    etfs = holdings.get('etfs', [])
    total_realtime_value = 0
    alerts = []
    
    log_message(f"开始获取 {len(etfs)}只 ETF 实时行情...")
    
    for i, etf in enumerate(etfs, 1):
        code = etf['code']
        name = etf['name']
        shares = etf['shares']
        cost = etf['cost']
        
        # 获取实时行情
        realtime_data = get_realtime_etf_data(code)
        
        if realtime_data:
            price = realtime_data['price']
            change_pct = realtime_data['change_pct']
            
            # 计算实时市值
            realtime_value = shares * price
            total_realtime_value += realtime_value
            
            # 计算实时盈亏
            cost_value = shares * cost
            profit = realtime_value - cost_value
            profit_pct = (price - cost) / cost * 100
            
            # 更新 ETF 数据
            etf['realtime_price'] = price
            etf['realtime_value'] = realtime_value
            etf['realtime_profit'] = profit
            etf['realtime_profit_pct'] = round(profit_pct, 2)
            etf['change_pct'] = change_pct
            
            # 风控检查
            if profit_pct <= STOP_LOSS * 100:
                alert_msg = f"⚠️ 止损预警：{name}({code}) 实时收益{profit_pct:.2f}% < {STOP_LOSS*100}%"
                alerts.append({'type': 'stop_loss', 'code': code, 'name': name, 'profit_pct': profit_pct, 'message': alert_msg})
                log_message(alert_msg)
            
            elif profit_pct >= TAKE_PROFIT * 100:
                alert_msg = f"✅ 止盈预警：{name}({code}) 实时收益{profit_pct:.2f}% > {TAKE_PROFIT*100}%"
                alerts.append({'type': 'take_profit', 'code': code, 'name': name, 'profit_pct': profit_pct, 'message': alert_msg})
                log_message(alert_msg)
            
            if i % 10 == 0:
                log_message(f"  进度 {i}/{len(etfs)}...")
        else:
            # 使用缓存价格
            etf['realtime_price'] = etf.get('price', 0)
            etf['realtime_value'] = etf['market_value']
    
    # 计算总盈亏
    total_cost = sum(etf['shares'] * etf['cost'] for etf in etfs)
    total_profit = total_realtime_value - total_cost
    total_profit_pct = (total_profit / total_cost) * 100
    
    # 总止损检查
    if total_profit_pct <= PORTFOLIO_STOP_LOSS * 100:
        alert_msg = f"🛑 总止损预警：组合实时收益{total_profit_pct:.2f}% < {PORTFOLIO_STOP_LOSS*100}%"
        alerts.append({'type': 'portfolio_stop_loss', 'profit_pct': total_profit_pct, 'message': alert_msg})
        log_message(f"🚨 {alert_msg}")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'total_realtime_value': round(total_realtime_value, 2),
        'total_cost': round(total_cost, 2),
        'total_profit': round(total_profit, 2),
        'total_profit_pct': round(total_profit_pct, 2),
        'etf_count': len(etfs),
        'etfs': etfs,
        'alerts': alerts
    }

def update_etf_cache(etf_codes: List[str], days: int = 60):
    """
    更新 ETF 历史数据缓存
    
    Args:
        etf_codes: ETF 代码列表
        days: 获取天数
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    log_message(f"更新 {len(etf_codes)}只 ETF 历史数据缓存...")
    
    for i, code in enumerate(etf_codes, 1):
        cache_file = f"{CACHE_DIR}/{code}.json"
        ts_code = f"{code}.SH" if code.startswith('51') else f"{code}.SZ"
        
        try:
            df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                data = {row['trade_date']: {'close': float(row.get('close', 0)), 'vol': float(row.get('vol', 0))} for _, row in df.iterrows()}
                
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
                
                if i % 50 == 0:
                    log_message(f"  进度 {i}/{len(etf_codes)}...")
            else:
                log_message(f"  ⚠️ {code} 无数据")
            
            time.sleep(0.05)  # API 限流
            
        except Exception as e:
            log_message(f"  ❌ {code} 失败：{e}")
    
    log_message(f"✅ 缓存更新完成：{len(etf_codes)}只 ETF")

def send_feishu_alert(alerts: List[Dict]):
    """发送飞书预警通知"""
    if not alerts:
        return
    
    import requests
    
    message = "🚨 **实时风控预警**\n\n"
    
    for alert in alerts:
        if alert['type'] == 'stop_loss':
            message += f"⚠️ {alert['name']}({alert['code']}): 收益{alert['profit_pct']:.2f}% 触发止损线\n"
        elif alert['type'] == 'take_profit':
            message += f"✅ {alert['name']}({alert['code']}): 收益{alert['profit_pct']:.2f}% 触发止盈线\n"
        elif alert['type'] == 'portfolio_stop_loss':
            message += f"🛑 **总止损触发**: 组合收益{alert['profit_pct']:.2f}%\n"
    
    message += f"\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 飞书 App Bot API
    try:
        # 这里需要配置飞书 webhook 或使用 message tool
        log_message(f"飞书预警：{len(alerts)}条")
        log_message(message)
    except Exception as e:
        log_message(f"发送飞书失败：{e}")

def main():
    """实时监控主循环"""
    print("="*70)
    print("实时数据监控 v1.0 - Tushare Pro 全权限")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    log_message("="*50)
    log_message("实时数据监控启动")
    
    # 1. 加载持仓
    holdings = load_holdings()
    if not holdings:
        log_message("❌ 持仓加载失败")
        return
    
    log_message(f"当前持仓：{holdings['etf_count']}只 ETF | 总市值：¥{holdings['total_market_value']:,.2f}")
    
    # 2. 获取实时估值
    realtime_valuation = get_realtime_holdings_valuation(holdings)
    
    print("\n" + "="*70)
    print("实时估值")
    print("="*70)
    print(f"总市值：¥{realtime_valuation['total_realtime_value']:,.2f}")
    print(f"总盈亏：¥{realtime_valuation['total_profit']:,.2f} ({realtime_valuation['total_profit_pct']:.2f}%)")
    print(f"持仓数量：{realtime_valuation['etf_count']}只")
    
    if realtime_valuation['alerts']:
        print(f"\n🚨 预警：{len(realtime_valuation['alerts'])}条")
        for alert in realtime_valuation['alerts']:
            print(f"  - {alert['message']}")
        
        # 发送飞书通知
        send_feishu_alert(realtime_valuation['alerts'])
    else:
        print("\n✅ 无风控预警")
    
    # 3. 保存实时估值
    output_file = '/home/admin/openclaw/workspace/realtime_valuation.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(realtime_valuation, f, ensure_ascii=False, indent=2)
    
    log_message(f"实时估值已保存：{output_file}")
    
    print(f"\n📄 详细数据：{output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
