#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 实时行情数据获取模块
创建：2026-03-29
用途：上午观察市场 + 下午实时调仓
"""

import sys, json, requests, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/admin/openclaw/workspace')

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

# 目标 ETF 池（24 只）
TARGET_ETF = {
    # Layer1 防守层
    '510880.SH': '红利 ETF',
    '510300.SH': '沪深 300ETF',
    '159915.SZ': '创业板 ETF',
    '510500.SH': '中证 500ETF',
    
    # Layer2 未来层
    '515790.SH': '光伏 ETF',
    '160723.SZ': '嘉实原油',
    '512760.SH': '芯片 ETF',
    '512010.SH': '医药 ETF',
    '515980.SH': '人工智能 ETF',
    '159663.SZ': '储能电池 ETF',
    '512480.SH': '半导体 ETF',
    '515200.SH': '科创 50ETF',
    
    # Layer3 获利层
    '512660.SH': '军工 ETF',
    '512200.SH': '房地产 ETF',
    '518880.SH': '黄金 9999',
    '515070.SH': '数字经济 ETF',
    '159985.SZ': '豆粕 ETF',
    '159981.SZ': '能源化工 ETF',
    '512880.SH': '券商 ETF',
    '515030.SH': '消费 ETF',
    '512690.SH': '酒 ETF',
    '159937.SZ': '黄金 9999',
    
    # Layer4 全球层
    '513500.SH': '标普 500ETF',
    '513110.SH': '纳指 100ETF',
}

# 目标外 ETF（需要清仓）
EXTRA_ETF = [
    '159566.SZ', '159399.SZ', '159206.SZ',
    '159363.SZ', '159819.SZ', '159243.SZ',
    '159227.SZ', '159241.SZ', '159949.SZ'
]

def get_tushare_data(api_name, **params):
    """通用 Tushare 接口调用"""
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            print(f"❌ 接口错误：{result.get('msg', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ 网络错误：{e}")
        return None

def get_etf_realtime_daily(etf_codes):
    """
    获取 ETF 实时日线行情
    接口：rt_etf_k
    """
    print(f"\n获取 ETF 实时日线...")
    
    # 分沪市和深市
    sh_etf = [code for code in etf_codes if code.endswith('.SH')]
    sz_etf = [code for code in etf_codes if code.endswith('.SZ')]
    
    all_data = {}
    
    # 沪市 ETF
    if sh_etf:
        ts_code_str = ','.join(sh_etf)
        data = get_tushare_data("rt_etf_k", ts_code=ts_code_str, topic='HQ_FND_TICK')
        if data and "items" in data:
            fields = data.get("fields", [])
            for item in data["items"]:
                row = dict(zip(fields, item))
                code = row.get("ts_code", "")
                all_data[code] = {
                    'name': row.get("name", ""),
                    'pre_close': row.get("pre_close", 0),
                    'open': row.get("open", 0),
                    'high': row.get("high", 0),
                    'low': row.get("low", 0),
                    'close': row.get("close", 0),  # 最新价
                    'vol': row.get("vol", 0),
                    'amount': row.get("amount", 0),
                    'change': (row.get("close", 0) - row.get("pre_close", 0)) / row.get("pre_close", 1) * 100 if row.get("pre_close", 0) > 0 else 0,
                    'trade_time': row.get("trade_time", "")
                }
                print(f"  ✅ {code} {row.get('name', '')}: ¥{row.get('close', 0):.3f} ({row.get('change', 0):+.2f}%)")
    
    # 深市 ETF
    if sz_etf:
        ts_code_str = ','.join(sz_etf)
        data = get_tushare_data("rt_etf_k", ts_code=ts_code_str)
        if data and "items" in data:
            fields = data.get("fields", [])
            for item in data["items"]:
                row = dict(zip(fields, item))
                code = row.get("ts_code", "")
                if code not in all_data:  # 避免重复
                    all_data[code] = {
                        'name': row.get("name", ""),
                        'pre_close': row.get("pre_close", 0),
                        'open': row.get("open", 0),
                        'high': row.get("high", 0),
                        'low': row.get("low", 0),
                        'close': row.get("close", 0),
                        'vol': row.get("vol", 0),
                        'amount': row.get("amount", 0),
                        'change': (row.get("close", 0) - row.get("pre_close", 0)) / row.get("pre_close", 1) * 100 if row.get("pre_close", 0) > 0 else 0,
                        'trade_time': row.get("trade_time", "")
                    }
                    print(f"  ✅ {code} {row.get('name', '')}: ¥{row.get('close', 0):.3f} ({row.get('change', 0):+.2f}%)")
    
    return all_data

def get_etf_realtime_minute(etf_codes, freq='5MIN'):
    """
    获取 ETF 实时分钟线
    接口：rt_min
    freq: 1MIN/5MIN/15MIN/30MIN/60MIN
    """
    print(f"\n获取 ETF 实时分钟线 ({freq})...")
    
    all_data = {}
    
    for code in etf_codes:
        data = get_tushare_data("rt_min", ts_code=code, freq=freq)
        if data and "items" in data:
            fields = data.get("fields", [])
            bars = []
            for item in data["items"]:
                row = dict(zip(fields, item))
                bars.append({
                    'time': row.get("time", ""),
                    'open': row.get("open", 0),
                    'high': row.get("high", 0),
                    'low': row.get("low", 0),
                    'close': row.get("close", 0),
                    'vol': row.get("vol", 0),
                    'amount': row.get("amount", 0)
                })
            
            if bars:
                latest = bars[-1]
                all_data[code] = {
                    'latest': latest,
                    'bars': bars[-5:]  # 最近 5 根 K 线
                }
                print(f"  ✅ {code}: {latest['time']} ¥{latest['close']:.3f}")
    
    return all_data

def get_index_realtime():
    """
    获取主要指数实时行情
    """
    print(f"\n获取主要指数实时行情...")
    
    indices = {
        '000001.SH': '上证指数',
        '399006.SZ': '创业板指',
        '000300.SH': '沪深 300',
        '000016.SH': '上证 50',
        '000905.SH': '中证 500'
    }
    
    index_data = {}
    
    for code, name in indices.items():
        # 使用 rt_min 获取最新分钟数据
        data = get_tushare_data("rt_min", ts_code=code, freq='1MIN')
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            latest = dict(zip(fields, data["items"][-1]))
            
            # 获取昨收
            pre_data = get_tushare_data("rt_etf_k", ts_code=code)
            pre_close = 0
            if pre_data and "items" in pre_data and pre_data["items"]:
                pre_fields = pre_data.get("fields", [])
                pre_row = dict(zip(pre_fields, pre_data["items"][0]))
                pre_close = pre_row.get("pre_close", 0)
            
            current = latest.get("close", 0)
            change = (current - pre_close) / pre_close * 100 if pre_close > 0 else 0
            
            index_data[code] = {
                'name': name,
                'current': current,
                'change': change,
                'time': latest.get("time", "")
            }
            print(f"  ✅ {name}: {current:.2f} ({change:+.2f}%)")
    
    return index_data

def generate_market_report(etf_data, index_data):
    """生成市场分析报告"""
    lines = ["📊 实时市场报告", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    # 大盘情况
    lines.append("━━━ 主要指数 ━━━")
    for code, data in index_data.items():
        lines.append(f"{data['name']}: {data['current']:.2f} ({data['change']:+.2f}%)")
    
    # 目标 ETF 表现
    lines.append("")
    lines.append("━━━ 目标 ETF TOP5 ━━━")
    sorted_etf = sorted(etf_data.items(), key=lambda x: x[1]['change'], reverse=True)[:5]
    for code, data in sorted_etf:
        lines.append(f"{code} {data['name']}: ¥{data['close']:.3f} ({data['change']:+.2f}%)")
    
    lines.append("")
    lines.append("━━━ 目标 ETF BOTTOM5 ━━━")
    sorted_etf_bottom = sorted(etf_data.items(), key=lambda x: x[1]['change'])[:5]
    for code, data in sorted_etf_bottom:
        lines.append(f"{code} {data['name']}: ¥{data['close']:.3f} ({data['change']:+.2f}%)")
    
    # 市场情绪判断
    lines.append("")
    lines.append("━━━ 市场情绪 ━━━")
    avg_change = sum(d['change'] for d in etf_data.values()) / len(etf_data)
    if avg_change > 2:
        lines.append("市场情绪：📈 大涨 (>2%)")
        lines.append("建议：✅ 加快补仓，清仓可延后")
    elif avg_change > 0.5:
        lines.append("市场情绪：📈 小涨 (0.5-2%)")
        lines.append("建议：✅ 正常补仓")
    elif avg_change > -0.5:
        lines.append("市场情绪：➖ 震荡 (-0.5%~0.5%)")
        lines.append("建议：✅ 按原计划执行")
    elif avg_change > -2:
        lines.append("市场情绪：📉 小跌 (-0.5~-2%)")
        lines.append("建议：🟡 减缓补仓，正常清仓")
    else:
        lines.append("市场情绪：📉 大跌 (<-2%)")
        lines.append("建议：⏸️ 暂停补仓，仅清仓")
    
    return "\n".join(lines)

def main():
    print("="*70)
    print("Tushare Pro 实时行情数据获取")
    print("="*70)
    
    # 获取所有 ETF 代码
    all_etf_codes = list(TARGET_ETF.keys()) + EXTRA_ETF
    
    # 获取实时日线
    etf_data = get_etf_realtime_daily(all_etf_codes)
    
    # 获取指数行情
    index_data = get_index_realtime()
    
    # 生成报告
    report = generate_market_report(etf_data, index_data)
    print("\n" + report)
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'etf_data': etf_data,
        'index_data': index_data,
        'market_sentiment': 'neutral'
    }
    
    with open('/home/admin/openclaw/workspace/realtime_market_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 数据已保存至 realtime_market_data.json")

if __name__ == "__main__":
    main()
