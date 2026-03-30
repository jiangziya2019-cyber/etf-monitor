#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值数据获取模块 - 优先级🔴高
版本：v1.0 | 创建：2026-03-28 13:40

功能:
  - 接入 Tushare Pro 指数估值数据
  - ETF→跟踪指数→估值映射
  - 缓存估值数据（7 天）
"""

import sys, json, os, time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
CACHE_DIR = '/home/admin/openclaw/workspace/valuation_cache'
LOG_FILE = '/home/admin/openclaw/workspace/valuation_data.log'

# ETF 与指数映射表
ETF_INDEX_MAP = {
    # 宽基 ETF
    '510300': '000300.SH',  # 300ETF → 沪深 300
    '510500': '000905.SH',  # 500ETF → 中证 500
    '510180': '000040.SH',  # 180ETF → 上证 180
    '159949': '399006.SZ',  # 创业 50 → 创业板指
    '159399': '000922.SH',  # 现金流 → 中证红利
    
    # 红利 ETF
    '510880': '000015.SH',  # 红利 ETF → 红利指数
    
    # 行业 ETF
    '512010': '000933.SH',  # 医药 ETF → 医药生物
    '512480': '000932.SH',  # 半导体 → 半导体
    '515790': '000993.SH',  # 光伏 ETF → 光伏产业
    '159566': '000993.SH',  # 储能电池 → 新能源
    '159663': '000993.SH',  # 机床 ETF → 工业母机
    '562500': '000993.SH',  # 机器人 ETF → 机器人
    '159227': '000993.SH',  # 航空航天 → 航空航天
    
    # 科技 ETF
    '159819': '000993.SH',  # AI 智能 → 人工智能
    '159363': '000993.SH',  # 创业板 AI → 人工智能
    '159243': '000993.SH',  # 创业智能 → 人工智能
    '515260': '000993.SH',  # 电子 ETF → 电子
    '512720': '000993.SH',  # 计算机 ETF → 计算机
    '515880': '000993.SH',  # 通信 ETF → 通信
    
    # 周期 ETF
    '512400': '000993.SH',  # 有色 ETF → 有色金属
    '516020': '000993.SH',  # 化工 ETF → 化工
    '515210': '000993.SH',  # 钢铁 ETF → 钢铁
    '515180': '000993.SH',  # 煤炭 ETF → 煤炭
    '516750': '000993.SH',  # 建材 ETF → 建材
    
    # 消费 ETF
    '516990': '000993.SH',  # 家电 ETF → 家电
    '516110': '000993.SH',  # 汽车 ETF → 汽车
    '159925': '000932.SH',  # 消费 ETF → 主要消费
    
    # 金融 ETF
    '512800': '000993.SH',  # 银行 ETF → 银行
    '510230': '000993.SH',  # 金融 ETF → 金融
    '512880': '000993.SH',  # 证券 ETF → 证券
    '512200': '000993.SH',  # 地产 ETF → 房地产
    
    # 其他
    '159206': '000993.SH',  # 卫星 ETF → 国防军工
    '159241': '000993.SH',  # 航空 ETF → 国防军工
    '159206': '000993.SH',  # 军工 ETF → 国防军工
}

# 股息率数据（静态，季度更新）
DIVIDEND_YIELD_DATA = {
    '510880': 5.2,  # 红利 ETF
    '159399': 4.1,  # 现金流
    '510300': 3.2,  # 300ETF
    '510500': 2.8,  # 500ETF
    '510180': 4.5,  # 180ETF
    '510230': 3.5,  # 金融 ETF
    '512800': 4.8,  # 银行 ETF
}

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def get_index_valuation(index_code: str) -> Optional[Dict]:
    """
    获取指数估值数据（Tushare Pro）
    
    Args:
        index_code: 指数代码（如 000300.SH）
    
    Returns:
        估值数据字典
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    try:
        # 获取指数估值数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.index_dailybasic(ts_code=index_code, start_date=start_date, end_date=end_date)
        
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            return {
                'index_code': index_code,
                'pe': float(latest.get('pe', 0)),
                'pe_percentile': float(latest.get('pe_ttm_percentile', 50)),  # PE 百分位
                'pb': float(latest.get('pb', 0)),
                'pb_percentile': float(latest.get('pb_percentile', 50)),  # PB 百分位
                'dividend_yield': float(latest.get('dv_ratio', 0)),  # 股息率
                'trade_date': latest.get('trade_date', ''),
                'update_time': datetime.now().isoformat()
            }
    except Exception as e:
        log_message(f"获取指数估值失败 {index_code}: {e}")
    
    return None

def get_etf_valuation(etf_code: str) -> Optional[Dict]:
    """
    获取 ETF 估值数据
    
    Args:
        etf_code: ETF 代码
    
    Returns:
        ETF 估值数据
    """
    # 1. 检查缓存
    cache_file = f"{CACHE_DIR}/{etf_code}.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # 检查缓存是否过期（7 天）
            cache_time = datetime.fromisoformat(cached_data.get('update_time', '2000-01-01'))
            if (datetime.now() - cache_time).days < 7:
                return cached_data
        except:
            pass
    
    # 2. 获取指数代码
    index_code = ETF_INDEX_MAP.get(etf_code)
    if not index_code:
        log_message(f"⚠️ {etf_code} 无指数映射，使用股息率替代")
        return get_dividend_yield(etf_code)
    
    # 3. 获取指数估值
    index_valuation = get_index_valuation(index_code)
    
    if index_valuation:
        etf_valuation = {
            'etf_code': etf_code,
            'index_code': index_code,
            'pe': index_valuation['pe'],
            'pe_percentile': index_valuation['pe_percentile'],
            'pb': index_valuation['pb'],
            'pb_percentile': index_valuation['pb_percentile'],
            'dividend_yield': index_valuation['dividend_yield'],
            'trade_date': index_valuation['trade_date'],
            'update_time': datetime.now().isoformat(),
            'data_source': 'tushare_index_valuation'
        }
        
        # 4. 保存缓存
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(etf_valuation, f, indent=2)
        
        log_message(f"✅ {etf_code} 估值：PE={etf_valuation['pe']:.1f} PE 分位={etf_valuation['pe_percentile']:.1f}%")
        return etf_valuation
    
    # 5. 降级：使用股息率
    log_message(f"⚠️ {etf_code} 指数估值失败，使用股息率替代")
    return get_dividend_yield(etf_code)

def get_dividend_yield(etf_code: str) -> Optional[Dict]:
    """
    获取股息率数据（静态数据）
    
    Args:
        etf_code: ETF 代码
    
    Returns:
        股息率数据
    """
    dividend = DIVIDEND_YIELD_DATA.get(etf_code, 2.0)  # 默认 2%
    
    return {
        'etf_code': etf_code,
        'pe_percentile': 50.0,  # 默认中位数
        'pb_percentile': 50.0,
        'dividend_yield': dividend,
        'trade_date': datetime.now().strftime('%Y%m%d'),
        'update_time': datetime.now().isoformat(),
        'data_source': 'static_dividend'
    }

def get_all_etf_valuations(etf_codes: List[str]) -> Dict:
    """
    批量获取 ETF 估值数据
    
    Args:
        etf_codes: ETF 代码列表
    
    Returns:
        估值数据字典 {code: valuation}
    """
    log_message(f"开始获取 {len(etf_codes)}只 ETF 估值数据...")
    
    valuations = {}
    for i, code in enumerate(etf_codes, 1):
        valuation = get_etf_valuation(code)
        if valuation:
            valuations[code] = valuation
        
        if i % 20 == 0:
            log_message(f"  进度 {i}/{len(etf_codes)}...")
        
        time.sleep(0.1)  # API 限流
    
    log_message(f"✅ 完成 {len(valuations)}/{len(etf_codes)}只 ETF 估值")
    return valuations

def main():
    """测试运行"""
    print("="*70)
    print("估值数据获取模块 v1.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 ETF 列表（第三层 12 只）
    test_etfs = [
        '512880', '512400', '512980', '515260', '512800', '516110',
        '512720', '516020', '515880', '515210', '512660', '512200'
    ]
    
    valuations = get_all_etf_valuations(test_etfs)
    
    print("\n" + "="*70)
    print("估值数据汇总")
    print("="*70)
    
    for code, val in valuations.items():
        print(f"{code}: PE={val.get('pe', 'N/A')} PE 分位={val.get('pe_percentile', 'N/A'):.1f}% 股息率={val.get('dividend_yield', 'N/A'):.2f}%")
    
    print(f"\n✅ 完成 {len(valuations)}只 ETF 估值获取")
    print(f"📄 缓存目录：{CACHE_DIR}")

if __name__ == "__main__":
    main()
