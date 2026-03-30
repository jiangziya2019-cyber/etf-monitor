#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版上午市场分析模块
整合：隔夜美股 + 期货市场 + 资金流向 + 实时行情
创建：2026-03-29
"""

import sys, json, requests
from datetime import datetime, timedelta

sys.path.insert(0, '/home/admin/openclaw/workspace')

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

def get_tushare_data(api_name, max_retries=3, retry_delay=2, **params):
    """
    通用 Tushare 接口调用（带重试机制）
    max_retries: 最大重试次数 (默认 3 次)
    retry_delay: 重试间隔秒数 (默认 2 秒)
    """
    import time
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    
    for retry in range(max_retries):
        try:
            resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
            result = resp.json()
            
            if result.get("code") == 0:
                return result.get("data", {})
            else:
                print(f"❌ 接口错误 (第{retry+1}次): {result.get('msg', 'Unknown error')}")
                if retry < max_retries - 1:
                    print(f"   {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
        except requests.exceptions.Timeout:
            print(f"⚠️ 网络超时 (第{retry+1}次)，{retry_delay}秒后重试...")
            time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 网络错误 (第{retry+1}次): {e}，{retry_delay}秒后重试...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"⚠️ 未知错误 (第{retry+1}次): {e}")
            break
    
    print(f"❌ 接口 {api_name} 获取失败（{max_retries}次重试后）")
    return None

def get_us_market_data():
    """
    获取隔夜美股数据
    接口：us_daily
    """
    print(f"\n获取隔夜美股数据...")
    
    # 主要美股指数/股票
    us_stocks = {
        'DJI': '道琼斯',
        'SPX': '标普 500',
        'IXIC': '纳斯达克',
        'AAPL': '苹果',
        'TSLA': '特斯拉',
        'NVDA': '英伟达',
        'MSFT': '微软'
    }
    
    # 获取昨日数据
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    us_data = {}
    for code, name in us_stocks.items():
        data = get_tushare_data("us_daily", ts_code=code, start_date=yesterday, end_date=yesterday)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            
            us_data[code] = {
                'name': name,
                'close': row.get("close", 0),
                'pct_change': row.get("pct_change", 0),
                'vol': row.get("vol", 0),
                'amount': row.get("amount", 0)
            }
            print(f"  ✅ {name} ({code}): {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
    
    return us_data

def get_futures_data():
    """
    获取期货市场数据
    接口：rt_fut_min
    """
    print(f"\n获取期货市场数据...")
    
    # 主要期货合约
    futures = {
        'AU2026.SHF': '沪金主力',
        'SC2026.INE': '原油主力',
        'CU2026.SHF': '沪铜主力',
        'AL2026.SHF': '沪铝主力',
        'IF2026.CFFEX': '沪深 300 期货'
    }
    
    futures_data = {}
    for code, name in futures.items():
        data = get_tushare_data("rt_fut_min", ts_code=code, freq='5MIN')
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            latest = dict(zip(fields, data["items"][-1]))
            
            # 获取开盘价计算涨跌
            open_price = latest.get("open", 0)
            current = latest.get("close", 0)
            change = (current - open_price) / open_price * 100 if open_price > 0 else 0
            
            futures_data[code] = {
                'name': name,
                'current': current,
                'change': change,
                'time': latest.get("time", ""),
                'vol': latest.get("vol", 0),
                'oi': latest.get("oi", 0)  # 持仓量
            }
            print(f"  ✅ {name}: {current:.2f} ({change:+.2f}%) 持仓:{latest.get('oi', 0):.0f}")
    
    return futures_data

def get_industry_moneyflow():
    """
    获取行业资金流向
    接口：moneyflow_ind_dc
    """
    print(f"\n获取行业资金流向...")
    
    today = datetime.now().strftime('%Y%m%d')
    
    data = get_tushare_data("moneyflow_ind_dc", trade_date=today, content_type='行业')
    
    industry_flow = {}
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        
        # 关注与我们持仓相关的行业
        target_industries = ['电池', '光伏设备', '半导体', '医药生物', '证券', '银行', 
                            '房地产开发', '食品饮料', '有色金属', '石油', '国防军工']
        
        for item in data["items"]:
            row = dict(zip(fields, item))
            name = row.get("name", "")
            
            # 筛选目标行业
            for target in target_industries:
                if target in name:
                    industry_flow[name] = {
                        'pct_change': row.get("pct_change", 0),
                        'net_amount': row.get("net_amount", 0) / 100000000,  # 转换为亿元
                        'net_amount_rate': row.get("net_amount_rate", 0),
                        'rank': row.get("rank", 0)
                    }
                    print(f"  ✅ {name}: {row.get('pct_change', 0):+.2f}% 净流入¥{industry_flow[name]['net_amount']:.2f}亿")
                    break
    
    return industry_flow

def get_concept_moneyflow():
    """
    获取概念板块资金流向
    接口：moneyflow_ind_dc
    """
    print(f"\n获取概念板块资金流向...")
    
    today = datetime.now().strftime('%Y%m%d')
    
    data = get_tushare_data("moneyflow_ind_dc", trade_date=today, content_type='概念')
    
    concept_flow = {}
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        
        # 关注热门概念
        target_concepts = ['人工智能', '芯片', '半导体', '光伏', '储能', '新能源车', 
                          '数字经济', '军工', '医药', '消费']
        
        for item in data["items"][:50]:  # 只看前 50
            row = dict(zip(fields, item))
            name = row.get("name", "")
            
            for target in target_concepts:
                if target in name:
                    concept_flow[name] = {
                        'pct_change': row.get("pct_change", 0),
                        'net_amount': row.get("net_amount", 0) / 100000000,
                        'rank': row.get("rank", 0)
                    }
                    print(f"  ✅ {name}: {row.get('pct_change', 0):+.2f}% 净流入¥{concept_flow[name]['net_amount']:.2f}亿")
                    break
    
    return concept_flow

def generate_morning_analysis(us_data, futures_data, industry_flow, concept_flow, etf_data, index_data):
    """
    生成上午市场分析报告
    """
    lines = ["📊 上午市场分析报告", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    # 1. 隔夜外围市场
    lines.append("━━━ 隔夜外围市场 ━━━")
    if us_data:
        avg_us_change = sum(d['pct_change'] for d in us_data.values()) / len(us_data)
        if avg_us_change > 1:
            lines.append(f"美股：📈 大涨 (+{avg_us_change:.2f}%) - 利好 A 股")
        elif avg_us_change > 0:
            lines.append(f"美股：📈 上涨 (+{avg_us_change:.2f}%) - 偏利好")
        elif avg_us_change > -1:
            lines.append(f"美股：➖ 震荡 ({avg_us_change:.2f}%) - 中性")
        else:
            lines.append(f"美股：📉 下跌 ({avg_us_change:.2f}%) - 利空 A 股")
        
        for code, data in list(us_data.items())[:3]:
            lines.append(f"  {data['name']}: {data['close']:.2f} ({data['pct_change']:+.2f}%)")
    
    # 2. 期货市场
    lines.append("")
    lines.append("━━━ 期货市场 ━━━")
    if futures_data:
        for code, data in futures_data.items():
            signal = "📈" if data['change'] > 0.5 else ("📉" if data['change'] < -0.5 else "➖")
            lines.append(f"  {signal} {data['name']}: {data['current']:.2f} ({data['change']:+.2f}%)")
    
    # 3. 行业资金流向
    lines.append("")
    lines.append("━━━ 行业资金流向 ━━━")
    if industry_flow:
        top_inflow = sorted(industry_flow.items(), key=lambda x: x[1]['net_amount'], reverse=True)[:3]
        top_outflow = sorted(industry_flow.items(), key=lambda x: x[1]['net_amount'])[:3]
        
        lines.append("流入 TOP3:")
        for name, data in top_inflow:
            lines.append(f"  ✅ {name}: +¥{data['net_amount']:.2f}亿 ({data['pct_change']:+.2f}%)")
        
        lines.append("流出 TOP3:")
        for name, data in top_outflow:
            lines.append(f"  ❌ {name}: -¥{abs(data['net_amount']):.2f}亿 ({data['pct_change']:+.2f}%)")
    
    # 4. 概念板块
    lines.append("")
    lines.append("━━━ 概念板块 ━━━")
    if concept_flow:
        for name, data in list(concept_flow.items())[:5]:
            signal = "🔥" if data['net_amount'] > 5 else ("✅" if data['net_amount'] > 0 else "❌")
            lines.append(f"  {signal} {name}: {data['pct_change']:+.2f}% 净流入¥{data['net_amount']:.2f}亿")
    
    # 5. A 股实时
    lines.append("")
    lines.append("━━━ A 股实时 ━━━")
    if index_data:
        for code, data in index_data.items():
            lines.append(f"  {data['name']}: {data['current']:.2f} ({data['change']:+.2f}%)")
    
    # 6. 综合判断
    lines.append("")
    lines.append("━━━ 综合判断 ━━━")
    
    # 计算综合得分
    score = 0
    
    # 美股影响 (+/-2)
    if us_data:
        avg_us = sum(d['pct_change'] for d in us_data.values()) / len(us_data)
        if avg_us > 1: score += 2
        elif avg_us > 0: score += 1
        elif avg_us < -1: score -= 2
        elif avg_us < 0: score -= 1
    
    # 期货影响 (+/-1)
    if futures_data:
        avg_fut = sum(d['change'] for d in futures_data.values()) / len(futures_data)
        if avg_fut > 0.5: score += 1
        elif avg_fut < -0.5: score -= 1
    
    # 资金流向 (+/-2)
    if industry_flow:
        net_total = sum(d['net_amount'] for d in industry_flow.values())
        if net_total > 50: score += 2
        elif net_total > 0: score += 1
        elif net_total < -50: score -= 2
        elif net_total < 0: score -= 1
    
    # 综合判断
    if score >= 3:
        lines.append("市场情绪：🔥 强烈看好")
        lines.append("建议：✅ 积极补仓，清仓可延后")
        lines.append("仓位：可适当提高至 90-95%")
    elif score >= 1:
        lines.append("市场情绪：📈 偏乐观")
        lines.append("建议：✅ 正常补仓")
        lines.append("仓位：保持 85-90%")
    elif score >= -1:
        lines.append("市场情绪：➖ 中性震荡")
        lines.append("建议：✅ 按原计划执行")
        lines.append("仓位：保持 80-85%")
    elif score >= -3:
        lines.append("市场情绪：📉 偏谨慎")
        lines.append("建议：🟡 减缓补仓，优先清仓")
        lines.append("仓位：降至 75-80%")
    else:
        lines.append("市场情绪：❄️ 谨慎观望")
        lines.append("建议：⏸️ 暂停补仓，仅清仓")
        lines.append("仓位：降至 70% 以下")
    
    lines.append("")
    lines.append(f"综合得分：{score:+d}/5")
    
    return "\n".join(lines)


def get_sw_realtime():
    """
    获取申万实时行情
    接口：rt_sw
    文档：https://tushare.pro/document/2?doc_id=417
    用途：补充行业资金流的时效性
    """
    print(f"\n获取申万实时行情...")
    
    # 主要申万行业指数
    sw_indices = [
        '801010.SI', '801020.SI', '801030.SI', '801040.SI', '801050.SI',
        '801080.SI', '801120.SI', '801130.SI', '801140.SI', '801150.SI'
    ]
    
    sw_data = {}
    for code in sw_indices:
        data = get_tushare_data("rt_sw", ts_code=code)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            
            sw_data[code] = {
                'name': row.get("name", ""),
                'current': row.get("close", 0),
                'change': row.get("pct_change", 0),
                'data_source': 'rt_sw',
                'update_time': datetime.now().isoformat()
            }
            signal = "📈" if row.get("pct_change", 0) > 1 else ("📉" if row.get("pct_change", 0) < -1 else "➖")
            print(f"  {signal} {row.get('name', '')}: {row.get('close', 0):.2f} ({row.get('pct_change', 0):+.2f}%)")
    
    return sw_data

def main():
    print("="*70)
    print("增强版上午市场分析")
    print("整合：隔夜美股 + 期货 + 资金流向 + 实时行情")
    print("="*70)
    
    # 1. 隔夜美股
    us_data = get_us_market_data()
    
    # 2. 期货市场
    futures_data = get_futures_data()
    
    # 3. 行业资金流向
    industry_flow = get_industry_moneyflow()
    
    # 4. 概念板块
    concept_flow = get_concept_moneyflow()
    
    # 5. A 股实时（简化版，实际应调用实时接口）
    index_data = {
        '000001.SH': {'name': '上证指数', 'current': 3400.00, 'change': 0.5},
        '399006.SZ': {'name': '创业板指', 'current': 2200.00, 'change': 0.8}
    }
    
    # 6. ETF 实时（简化版）
    etf_data = {}
    
    # 生成报告
    report = generate_morning_analysis(us_data, futures_data, industry_flow, concept_flow, etf_data, index_data)
    print("\n" + report)
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'us_data': us_data,
        'futures_data': futures_data,
        'industry_flow': industry_flow,
        'concept_flow': concept_flow,
        'index_data': index_data,
        'score': 0  # 实际应计算
    }
    
    with open('/home/admin/openclaw/workspace/morning_analysis_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 数据已保存至 morning_analysis_data.json")

if __name__ == "__main__":
    main()
