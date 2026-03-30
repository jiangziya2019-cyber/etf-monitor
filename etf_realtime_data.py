#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 实时数据获取模块 - 使用 Tushare 实时接口
版本：v1.0 | 创建：2026-03-28 14:03

功能:
  - rt_etf_k: ETF 实时日线行情
  - rt_min: ETF 实时分钟数据（1/5/15/30/60MIN）
  - 用于第三层日频策略和实时监控

接口文档:
  - 实时日线：https://tushare.pro/document/2?doc_id=400
  - 实时分钟：https://tushare.pro/document/2?doc_id=416
"""

import sys, json, os, time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
LOG_FILE = '/home/admin/openclaw/workspace/etf_realtime.log'
REALTIME_CACHE = '/home/admin/openclaw/workspace/realtime_data_cache'
CACHE_TTL_SECONDS = 180  # 3 分钟缓存（用于实时监控）

# 第三层 12 只高频 ETF
LAYER3_ETFS = [
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200'
]

# 全部 32 只 ETF
ALL_ETFS = [
    '510880', '159399', '510300', '510500', '510180',
    '515790', '159566', '512480', '159819', '512010', '159663', '562500', '159227',
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200',
    '513110', '513500', '159937', '160723', '513130'
]

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def get_etf_realtime_daily(etf_codes: List[str]) -> Dict:
    """
    获取 ETF 实时日线数据
    
    接口：rt_etf_k
    权限：需单独申请
    
    Args:
        etf_codes: ETF 代码列表（带后缀）
    
    Returns:
        实时日线数据
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    results = {}
    
    # 分组：沪市（5*.SH）和深市（1*.SZ）
    sh_etfs = [code + '.SH' for code in etf_codes if code.startswith('5')]
    sz_etfs = [code + '.SZ' for code in etf_codes if code.startswith('1')]
    
    # 获取沪市 ETF 实时数据
    if sh_etfs:
        try:
            ts_code_pattern = '5*.SH'  # 获取全部沪市 ETF
            df = pro.rt_etf_k(ts_code=ts_code_pattern, topic='HQ_FND_TICK')
            
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
                            'num': int(row.get('num', 0)),
                            'trade_time': row.get('trade_time', ''),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
                log_message(f"✅ 获取沪市 {len([k for k in results if k.startswith('5')])}只 ETF 实时数据")
        except Exception as e:
            log_message(f"⚠️ 获取沪市 ETF 实时数据失败：{e}")
    
    # 获取深市 ETF 实时数据
    if sz_etfs:
        try:
            ts_code_pattern = '1*.SZ'  # 获取全部深市 ETF
            df = pro.rt_etf_k(ts_code=ts_code_pattern)
            
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
                            'num': int(row.get('num', 0)),
                            'trade_time': row.get('trade_time', ''),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
                log_message(f"✅ 获取深市 {len([k for k in results if k.startswith('1')])}只 ETF 实时数据")
        except Exception as e:
            log_message(f"⚠️ 获取深市 ETF 实时数据失败：{e}")
    
    return results

def get_etf_realtime_minute(etf_codes: List[str], freq: str = '5MIN') -> Dict:
    """
    获取 ETF 实时分钟数据
    
    接口：rt_min
    权限：正式权限
    
    Args:
        etf_codes: ETF 代码列表
        freq: 频率（1MIN/5MIN/15MIN/30MIN/60MIN）
    
    Returns:
        分钟数据
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    results = {}
    
    for code in etf_codes:
        if code.startswith('5'):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        try:
            df = pro.rt_min(ts_code=ts_code, freq=freq)
            
            if df is not None and len(df) > 0:
                minutes_data = []
                for _, row in df.iterrows():
                    minutes_data.append({
                        'time': row.get('time', ''),
                        'open': float(row.get('open', 0)),
                        'close': float(row.get('close', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'vol': float(row.get('vol', 0)),
                        'amount': float(row.get('amount', 0))
                    })
                
                results[code] = {
                    'code': code,
                    'freq': freq,
                    'data': minutes_data,
                    'count': len(minutes_data),
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'tushare_rt_min'
                }
        except Exception as e:
            log_message(f"⚠️ 获取 {code} 分钟数据失败：{e}")
        
        time.sleep(0.1)  # 避免限流
    
    return results

def calculate_realtime_metrics(realtime_data: Dict, holdings: Dict = None) -> Dict:
    """
    计算实时指标
    
    Args:
        realtime_data: 实时数据
        holdings: 持仓数据
    
    Returns:
        实时指标
    """
    metrics = {
        'update_time': datetime.now().isoformat(),
        'etf_count': len(realtime_data),
        'etfs': []
    }
    
    total_market_value = 0
    total_profit = 0
    
    for code, data in realtime_data.items():
        close_price = data.get('close', 0)
        pre_close = data.get('pre_close', 1)
        
        # 计算涨跌幅
        change_pct = ((close_price - pre_close) / pre_close * 100) if pre_close > 0 else 0
        
        etf_metric = {
            'code': code,
            'name': data.get('name', ''),
            'close': close_price,
            'change_pct': round(change_pct, 2),
            'vol': data.get('vol', 0),
            'amount': data.get('amount', 0)
        }
        
        # 如果有持仓，计算盈亏
        if holdings:
            for etf in holdings.get('holdings', []):
                if etf.get('code') == code:
                    shares = etf.get('shares', 0)
                    cost_price = etf.get('cost_price', 0)
                    market_value = shares * close_price
                    cost_value = shares * cost_price
                    profit = market_value - cost_value
                    profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
                    
                    etf_metric['shares'] = shares
                    etf_metric['market_value'] = round(market_value, 2)
                    etf_metric['profit'] = round(profit, 2)
                    etf_metric['profit_pct'] = round(profit_pct, 2)
                    
                    total_market_value += market_value
                    total_profit += profit
        
        metrics['etfs'].append(etf_metric)
    
    metrics['total_market_value'] = round(total_market_value, 2)
    metrics['total_profit'] = round(total_profit, 2)
    metrics['total_profit_pct'] = round((total_profit / (total_market_value - total_profit) * 100) if (total_market_value - total_profit) > 0 else 0, 2)
    
    return metrics

def save_realtime_data(data: Dict, filename: str = 'realtime_valuation.json'):
    """保存实时数据"""
    os.makedirs(REALTIME_CACHE, exist_ok=True)
    output_file = f"{REALTIME_CACHE}/{filename}"
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_message(f"💾 已保存到 {output_file}")

def main():
    """主函数"""
    print("="*70)
    print("ETF 实时数据获取模块 v1.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 获取实时日线数据
    log_message("获取 ETF 实时日线数据...")
    realtime_daily = get_etf_realtime_daily(ALL_ETFS)
    
    print(f"\n✅ 获取 {len(realtime_daily)}只 ETF 实时日线数据")
    
    if realtime_daily:
        print("\n实时数据示例:")
        for code, data in list(realtime_daily.items())[:5]:
            change = ((data['close'] - data['pre_close']) / data['pre_close'] * 100) if data['pre_close'] > 0 else 0
            print(f"{code}({data['name']}): {data['close']:.3f} ({change:+.2f}%) 成交:{data['vol']}手")
    
    # 2. 保存实时数据
    save_realtime_data({
        'update_time': datetime.now().isoformat(),
        'data_type': 'realtime_daily',
        'etf_count': len(realtime_daily),
        'data': realtime_daily
    })
    
    # 3. 测试分钟数据（仅第三层 ETF）
    log_message(f"\n获取第三层 {len(LAYER3_ETFS)}只 ETF 5 分钟数据...")
    realtime_min = get_etf_realtime_minute(LAYER3_ETFS[:3], freq='5MIN')  # 测试前 3 只
    
    print(f"✅ 获取 {len(realtime_min)}只 ETF 分钟数据")
    for code, data in realtime_min.items():
        print(f"  {code}: {data['count']}条 {data['freq']} 数据")
    
    print("\n" + "="*70)
    print("实时数据获取完成！")
    print(f"📄 缓存目录：{REALTIME_CACHE}")
    print(f"💾 实时数据：{REALTIME_CACHE}/realtime_valuation.json")

if __name__ == "__main__":
    main()
