#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值数据获取模块 v3.0 - 使用 Tushare ETF 官方接口
版本：v3.0 | 创建：2026-03-28 14:00

功能:
  - 使用 Tushare etf_basic 接口获取 ETF 基础信息
  - 使用 index_dailybasic 获取指数估值数据
  - ETF→跟踪指数→估值映射
  - 缓存估值数据（7 天）

接口文档：https://tushare.pro/document/2?doc_id=385
"""

import sys, json, os, time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'
CACHE_DIR = '/home/admin/openclaw/workspace/valuation_cache'
LOG_FILE = '/home/admin/openclaw/workspace/valuation_data_v3.log'

# 目标 ETF 列表（32 只）
TARGET_ETFS = [
    # 第一层
    '510880', '159399', '510300', '510500', '510180',
    # 第二层
    '515790', '159566', '512480', '159819', '512010', '159663', '562500', '159227',
    # 第三层
    '512880', '512400', '512980', '515260', '512800', '516110',
    '512720', '516020', '515880', '515210', '512660', '512200',
    # 第四层
    '513110', '513500', '159937', '160723', '513130'
]

# 股息率数据（静态，季度更新）
DIVIDEND_YIELD_DATA = {
    '510880': 5.2, '159399': 4.1, '510300': 3.2, '510500': 2.8, '510180': 4.5,
    '510230': 3.5, '512800': 4.8, '512880': 2.5, '512010': 1.8, '515790': 1.5,
    '159566': 1.2, '159663': 1.5, '562500': 1.3, '159227': 1.4, '159819': 1.0,
    '512480': 1.2, '515260': 1.5, '512720': 1.3, '515880': 2.0, '512400': 2.2,
    '516020': 2.5, '515210': 3.0, '516110': 2.0, '512200': 2.8, '512660': 1.5,
    '159363': 1.0, '159243': 1.2, '159206': 1.5, '159241': 1.4,
}

# 行业估值中枢（经验值，作为备用）
SECTOR_PE_PERCENTILE = {
    '沪深 300': 45, '中证 500': 40, '上证 180': 42, '创业板指': 35, '中证红利': 55, '上证红利': 60,
    '医药生物': 30, '半导体': 45, '光伏产业': 25, '储能产业': 35, '工业母机': 40, '机器人': 40, '航空航天': 45,
    '人工智能': 40, '电子': 45, '计算机': 35, '通信': 40,
    '有色金属': 50, '化工': 45, '钢铁': 40, '汽车': 45, '房地产': 30,
    '银行': 60, '金融': 55, '证券': 50, '军工': 45,
}

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')

def get_etf_info_from_tushare(etf_code: str) -> Optional[Dict]:
    """
    从 Tushare 获取 ETF 基础信息（包括跟踪指数代码）
    
    接口：etf_basic
    权限：8000 积分
    
    Args:
        etf_code: ETF 代码（不含后缀）
    
    Returns:
        ETF 基础信息
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    try:
        # 确定交易所后缀
        if etf_code.startswith('5'):
            ts_code = f"{etf_code}.SH"
        else:
            ts_code = f"{etf_code}.SZ"
        
        # 获取 ETF 基础信息
        df = pro.etf_basic(ts_code=ts_code, fields='ts_code,csname,index_code,index_name,exchange,etf_type')
        
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            return {
                'ts_code': row.get('ts_code', ''),
                'csname': row.get('csname', ''),
                'index_code': row.get('index_code', ''),
                'index_name': row.get('index_name', ''),
                'exchange': row.get('exchange', ''),
                'etf_type': row.get('etf_type', '')
            }
    except Exception as e:
        log_message(f"⚠️ 获取 ETF 基础信息失败 {etf_code}: {e}")
    
    return None

def get_index_valuation_from_tushare(index_code: str) -> Optional[Dict]:
    """
    从 Tushare 获取指数估值数据
    
    接口：index_dailybasic
    权限：需确认积分要求
    
    Args:
        index_code: 指数代码（如 000300.SH）
    
    Returns:
        指数估值数据
    """
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        # 获取指数估值数据
        df = pro.index_dailybasic(
            ts_code=index_code,
            start_date=start_date,
            end_date=end_date,
            fields='ts_code,trade_date,pe,pe_ttm,pb,ps,dv_ratio,pe_percentile,pb_percentile,ps_percentile'
        )
        
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            return {
                'index_code': latest.get('ts_code', ''),
                'trade_date': latest.get('trade_date', ''),
                'pe': float(latest.get('pe_ttm', 0)) if latest.get('pe_ttm') else float(latest.get('pe', 0)),
                'pe_percentile': float(latest.get('pe_percentile', 50)),
                'pb': float(latest.get('pb', 0)),
                'pb_percentile': float(latest.get('pb_percentile', 50)),
                'dividend_yield': float(latest.get('dv_ratio', 0)),
                'update_time': datetime.now().isoformat()
            }
    except Exception as e:
        log_message(f"⚠️ 获取指数估值失败 {index_code}: {e}")
    
    return None

def get_etf_valuation(etf_code: str) -> Dict:
    """
    获取 ETF 估值数据（综合方案 v3.0）
    
    优先级:
    1. Tushare ETF 基础信息 + 指数估值
    2. 行业估值中枢（经验值）
    3. 股息率替代
    
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
            cache_time = datetime.fromisoformat(cached_data.get('update_time', '2000-01-01'))
            if (datetime.now() - cache_time).days < 7:
                cached_data['cache_hit'] = True
                return cached_data
        except:
            pass
    
    # 2. 获取股息率
    dividend_yield = DIVIDEND_YIELD_DATA.get(etf_code, 2.0)
    
    # 3. 尝试从 Tushare 获取 ETF 基础信息
    etf_info = get_etf_info_from_tushare(etf_code)
    
    if etf_info:
        index_code = etf_info.get('index_code', '')
        index_name = etf_info.get('index_name', '')
        etf_type = etf_info.get('etf_type', '')
        
        log_message(f"📊 {etf_code}({etf_info['csname']}): 跟踪{index_name}({index_code}) 类型:{etf_type}")
        
        # 4. 获取指数估值
        if index_code:
            index_valuation = get_index_valuation_from_tushare(index_code)
            
            if index_valuation:
                valuation = {
                    'etf_code': etf_code,
                    'etf_name': etf_info.get('csname', ''),
                    'index_code': index_code,
                    'index_name': index_name,
                    'etf_type': etf_type,
                    'pe': index_valuation['pe'],
                    'pe_percentile': index_valuation['pe_percentile'],
                    'pb': index_valuation['pb'],
                    'pb_percentile': index_valuation['pb_percentile'],
                    'dividend_yield': index_valuation['dividend_yield'] if index_valuation['dividend_yield'] > 0 else dividend_yield,
                    'trade_date': index_valuation['trade_date'],
                    'update_time': datetime.now().isoformat(),
                    'data_source': 'tushare_etf_basic_index_valuation',
                    'cache_hit': False
                }
                
                # 5. 保存缓存
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump(valuation, f, indent=2)
                
                log_message(f"✅ {etf_code}: PE={valuation['pe']:.1f} PE 分位={valuation['pe_percentile']:.1f}% 股息率={valuation['dividend_yield']:.2f}%")
                return valuation
    
    # 6. 降级：使用行业估值中枢
    if etf_info:
        index_name = etf_info.get('index_name', '')
        pe_percentile = float(SECTOR_PE_PERCENTILE.get(index_name, 45))
        
        valuation = {
            'etf_code': etf_code,
            'etf_name': etf_info.get('csname', ''),
            'index_code': etf_info.get('index_code', ''),
            'index_name': index_name,
            'pe': None,
            'pe_percentile': pe_percentile,
            'pb': None,
            'pb_percentile': pe_percentile * 0.9,
            'dividend_yield': dividend_yield,
            'trade_date': datetime.now().strftime('%Y%m%d'),
            'update_time': datetime.now().isoformat(),
            'data_source': 'sector_median_estimate',
            'cache_hit': False
        }
        
        log_message(f"⚠️ {etf_code}: 使用行业中枢 PE 分位={pe_percentile:.1f}% 股息率={dividend_yield:.2f}%")
        return valuation
    
    # 7. 最终降级：使用股息率估算
    if dividend_yield >= 4.0:
        pe_percentile = 30.0
    elif dividend_yield >= 2.5:
        pe_percentile = 50.0
    else:
        pe_percentile = 70.0
    
    valuation = {
        'etf_code': etf_code,
        'etf_name': 'unknown',
        'index_code': '',
        'index_name': 'unknown',
        'pe': None,
        'pe_percentile': pe_percentile,
        'pb': None,
        'pb_percentile': pe_percentile * 0.9,
        'dividend_yield': dividend_yield,
        'trade_date': datetime.now().strftime('%Y%m%d'),
        'update_time': datetime.now().isoformat(),
        'data_source': 'dividend_yield_estimate',
        'cache_hit': False
    }
    
    log_message(f"⚠️ {etf_code}: 使用股息率估算 PE 分位={pe_percentile:.1f}% 股息率={dividend_yield:.2f}%")
    return valuation

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
    success_count = 0
    sector_count = 0
    dividend_count = 0
    
    for i, code in enumerate(etf_codes, 1):
        valuation = get_etf_valuation(code)
        valuations[code] = valuation
        
        # 统计数据来源
        source = valuation.get('data_source', '')
        if 'tushare' in source:
            success_count += 1
        elif 'sector' in source:
            sector_count += 1
        else:
            dividend_count += 1
        
        if i % 10 == 0:
            log_message(f"  进度 {i}/{len(etf_codes)}...")
        
        time.sleep(0.2)  # API 限流
    
    log_message(f"✅ 完成 {len(valuations)}只 ETF 估值")
    log_message(f"  Tushare 真实数据：{success_count}只 ({success_count/len(valuations)*100:.1f}%)")
    log_message(f"  行业中枢估算：{sector_count}只 ({sector_count/len(valuations)*100:.1f}%)")
    log_message(f"  股息率估算：{dividend_count}只 ({dividend_count/len(valuations)*100:.1f}%)")
    
    return valuations

def save_all_valuations(valuations: Dict):
    """保存所有估值数据到统一文件"""
    output_file = f"{CACHE_DIR}/all_valuations_v3.json"
    output_data = {
        'update_time': datetime.now().isoformat(),
        'total_count': len(valuations),
        'data_sources': {
            'tushare': sum(1 for v in valuations.values() if 'tushare' in v.get('data_source', '')),
            'sector_estimate': sum(1 for v in valuations.values() if 'sector' in v.get('data_source', '')),
            'dividend_estimate': sum(1 for v in valuations.values() if 'dividend' in v.get('data_source', ''))
        },
        'valuations': valuations
    }
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    log_message(f"💾 已保存到 {output_file}")

def main():
    """主函数"""
    print("="*70)
    print("估值数据获取模块 v3.0 (Tushare ETF 官方接口)")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    valuations = get_all_etf_valuations(TARGET_ETFS)
    save_all_valuations(valuations)
    
    print("\n" + "="*70)
    print("估值数据汇总")
    print("="*70)
    
    for code, val in sorted(valuations.items()):
        etf_name = str(val.get('etf_name', 'N/A'))[:8]
        pe = val.get('pe')
        pe_pct = val.get('pe_percentile', 0)
        div = val.get('dividend_yield', 0)
        source = str(val.get('data_source', 'N/A'))[:20]
        
        if pe is not None:
            print(f"{code} ({etf_name:8s}): PE={pe:6.1f} PE 分位={pe_pct:5.1f}% 股息率={div:5.2f}%")
        else:
            print(f"{code} ({etf_name:8s}): PE=N/A   PE 分位={pe_pct:5.1f}% 股息率={div:5.2f}% [{source}]")
    
    print(f"\n✅ 完成 {len(valuations)}只 ETF 估值获取")
    print(f"📄 缓存目录：{CACHE_DIR}")
    print(f"💾 汇总文件：{CACHE_DIR}/all_valuations_v3.json")

if __name__ == "__main__":
    main()