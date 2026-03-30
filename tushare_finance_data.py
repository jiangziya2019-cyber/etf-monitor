#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 数据获取模块 - 完整版
版本：v3.0 | 创建：2026-03-27 | 更新：2026-03-28 14:45

功能:
  - ETF 基础信息 (etf_basic)
  - ETF 实时日线 (rt_etf_k)
  - ETF 实时分钟 (rt_min)
  - ETF 份额规模 (etf_share_size)
  - 指数实时日线 (rt_idx_k)
  - 指数实时分钟 (rt_idx_min)
  - 指数技术因子 (idx_techfactor)
  - 全球指数 (index_global)
  - 新闻快讯 (news)
  - A 股/港股/美股 ETF 日线
  - 估值数据 (index_dailybasic)

接口文档汇总:
  - ETF 基础：https://tushare.pro/document/2?doc_id=385
  - ETF 实时日线：https://tushare.pro/document/2?doc_id=400
  - ETF 实时分钟：https://tushare.pro/document/2?doc_id=416
  - ETF 份额规模：https://tushare.pro/document/2?doc_id=408
  - 指数实时日线：https://tushare.pro/document/2?doc_id=403
  - 指数实时分钟：https://tushare.pro/document/2?doc_id=420
  - 指数技术因子：https://tushare.pro/document/2?doc_id=358
  - 全球指数：https://tushare.pro/document/2?doc_id=211
  - 新闻快讯：https://tushare.pro/document/2?doc_id=143
"""

import sys, json, os, time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
LOG_FILE = '/home/admin/openclaw/workspace/tushare_data.log'
CACHE_DIR = '/home/admin/openclaw/workspace/tushare_cache'
CACHE_TTL_SECONDS = 300  # 5 分钟缓存

# ETF 列表
ALL_32_ETFS = [
    '510880', '159399', '510300', '510500', '510180',
    '515790', '159566', '512480', '159819', '512010', '159663', '562500', '159227',
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200',
    '513110', '513500', '159937', '160723', '513130'
]

# 指数代码
INDEX_CODES = {
    '沪深 300': '000300.SH',
    '中证 500': '000905.SH',
    '上证 180': '000040.SH',
    '创业板指': '399006.SZ',
    '恒生指数': 'HSI',
    '纳斯达克': 'IXIC',
    '标普 500': 'SPX',
    '道琼斯': 'DJI',
}

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def get_pro():
    """获取 Tushare Pro API 实例"""
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    return ts.pro_api()

# ============ ETF 基础信息 ============

def get_etf_basic(etf_codes: List[str] = None) -> Dict:
    """
    获取 ETF 基础信息
    
    接口：etf_basic
    文档：https://tushare.pro/document/2?doc_id=385
    权限：8000 积分
    
    Args:
        etf_codes: ETF 代码列表（可选）
    
    Returns:
        ETF 基础信息
    """
    pro = get_pro()
    
    try:
        if etf_codes:
            # 获取指定 ETF
            results = {}
            for code in etf_codes:
                ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
                df = pro.etf_basic(ts_code=ts_code, fields='ts_code,csname,index_code,index_name,exchange,etf_type,setup_date,list_date,mgr_name')
                if df is not None and len(df) > 0:
                    row = df.iloc[0]
                    results[code] = {
                        'ts_code': row.get('ts_code', ''),
                        'csname': row.get('csname', ''),
                        'index_code': row.get('index_code', ''),
                        'index_name': row.get('index_name', ''),
                        'exchange': row.get('exchange', ''),
                        'etf_type': row.get('etf_type', ''),
                        'setup_date': row.get('setup_date', ''),
                        'list_date': row.get('list_date', ''),
                        'mgr_name': row.get('mgr_name', ''),
                        'update_time': datetime.now().isoformat()
                    }
            return results
        else:
            # 获取全部 ETF
            df = pro.etf_basic(list_status='L', fields='ts_code,csname,index_code,index_name,exchange,etf_type,mgr_name')
            if df is not None and len(df) > 0:
                results = {}
                for _, row in df.iterrows():
                    ts_code = row.get('ts_code', '')
                    code = ts_code.split('.')[0]
                    results[code] = {
                        'ts_code': ts_code,
                        'csname': row.get('csname', ''),
                        'index_code': row.get('index_code', ''),
                        'index_name': row.get('index_name', ''),
                        'exchange': row.get('exchange', ''),
                        'etf_type': row.get('etf_type', ''),
                        'mgr_name': row.get('mgr_name', ''),
                        'update_time': datetime.now().isoformat()
                    }
                return results
    except Exception as e:
        log_message(f"⚠️ 获取 ETF 基础信息失败：{e}")
    
    return {}

# ============ ETF 实时日线 ============

def get_etf_realtime_daily(etf_codes: List[str]) -> Dict:
    """
    获取 ETF 实时日线数据
    
    接口：rt_etf_k
    文档：https://tushare.pro/document/2?doc_id=400
    权限：单独开通
    
    Args:
        etf_codes: ETF 代码列表
    
    Returns:
        实时日线数据
    """
    pro = get_pro()
    results = {}
    
    # 沪市 ETF
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
                            'num': int(row.get('num', 0)),
                            'trade_time': row.get('trade_time', ''),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
        except Exception as e:
            log_message(f"⚠️ 沪市 ETF 实时数据失败：{e}")
    
    # 深市 ETF
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
                            'num': int(row.get('num', 0)),
                            'trade_time': row.get('trade_time', ''),
                            'update_time': datetime.now().isoformat(),
                            'data_source': 'tushare_rt_etf_k'
                        }
        except Exception as e:
            log_message(f"⚠️ 深市 ETF 实时数据失败：{e}")
    
    return results

# ============ ETF 实时分钟 ============

def get_etf_realtime_minute(etf_codes: List[str], freq: str = '5MIN') -> Dict:
    """
    获取 ETF 实时分钟数据
    
    接口：rt_min
    文档：https://tushare.pro/document/2?doc_id=416
    权限：正式权限
    
    Args:
        etf_codes: ETF 代码列表
        freq: 频率（1MIN/5MIN/15MIN/30MIN/60MIN）
    
    Returns:
        分钟数据
    """
    pro = get_pro()
    results = {}
    
    for code in etf_codes:
        ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
        
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
            log_message(f"⚠️ {code} 分钟数据失败：{e}")
        
        time.sleep(0.1)
    
    return results

# ============ ETF 份额规模 ============

def get_etf_share_size(etf_codes: List[str], days: int = 10) -> Dict:
    """
    获取 ETF 份额规模数据
    
    接口：etf_share_size
    文档：https://tushare.pro/document/2?doc_id=408
    权限：8000 积分
    
    Args:
        etf_codes: ETF 代码列表
        days: 获取天数
    
    Returns:
        份额规模数据
    """
    pro = get_pro()
    results = {}
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    for code in etf_codes:
        ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
        
        try:
            df = pro.etf_share_size(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                share_data = []
                for _, row in df.iterrows():
                    share_data.append({
                        'trade_date': row.get('trade_date', ''),
                        'total_share': float(row.get('total_share', 0)),  # 万份
                        'total_size': float(row.get('total_size', 0)),  # 万元
                        'nav': float(row.get('nav', 0)),  # 净值
                        'close': float(row.get('close', 0))  # 收盘价
                    })
                
                # 计算份额变化
                if len(share_data) >= 2:
                    latest = share_data[0]
                    prev = share_data[1]
                    share_change = (latest['total_share'] - prev['total_share']) / prev['total_share'] if prev['total_share'] > 0 else 0
                    
                    results[code] = {
                        'code': code,
                        'latest': latest,
                        'prev': prev,
                        'share_change': round(share_change, 4),
                        'share_change_pct': round(share_change * 100, 2),
                        'signal': '大幅申购' if share_change > 0.05 else ('大幅赎回' if share_change < -0.05 else '正常'),
                        'update_time': datetime.now().isoformat(),
                        'data_source': 'tushare_etf_share_size'
                    }
        except Exception as e:
            log_message(f"⚠️ {code} 份额数据失败：{e}")
        
        time.sleep(0.1)
    
    return results

# ============ 指数实时日线 ============

def get_index_realtime_daily(index_codes: List[str] = None) -> Dict:
    """
    获取指数实时日线数据
    
    接口：rt_idx_k
    文档：https://tushare.pro/document/2?doc_id=403
    权限：单独开通
    
    Args:
        index_codes: 指数代码列表（如 ['000300.SH', '000905.SH']）
    
    Returns:
        指数实时数据
    """
    pro = get_pro()
    results = {}
    
    if not index_codes:
        # 默认获取主要指数
        index_codes = list(INDEX_CODES.values())
    
    try:
        # 支持多个代码同时查询
        ts_code_str = ','.join(index_codes)
        df = pro.rt_idx_k(ts_code=ts_code_str)
        
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                ts_code = row.get('ts_code', '')
                code = ts_code.split('.')[0]
                results[code] = {
                    'ts_code': ts_code,
                    'name': row.get('name', ''),
                    'close': float(row.get('close', 0)),
                    'pre_close': float(row.get('pre_close', 0)),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'vol': float(row.get('vol', 0)),
                    'amount': float(row.get('amount', 0)),
                    'trade_time': row.get('trade_time', ''),
                    'change_pct': round((float(row.get('close', 0)) - float(row.get('pre_close', 0))) / float(row.get('pre_close', 0)) * 100, 2) if row.get('pre_close', 0) > 0 else 0,
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'tushare_rt_idx_k'
                }
    except Exception as e:
        log_message(f"⚠️ 指数实时数据失败：{e}")
    
    return results

# ============ 指数实时分钟 ============

def get_index_realtime_minute(index_codes: List[str], freq: str = '5MIN') -> Dict:
    """获取指数分钟数据"""
    pro = get_pro()
    results = {}
    
    for ts_code in index_codes:
        try:
            df = pro.rt_idx_min(ts_code=ts_code, freq=freq)
            if df is not None and len(df) > 0:
                data = []
                for _, row in df.iterrows():
                    data.append({
                        'time': row.get('time', ''),
                        'close': float(row.get('close', 0)),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'vol': float(row.get('vol', 0))
                    })
                results[ts_code] = {'data': data, 'count': len(data), 'freq': freq}
        except Exception as e:
            log_message(f"⚠️ {ts_code} 分钟数据失败：{e}")
        time.sleep(0.1)
    
    return results

# ============ 指数技术因子 ============

def get_index_techfactor(index_codes: List[str]) -> Dict:
    """获取指数技术指标"""
    pro = get_pro()
    results = {}
    
    for ts_code in index_codes:
        try:
            df = pro.idx_techfactor(ts_code=ts_code, trade_date=datetime.now().strftime('%Y%m%d'))
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                results[ts_code] = {
                    'rsi': float(row.get('rsi', 0)),
                    'macd': float(row.get('macd', 0)),
                    'kdj_k': float(row.get('kdj_k', 0)),
                    'kdj_d': float(row.get('kdj_d', 0)),
                    'boll_upper': float(row.get('boll_upper', 0)),
                    'boll_lower': float(row.get('boll_lower', 0)),
                    'update_time': datetime.now().isoformat()
                }
        except Exception as e:
            log_message(f"⚠️ {ts_code} 技术指标失败：{e}")
        time.sleep(0.1)
    
    return results

# ============ 全球指数 ============

def get_global_index(index_codes: List[str] = None) -> Dict:
    """获取全球指数数据"""
    pro = get_pro()
    results = {}
    
    if not index_codes:
        index_codes = ['DJI', 'SPX', 'IXIC', 'HSI', 'N225', 'FTSE', 'GDAXI']
    
    try:
        df = pro.index_global(ts_code=','.join(index_codes))
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                ts_code = row.get('ts_code', '')
                results[ts_code] = {
                    'name': row.get('name', ''),
                    'close': float(row.get('close', 0)),
                    'change': float(row.get('change', 0)),
                    'change_pct': float(row.get('pct_chg', 0)),
                    'update_time': datetime.now().isoformat()
                }
    except Exception as e:
        log_message(f"⚠️ 全球指数失败：{e}")
    
    return results

# ============ 新闻快讯 ============

def get_news(start_date: str = None, end_date: str = None, limit: int = 50) -> List[Dict]:
    """获取新闻快讯"""
    pro = get_pro()
    
    if not start_date:
        start_date = datetime.now().strftime('%Y%m%d')
    if not end_date:
        end_date = start_date
    
    try:
        df = pro.news(start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            news_list = []
            for _, row in df.iterrows():
                news_list.append({
                    'id': row.get('id', ''),
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'pub_date': row.get('pub_date', ''),
                    'source': row.get('source', '')
                })
            return news_list[:limit]
    except Exception as e:
        log_message(f"⚠️ 新闻获取失败：{e}")
    
    return []

# ============ 股票每日指标 ============

def get_daily_basic(ts_codes: List[str] = None, trade_date: str = None, start_date: str = None, end_date: str = None) -> Dict:
    """
    获取股票每日指标（PE/PB/股息率等）
    
    接口：daily_basic
    文档：https://tushare.pro/document/2?doc_id=32
    权限：2000 积分
    
    Args:
        ts_codes: 股票代码列表（可选）
        trade_date: 交易日期（YYYYMMDD 格式）
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        每日指标数据
    """
    pro = get_pro()
    
    if not trade_date and not start_date:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    try:
        if ts_codes:
            # 获取指定股票
            results = {}
            for ts_code in ts_codes:
                df = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
                if df is not None and len(df) > 0:
                    row = df.iloc[0]
                    results[ts_code] = {
                        'ts_code': ts_code,
                        'trade_date': row.get('trade_date', ''),
                        'close': float(row.get('close', 0)),
                        'turnover_rate': float(row.get('turnover_rate', 0)),
                        'volume_ratio': float(row.get('volume_ratio', 0)),
                        'pe': float(row.get('pe', 0)) if row.get('pe') else None,
                        'pe_ttm': float(row.get('pe_ttm', 0)) if row.get('pe_ttm') else None,
                        'pb': float(row.get('pb', 0)),
                        'ps': float(row.get('ps', 0)),
                        'ps_ttm': float(row.get('ps_ttm', 0)),
                        'dv_ratio': float(row.get('dv_ratio', 0)),
                        'dv_ttm': float(row.get('dv_ttm', 0)),
                        'total_share': float(row.get('total_share', 0)),
                        'float_share': float(row.get('float_share', 0)),
                        'total_mv': float(row.get('total_mv', 0)),
                        'circ_mv': float(row.get('circ_mv', 0)),
                        'update_time': datetime.now().isoformat()
                    }
            return results
        else:
            # 获取全部股票
            if trade_date:
                df = pro.daily_basic(trade_date=trade_date)
            else:
                df = pro.daily_basic(start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                results = {}
                for _, row in df.iterrows():
                    ts_code = row.get('ts_code', '')
                    results[ts_code] = {
                        'ts_code': ts_code,
                        'trade_date': row.get('trade_date', ''),
                        'close': float(row.get('close', 0)),
                        'pe': float(row.get('pe', 0)) if row.get('pe') else None,
                        'pe_ttm': float(row.get('pe_ttm', 0)) if row.get('pe_ttm') else None,
                        'pb': float(row.get('pb', 0)),
                        'dv_ratio': float(row.get('dv_ratio', 0)),
                        'total_mv': float(row.get('total_mv', 0)),
                        'update_time': datetime.now().isoformat()
                    }
                return results
    except Exception as e:
        log_message(f"⚠️ 获取每日指标失败：{e}")
    
    return {}

def calculate_etf_valuation_from_constituents(etf_code: str, index_code: str) -> Dict:
    """
    通过成分股计算 ETF 估值
    
    Args:
        etf_code: ETF 代码
        index_code: 跟踪指数代码
    
    Returns:
        ETF 估值数据
    """
    # TODO: 需要获取指数成分股权重数据
    # 简化版本：使用行业平均估值
    return {}

# ============ 场内基金技术因子 ============

def get_fund_factor_pro(ts_codes: List[str], trade_date: str = None, start_date: str = None, end_date: str = None) -> Dict:
    """
    获取场内基金技术因子（专业版）
    
    接口：fund_factor_pro
    文档：https://tushare.pro/document/2?doc_id=359
    权限：5000 积分（5000 积分每分钟 30 次，8000+ 积分每分钟 500 次）
    
    Args:
        ts_codes: 基金代码列表
        trade_date: 交易日期
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        技术因子数据
    """
    pro = get_pro()
    results = {}
    
    if not trade_date and not start_date:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    try:
        for ts_code in ts_codes:
            code_with_suffix = f"{ts_code}.SH" if ts_code.startswith('5') else f"{ts_code}.SZ"
            
            df = pro.fund_factor_pro(
                ts_code=code_with_suffix,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) > 0:
                row = df.iloc[-1]  # 取最新数据
                
                results[ts_code] = {
                    'ts_code': code_with_suffix,
                    'trade_date': row.get('trade_date', ''),
                    'close': float(row.get('close', 0)),
                    'pct_change': float(row.get('pct_change', 0)),
                    # 趋势指标
                    'ma_5': float(row.get('ma_bfq_5', 0)),
                    'ma_10': float(row.get('ma_bfq_10', 0)),
                    'ma_20': float(row.get('ma_bfq_20', 0)),
                    'ma_60': float(row.get('ma_bfq_60', 0)),
                    'ema_12': float(row.get('ema_bfq_12', 0)),
                    'ema_26': float(row.get('expma_12_bfq', 0)),
                    # 动量指标
                    'rsi_6': float(row.get('rsi_bfq_6', 0)),
                    'rsi_12': float(row.get('rsi_bfq_12', 0)),
                    'rsi_24': float(row.get('rsi_bfq_24', 0)),
                    'kdj_k': float(row.get('kdj_k_bfq', 0)),
                    'kdj_d': float(row.get('kdj_d_bfq', 0)),
                    'kdj_j': float(row.get('kdj_bfq', 0)),
                    'bias_6': float(row.get('bias1_bfq', 0)),
                    'bias_12': float(row.get('bias2_bfq', 0)),
                    'bias_24': float(row.get('bias3_bfq', 0)),
                    'macd': float(row.get('macd_bfq', 0)),
                    'macd_dif': float(row.get('macd_dif_bfq', 0)),
                    'macd_dea': float(row.get('macd_dea_bfq', 0)),
                    # 波动指标
                    'boll_upper': float(row.get('boll_upper_bfq', 0)),
                    'boll_mid': float(row.get('boll_mid_bfq', 0)),
                    'boll_lower': float(row.get('boll_lower_bfq', 0)),
                    'atr': float(row.get('atr_bfq', 0)),
                    # 成交量指标
                    'obv': float(row.get('obv_bfq', 0)),
                    'mfi': float(row.get('mfi_bfq', 0)),
                    # 压力支撑
                    'taq_up': float(row.get('taq_up_bfq', 0)),
                    'taq_down': float(row.get('taq_down_bfq', 0)),
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'tushare_fund_factor_pro'
                }
            
            time.sleep(0.05)  # 控制请求频率
    except Exception as e:
        log_message(f"⚠️ 获取基金技术因子失败：{e}")
    
    return results

def generate_tech_signals(etf_factors: Dict) -> Dict:
    """
    根据技术指标生成信号
    
    Args:
        etf_factors: 技术因子数据
    
    Returns:
        信号数据
    """
    signals = {}
    
    for code, data in etf_factors.items():
        signal = {
            'code': code,
            'signals': [],
            'overall': '中性'
        }
        
        # RSI 信号
        rsi = data.get('rsi_12', 50)
        if rsi < 30:
            signal['signals'].append({'type': 'RSI', 'signal': '超卖', 'strength': '强', 'direction': '买入'})
        elif rsi > 70:
            signal['signals'].append({'type': 'RSI', 'signal': '超买', 'strength': '强', 'direction': '卖出'})
        
        # MACD 信号
        macd = data.get('macd', 0)
        macd_dif = data.get('macd_dif', 0)
        macd_dea = data.get('macd_dea', 0)
        if macd_dif > macd_dea and macd > 0:
            signal['signals'].append({'type': 'MACD', 'signal': '金叉', 'strength': '中', 'direction': '买入'})
        elif macd_dif < macd_dea and macd < 0:
            signal['signals'].append({'type': 'MACD', 'signal': '死叉', 'strength': '中', 'direction': '卖出'})
        
        # KDJ 信号
        kdj_k = data.get('kdj_k', 50)
        kdj_d = data.get('kdj_d', 50)
        if kdj_k < 20 and kdj_k > kdj_d:
            signal['signals'].append({'type': 'KDJ', 'signal': '超卖金叉', 'strength': '中', 'direction': '买入'})
        elif kdj_k > 80 and kdj_k < kdj_d:
            signal['signals'].append({'type': 'KDJ', 'signal': '超买死叉', 'strength': '中', 'direction': '卖出'})
        
        # BOLL 信号
        close = data.get('close', 0)
        boll_lower = data.get('boll_lower', 0)
        boll_upper = data.get('boll_upper', 0)
        if close < boll_lower:
            signal['signals'].append({'type': 'BOLL', 'signal': '突破下轨', 'strength': '强', 'direction': '买入'})
        elif close > boll_upper:
            signal['signals'].append({'type': 'BOLL', 'signal': '突破上轨', 'strength': '强', 'direction': '卖出'})
        
        # 综合判断
        buy_signals = sum(1 for s in signal['signals'] if s['direction'] == '买入')
        sell_signals = sum(1 for s in signal['signals'] if s['direction'] == '卖出')
        
        if buy_signals > sell_signals:
            signal['overall'] = '看涨'
        elif sell_signals > buy_signals:
            signal['overall'] = '看跌'
        
        signal['score'] = buy_signals - sell_signals
        signals[code] = signal
    
    return signals

# ============ 综合测试 ============

def main():
    """测试所有接口"""
    print("="*70)
    print("Tushare Pro 数据获取模块 v4.0 完整测试")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1-8. 原有测试...
    log_message("\n1. 测试 ETF 基础信息...")
    etf_basic = get_etf_basic(ALL_32_ETFS[:5])
    print(f"✅ ETF 基础信息：{len(etf_basic)}只")
    
    log_message("\n2. 测试 ETF 实时日线...")
    etf_realtime = get_etf_realtime_daily(ALL_32_ETFS)
    print(f"✅ ETF 实时日线：{len(etf_realtime)}只")
    
    log_message("\n3. 测试 ETF 实时分钟...")
    etf_min = get_etf_realtime_minute(ALL_32_ETFS[:3], freq='5MIN')
    print(f"✅ ETF 实时分钟：{len(etf_min)}只")
    
    log_message("\n4. 测试 ETF 份额规模...")
    etf_share = get_etf_share_size(ALL_32_ETFS[:5], days=5)
    print(f"✅ ETF 份额规模：{len(etf_share)}只")
    for code, data in etf_share.items():
        print(f"  {code}: 份额变化{data['share_change_pct']:+.2f}% ({data['signal']})")
    
    log_message("\n5. 测试指数实时日线...")
    idx_realtime = get_index_realtime_daily()
    print(f"✅ 指数实时日线：{len(idx_realtime)}只")
    for code, data in idx_realtime.items():
        print(f"  {code}({data['name']}): {data['close']:.2f} ({data['change_pct']:+.2f}%)")
    
    log_message("\n6. 测试指数实时分钟...")
    idx_min = get_index_realtime_minute(['000300.SH'], freq='5MIN')
    print(f"✅ 指数实时分钟：{len(idx_min)}只")
    
    log_message("\n7. 测试全球指数...")
    global_idx = get_global_index()
    print(f"✅ 全球指数：{len(global_idx)}只")
    for code, data in global_idx.items():
        print(f"  {code}({data['name']}): {data['close']:.2f} ({data['change_pct']:+.2f}%)")
    
    log_message("\n8. 测试新闻快讯...")
    news = get_news(limit=5)
    print(f"✅ 新闻快讯：{len(news)}条")
    for n in news[:3]:
        print(f"  {n['title'][:50]}...")
    
    # 9. 股票每日指标（新增）
    log_message("\n9. 测试股票每日指标...")
    test_stocks = ['600000.SH', '600036.SH', '000001.SZ']  # 测试几只股票
    daily_basic = get_daily_basic(test_stocks)
    print(f"✅ 股票每日指标：{len(daily_basic)}只")
    for ts_code, data in daily_basic.items():
        pe = data.get('pe', 'N/A')
        pb = data.get('pb', 'N/A')
        dv = data.get('dv_ratio', 'N/A')
        print(f"  {ts_code}: PE={pe} PB={pb} 股息率={dv}%")
    
    # 10. 场内基金技术因子（新增）
    log_message("\n10. 测试场内基金技术因子...")
    fund_factors = get_fund_factor_pro(ALL_32_ETFS[:5])
    print(f"✅ 场内基金技术因子：{len(fund_factors)}只")
    for code, data in fund_factors.items():
        rsi = data.get('rsi_12', 'N/A')
        macd = data.get('macd', 'N/A')
        boll_mid = data.get('boll_mid', 'N/A')
        print(f"  {code}: RSI={rsi} MACD={macd} BOLL 中={boll_mid}")
    
    # 11. 技术指标信号（新增）
    log_message("\n11. 测试技术指标信号...")
    tech_signals = generate_tech_signals(fund_factors)
    print(f"✅ 技术指标信号：{len(tech_signals)}只")
    for code, signal in tech_signals.items():
        overall = signal.get('overall', 'N/A')
        score = signal.get('score', 0)
        signals_count = len(signal.get('signals', []))
        print(f"  {code}: {overall} (得分:{score}, 信号数:{signals_count})")
    
    print("\n" + "="*70)
    print("所有接口测试完成！v4.0 新增 2 个核心接口！")
    print("="*70)

if __name__ == "__main__":
    main()

# ============ Tushare 官方 ETF 日线接口 ============

def get_fund_daily(ts_code: str = None, trade_date: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    获取 ETF 日线行情（fund_daily）
    
    接口：fund_daily
    描述：获取 ETF 行情每日收盘后成交数据，历史超过 10 年
    积分：需要至少 5000 积分（我们有 25,100 分，完全可用）
    
    Args:
        ts_code: 基金代码（如 510330.SH）
        trade_date: 交易日期（YYYYMMDD 格式）
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        DataFrame with columns: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
    """
    log_message(f"获取 ETF 日线行情：{ts_code}...")
    
    pro = get_pro()
    
    try:
        df = pro.fund_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is not None and len(df) > 0:
            log_message(f"  ✅ 获取 {len(df)}条记录")
            return df
        else:
            log_message(f"  ⚠️ 无数据")
            return pd.DataFrame()
    
    except Exception as e:
        log_message(f"  ❌ 失败：{e}")
        return pd.DataFrame()
