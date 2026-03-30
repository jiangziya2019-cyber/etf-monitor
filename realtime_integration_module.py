#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据整合模块 v1.0
版本：v1.0 | 创建：2026-03-28 14:05

功能:
  - 整合 Tushare 实时日线 + 分钟数据
  - 自动降级机制
  - 用于监控系统和第三层策略
"""

import sys, json, os, time
from datetime import datetime, timedelta
from typing import Dict, List

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
LOG_FILE = '/home/admin/openclaw/workspace/realtime_integration.log'
CACHE_DIR = '/home/admin/openclaw/workspace/realtime_data_cache'
CACHE_TTL_SECONDS = 180

ALL_32_ETFS = [
    '510880', '159399', '510300', '510500', '510180',
    '515790', '159566', '512480', '159819', '512010', '159663', '562500', '159227',
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200',
    '513110', '513500', '159937', '160723', '513130'
]

LAYER3_12_ETFS = [
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200'
]

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def is_trading_time() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    morning = now.replace(hour=9, minute=30, second=0) <= now <= now.replace(hour=11, minute=30, second=0)
    afternoon = now.replace(hour=13, minute=0, second=0) <= now <= now.replace(hour=15, minute=0, second=0)
    return morning or afternoon

def get_realtime_data(etf_codes: List[str], use_cache: bool = True) -> Dict:
    if use_cache:
        cache_file = f"{CACHE_DIR}/realtime_latest.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                cache_time = datetime.fromisoformat(cached_data.get('update_time', '2000-01-01'))
                age_seconds = (datetime.now() - cache_time).total_seconds()
                if age_seconds < CACHE_TTL_SECONDS:
                    log_message(f"✅ 使用缓存数据 ({age_seconds:.0f}秒前)")
                    cached_data['cache_hit'] = True
                    return cached_data
            except:
                pass
    
    if is_trading_time():
        log_message("获取实时数据...")
        try:
            realtime_data = fetch_realtime_daily(etf_codes)
            if realtime_data and len(realtime_data) > 0:
                save_cache(realtime_data)
                log_message(f"✅ 获取 {len(realtime_data)}只 ETF 实时数据")
                return realtime_data
        except Exception as e:
            log_message(f"⚠️ 实时数据获取失败：{e}")
    
    log_message("降级到日线数据...")
    try:
        daily_data = fetch_daily_data(etf_codes)
        if daily_data:
            log_message(f"✅ 获取 {len(daily_data)}只 ETF 日线数据")
            return daily_data
    except Exception as e:
        log_message(f"⚠️ 日线数据获取失败：{e}")
    
    log_message("使用过期缓存...")
    cache_file = f"{CACHE_DIR}/realtime_latest.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def fetch_realtime_daily(etf_codes: List[str]) -> Dict:
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    results = {}
    
    sh_codes = [code + '.SH' for code in etf_codes if code.startswith('5')]
    if sh_codes:
        try:
            df = pro.rt_etf_k(ts_code='5*.SH', topic='HQ_FND_TICK')
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    ts_code = row.get('ts_code', '')
                    code = ts_code.split('.')[0]
                    if code in etf_codes:
                        results[code] = {
                            'code': code,
                            'name': row.get('name', ''),
                            'pre_close': float(row.get('pre_close', 0)),
                            'open': float(row.get('open', 0)),
                            'high': float(row.get('high', 0)),
                            'low': float(row.get('low', 0)),
                            'close': float(row.get('close', 0)),
                            'vol': int(row.get('vol', 0)),
                            'amount': int(row.get('amount', 0)),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
        except Exception as e:
            log_message(f"⚠️ 沪市实时数据失败：{e}")
    
    sz_codes = [code + '.SZ' for code in etf_codes if code.startswith('1')]
    if sz_codes:
        try:
            df = pro.rt_etf_k(ts_code='1*.SZ')
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    ts_code = row.get('ts_code', '')
                    code = ts_code.split('.')[0]
                    if code in etf_codes:
                        results[code] = {
                            'code': code,
                            'name': row.get('name', ''),
                            'pre_close': float(row.get('pre_close', 0)),
                            'open': float(row.get('open', 0)),
                            'high': float(row.get('high', 0)),
                            'low': float(row.get('low', 0)),
                            'close': float(row.get('close', 0)),
                            'vol': int(row.get('vol', 0)),
                            'amount': int(row.get('amount', 0)),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
        except Exception as e:
            log_message(f"⚠️ 深市实时数据失败：{e}")
    
    return results

def fetch_daily_data(etf_codes: List[str]) -> Dict:
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    results = {}
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
    
    for code in etf_codes:
        ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
        try:
            df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                results[code] = {
                    'code': code,
                    'close': float(latest.get('close', 0)),
                    'pre_close': float(latest.get('pre_close', 0)),
                    'vol': float(latest.get('vol', 0)),
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'tushare_fund_daily'
                }
        except:
            pass
        time.sleep(0.05)
    return results

def save_cache(data: Dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(f"{CACHE_DIR}/realtime_latest.json", 'w') as f:
        json.dump(data, f, indent=2)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f"{CACHE_DIR}/realtime_{timestamp}.json", 'w') as f:
        json.dump(data, f, indent=2)

def calculate_metrics(realtime_data: Dict, holdings: Dict = None) -> Dict:
    metrics = {'update_time': datetime.now().isoformat(), 'etf_count': len(realtime_data), 'etfs': []}
    total_market_value = 0
    total_profit = 0
    
    for code, data in realtime_data.items():
        close = data.get('close', 0)
        pre_close = data.get('pre_close', 1)
        change_pct = ((close - pre_close) / pre_close * 100) if pre_close > 0 else 0
        etf_metric = {'code': code, 'name': data.get('name', ''), 'close': close, 'change_pct': round(change_pct, 2), 'vol': data.get('vol', 0)}
        
        if holdings:
            for etf in holdings.get('holdings', []):
                if etf.get('code') == code:
                    shares = etf.get('shares', 0)
                    cost = etf.get('cost_price', 0)
                    market_value = shares * close
                    profit = market_value - (shares * cost)
                    etf_metric['market_value'] = round(market_value, 2)
                    etf_metric['profit'] = round(profit, 2)
                    etf_metric['profit_pct'] = round((profit / (shares * cost) * 100) if cost > 0 else 0, 2)
                    total_market_value += market_value
                    total_profit += profit
        metrics['etfs'].append(etf_metric)
    
    metrics['total_market_value'] = round(total_market_value, 2)
    metrics['total_profit'] = round(total_profit, 2)
    return metrics

def check_triggers(realtime_data: Dict, holdings: Dict) -> List[Dict]:
    triggers = []
    for etf in holdings.get('holdings', []):
        code = etf.get('code')
        if code not in realtime_data:
            continue
        data = realtime_data[code]
        close = data.get('close', 0)
        cost = etf.get('cost_price', 0)
        if cost > 0:
            profit_pct = (close - cost) / cost * 100
            if profit_pct <= -5.0:
                triggers.append({'type': 'stop_loss', 'code': code, 'name': etf.get('name', ''), 'profit_pct': round(profit_pct, 2), 'action': '建议卖出', 'level': 'layer3' if code in LAYER3_12_ETFS else 'other'})
            elif profit_pct >= 10.0:
                triggers.append({'type': 'take_profit_1', 'code': code, 'name': etf.get('name', ''), 'profit_pct': round(profit_pct, 2), 'action': '建议减半', 'level': 'layer3' if code in LAYER3_12_ETFS else 'other'})
            elif profit_pct >= 20.0:
                triggers.append({'type': 'take_profit_2', 'code': code, 'name': etf.get('name', ''), 'profit_pct': round(profit_pct, 2), 'action': '建议清仓', 'level': 'layer3' if code in LAYER3_12_ETFS else 'other'})
    return triggers

if __name__ == "__main__":
    print("="*70)
    print("实时数据整合模块 v1.0 测试")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    log_message("获取 32 只 ETF 实时数据...")
    realtime_data = get_realtime_data(ALL_32_ETFS)
    print(f"\n✅ 获取 {len(realtime_data)}只 ETF 数据")
    
    holdings_file = '/home/admin/openclaw/workspace/holdings_current.json'
    holdings = {}
    if os.path.exists(holdings_file):
        with open(holdings_file, 'r') as f:
            holdings = json.load(f)
    
    metrics = calculate_metrics(realtime_data, holdings)
    print(f"\n📊 总市值：¥{metrics.get('total_market_value', 0):,.2f}")
    print(f"📊 总盈亏：¥{metrics.get('total_profit', 0):,.2f}")
    
    triggers = check_triggers(realtime_data, holdings)
    if triggers:
        print(f"\n⚠️ 触发 {len(triggers)}个预警")
        for t in triggers:
            print(f"  {t['type']}: {t['code']} {t['profit_pct']:.2f}% - {t['action']}")
    else:
        print(f"\n✅ 无触发预警")
    
    print(f"\n💾 缓存：{CACHE_DIR}/realtime_latest.json")
