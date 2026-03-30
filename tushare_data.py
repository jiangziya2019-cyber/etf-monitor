#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 数据获取模块 (主数据源)
积分：25,100 分 - 完全数据接口
Token: 7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75

所有金融数据获取统一使用此模块，Tushare Pro 作为主数据源。
"""

import tushare as ts
from datetime import datetime
from typing import Optional, Any, List

# Tushare 配置
TS_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# ============ 通用行情接口 (pro_bar) ============

def get_daily(ts_code: str, start_date: str = None, end_date: str = None, 
              asset: str = 'E', adj: str = None) -> Optional[Any]:
    """
    获取日线数据（股票/指数/ETF/期货）
    
    Args:
        ts_code: 证券代码 (e.g. '000001.SZ', '000001.SH', '510300.SH', 'AU2406.SHF')
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        asset: 资产类别 E=股票，I=指数，FT=期货，FD=基金，O=期权，CB=可转债
        adj: 复权类型 None/qfq/hfq (只针对股票)
    
    Returns:
        DataFrame or None
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = end_date
        
        df = ts.pro_bar(ts_code=ts_code, asset=asset, adj=adj, 
                       start_date=start_date, end_date=end_date)
        return df if df is not None and len(df) > 0 else None
    except Exception as e:
        print(f"❌ get_daily 失败 ({ts_code}): {e}")
        return None

def get_min(ts_code: str, trade_date: str = None, 
            start_time: str = None, end_time: str = None,
            asset: str = 'E', freq: str = '1min') -> Optional[Any]:
    """
    获取分钟线数据（股票/指数/ETF）
    
    Args:
        ts_code: 证券代码
        trade_date: 交易日期 YYYYMMDD
        start_time: 开始时间 "2026-03-27 09:30:00"
        end_time: 结束时间 "2026-03-27 15:00:00"
        asset: 资产类别 E=股票，I=指数，FD=基金
        freq: 频度 1min/5min/15min/30min/60min
    
    Returns:
        DataFrame or None
    """
    try:
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        # 如果没有指定时间，默认获取全天数据
        if not start_time:
            start_time = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 09:30:00"
        if not end_time:
            end_time = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 15:00:00"
        
        df = ts.pro_bar(ts_code=ts_code, asset=asset, 
                       start_date=start_time, end_date=end_time, 
                       freq=freq)
        return df if df is not None and len(df) > 0 else None
    except Exception as e:
        print(f"❌ get_min 失败 ({ts_code}): {e}")
        return None

# ============ 便捷函数 ============

def get_stock_daily(ts_code: str, start_date: str = None, end_date: str = None, 
                    adj: str = None) -> Optional[Any]:
    """获取 A 股个股日线"""
    return get_daily(ts_code, start_date, end_date, asset='E', adj=adj)

def get_stock_min(ts_code: str, trade_date: str = None, 
                  start_time: str = None, end_time: str = None,
                  freq: str = '1min') -> Optional[Any]:
    """获取 A 股个股分钟线"""
    return get_min(ts_code, trade_date, start_time, end_time, asset='E', freq=freq)

def get_index_daily(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取指数日线"""
    return get_daily(ts_code, start_date, end_date, asset='I')

def get_index_min(ts_code: str, trade_date: str = None,
                  start_time: str = None, end_time: str = None,
                  freq: str = '1min') -> Optional[Any]:
    """获取指数分钟线"""
    return get_min(ts_code, trade_date, start_time, end_time, asset='I', freq=freq)

def get_fund_daily(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取 ETF/基金日线"""
    return get_daily(ts_code, start_date, end_date, asset='FD')

def get_fund_min(ts_code: str, trade_date: str = None,
                 start_time: str = None, end_time: str = None,
                 freq: str = '1min') -> Optional[Any]:
    """获取 ETF/基金分钟线"""
    return get_min(ts_code, trade_date, start_time, end_time, asset='FD', freq=freq)

def get_futures_daily(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取期货日线"""
    return get_daily(ts_code, start_date, end_date, asset='FT')

def get_hk_daily(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取港股日线"""
    return get_daily(ts_code, start_date, end_date, asset='E')

def get_us_daily(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取美股日线"""
    return get_daily(ts_code, start_date, end_date, asset='E')

def get_hk_daily_pro(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """获取港股日线 (hk_daily 接口)"""
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = end_date
        
        df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df if df is not None and len(df) > 0 else None
    except Exception as e:
        print(f"❌ get_hk_daily_pro 失败 ({ts_code}): {e}")
        return None

def get_futures_daily_pro(ts_code: str, start_date: str = None, end_date: str = None) -> Optional[Any]:
    """
    获取期货日线 (fut_daily 接口)
    
    Args:
        ts_code: 期货代码 (e.g. 'AU.SHF' 沪金，'SC.INE' 原油，'AUL.SHF' 沪金主连)
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = end_date
        
        df = pro.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df if df is not None and len(df) > 0 else None
    except Exception as e:
        print(f"❌ get_futures_daily_pro 失败 ({ts_code}): {e}")
        return None

# ============ 测试函数 ============

def test_all():
    """测试所有接口"""
    print("=" * 70)
    print("🧪 Tushare Pro 接口测试 (完整版)")
    print("=" * 70)
    
    tests = [
        # A 股
        ("A 股日线", lambda: get_stock_daily('000001.SZ', '20260325', '20260327')),
        ("A 股分钟线", lambda: get_stock_min('000001.SZ', '20260327')),
        
        # 指数
        ("上证指数日线", lambda: get_index_daily('000001.SH', '20260325', '20260327')),
        ("上证指数分钟线", lambda: get_index_min('000001.SH', '20260327')),
        
        # ETF
        ("300ETF 日线", lambda: get_fund_daily('510300.SH', '20260325', '20260327')),
        ("300ETF 分钟线", lambda: get_fund_min('510300.SH', '20260327')),
        
        # 港股
        ("腾讯控股日线", lambda: get_hk_daily_pro('00700.HK', '20260325', '20260327')),
        
        # 期货
        ("沪金日线", lambda: get_futures_daily_pro('AU.SHF', '20260325', '20260327')),
        ("SC 原油日线", lambda: get_futures_daily_pro('SC.INE', '20260325', '20260327')),
        ("沪金主连", lambda: get_futures_daily_pro('AUL.SHF', '20260325', '20260327')),
    ]
    
    for name, func in tests:
        try:
            df = func()
            if df is not None and len(df) > 0:
                print(f"✅ {name}: {len(df)} 条记录")
            else:
                print(f"⚠️ {name}: 无数据")
        except Exception as e:
            print(f"❌ {name}: {e}")

if __name__ == "__main__":
    test_all()
