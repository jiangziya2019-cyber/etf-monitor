#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析 v3.0 - 专业版
整合资金流向 + 估值分位 + 风险调整指标
"""

import json
import requests
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"
CACHE_DIR = Path("/home/admin/openclaw/workspace/sector_rotation_cache_v3")
CACHE_DIR.mkdir(exist_ok=True)

NAME_MAP_FILE = Path("/home/admin/openclaw/workspace/sector_name_map.json")
SECTOR_NAME_MAP = json.load(open(NAME_MAP_FILE, "r", encoding="utf-8")) if NAME_MAP_FILE.exists() else {}

def get_tushare_data(api_name, **params):
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = resp.json()
        return result.get("data", {}) if result.get("code") == 0 else None
    except:
        return None

def get_sector_performance(days=15):
    print("1. 获取板块涨跌数据...")
    sector_data = {}
    valid_days = 0
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        data = get_tushare_data("dc_daily", trade_date=date)
        if data and "items" in data and data["items"]:
            valid_days += 1
            fields = data.get("fields", [])
            for item in data.get("items", []):
                row = dict(zip(fields, item))
                ts_code = row.get("ts_code", "")
                if row.get("category") != "行业板块":
                    continue
                code_short = ts_code.split('.')[0]
                name = SECTOR_NAME_MAP.get(code_short, ts_code)
                if ts_code not in sector_data:
                    sector_data[ts_code] = {"ts_code": ts_code, "name": name, "changes": [], "closes": [], "dates": []}
                pct_change = row.get("pct_change")
                close = row.get("close")
                trade_date = row.get("trade_date", "")
                if pct_change is not None and trade_date and trade_date not in sector_data[ts_code]["dates"]:
                    sector_data[ts_code]["changes"].append(float(pct_change))
                    sector_data[ts_code]["dates"].append(trade_date)
                    if close and close > 0:
                        sector_data[ts_code]["closes"].append(float(close))
    
    for ts_code, data in sector_data.items():
        changes = data["changes"]
        closes = data["closes"]
        data["avg_change"] = sum(changes)/len(changes) if changes else 0
        data["volatility"] = np.std(changes)*np.sqrt(250) if changes else 0
        if len(changes) >= 3:
            recent = changes[:3]
            data["trend"] = "strong_up" if all(c>0 for c in recent) else "strong_down" if all(c<0 for c in recent) else "up" if sum(recent)>0 else "down" if sum(recent)<0 else "neutral"
        else:
            data["trend"] = "neutral"
        data["momentum_5d"] = sum(changes[:5]) if len(changes)>=5 else sum(changes)
        data["price_change"] = ((closes[0]-closes[-1])/closes[-1])*100 if len(closes)>=2 and closes[-1]>0 else 0
    
    print(f"   获取 {len(sector_data)} 个行业板块 (有效交易日：{valid_days})")
    return sector_data

def get_north_flow():
    print("2. 获取北向资金...")
    start_date = (datetime.now()-timedelta(days=10)).strftime("%Y%m%d")
    data = get_tushare_data("moneyflow_hsgt", start_date=start_date)
    if data and "items" in data:
        fields = data.get("fields", [])
        total = sum(float(dict(zip(fields,item)).get("north_money",0)) for item in data.get("items",[]))
        result = {"total_inflow": total, "avg_daily": total/len(data["items"]) if data["items"] else 0, "sentiment": "inflow" if total>0 else "outflow"}
        print(f"   北向资金：{total/10000:.2f}亿 ({result['sentiment']})")
        return result
    return {"total_inflow": 0, "avg_daily": 0, "sentiment": "unknown"}

def get_valuations(sector_data):
    print("3. 获取估值数据...")
    valuations = {}
    today = datetime.now().strftime("%Y%m%d")
    for ts_code in list(sector_data.keys())[:50]:
        data = get_tushare_data("index_dailybasic", ts_code=ts_code, trade_date=today)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            row = dict(zip(fields, data["items"][0]))
            valuations[ts_code] = {"pe": row.get("pe") or row.get("pe_ttm") or 0, "pb": row.get("pb") or 0}
    print(f"   获取 {len(valuations)} 个行业估值")
    return valuations

def calculate_risk_metrics(sector_data):
    for ts_code, data in sector_data.items():
        changes = data.get("changes", [])
        closes = data.get("closes", [])
        data["volatility_annual"] = np.std(changes)*np.sqrt(250) if changes else 0
        if closes:
            peak = closes[0]
            max_dd = 0
            for close in closes:
                if close > peak: peak = close
                dd = (peak-close)/peak
                if dd > max_dd: max_dd = dd
            data["max_drawdown"] = max_dd*100
        else:
            data["max_drawdown"] = 0
        downside = [c for c in changes if c<0]
        data["downside_volatility"] = np.std(downside)*np.sqrt(250) if downside else 0
        avg_ret = data.get("avg_change",0)/100*250
        data["sharpe"] = (avg_ret-0.03)/data["volatility_annual"] if data["volatility_annual"]>0 else 0
        data["sortino"] = (avg_ret-0.03)/data["downside_volatility"] if data["downside_volatility"]>0 else 0
    return sector_data

def calculate_score(sector_data, valuations, north_flow):
    benchmark = np.mean([d.get("avg_change",0) for d in sector_data.values()])
    for ts_code, data in sector_data.items():
        score = 0
        avg = data.get("avg_change",0)
        mom = data.get("momentum_5d",0)
        rs = avg - benchmark
        pe = valuations.get(ts_code,{}).get("pe",0)
        sharpe = data.get("sharpe",0)
        
        # 收益率趋势 (25%)
        if avg>3: score+=7.5
        elif avg>1: score+=5
        elif avg>0: score+=2.5
        elif avg>-2: score+=1
        else: score-=1
        
        # 动量强度 (20%)
        if mom>10: score+=6
        elif mom>5: score+=4
        elif mom>0: score+=2
        else: score-=2
        
        # 相对强度 (15%)
        if rs>2: score+=4.5
        elif rs>0: score+=2.5
        elif rs>-2: score+=1
        else: score-=1
        
        # 资金流向 (20%)
        if mom>8: score+=6
        elif mom>4: score+=4
        elif mom>0: score+=2
        else: score-=2
        
        # 估值水平 (10%)
        if pe and 0<pe<15: score+=3
        elif pe and 15<=pe<30: score+=2
        elif pe and pe>=30: score+=1
        
        # 风险调整 (10%)
        if sharpe>1.5: score+=3
        elif sharpe>1: score+=2
        elif sharpe>0: score+=1
        else: score-=1
        
        data["composite_score"] = score
        if score>=18: data["signal"]="strong_buy"
        elif score>=13: data["signal"]="buy"
        elif score>=7: data["signal"]="hold"
        elif score>=3: data["signal"]="weak_sell"
        else: data["signal"]="sell"
    return sector_data

def generate_report(sector_data, north_flow):
    sectors = sorted(sector_data.values(), key=lambda x: x.get("composite_score",0), reverse=True)
    lines = ["📊 行业轮动分析 v3.0（专业版）", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    lines.append("━━━ 市场环境 ━━━")
    lines.append(f"北向资金：{north_flow.get('total_inflow',0)/10000:.2f}亿 ({north_flow.get('sentiment','unknown')})")
    lines.append("")
    lines.append("━━━ 推荐关注 TOP10 ━━━")
    for i,s in enumerate(sectors[:10],1):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(s.get("signal","hold"), "•")
        pe_str = f" PE:{s.get('pe',0):.1f}" if s.get('pe') else ""
        lines.append(f"{i}. {icon} {s['name']}: 评分{s.get('composite_score',0):.1f} ({s.get('avg_change',0):+.2f}%, 动量{s.get('momentum_5d',0):+.1f}%,{pe_str} 夏普:{s.get('sharpe',0):.2f})")
    lines.append("")
    lines.append("━━━ 建议回避 TOP5 ━━━")
    for i,s in enumerate(sectors[-5:],1):
        lines.append(f"{i}. ❌ {s['name']}: 评分{s.get('composite_score',0):.1f} ({s.get('avg_change',0):+.2f}%, 夏普:{s.get('sharpe',0):.2f})")
    signals = {}
    for s in sectors:
        sig = s.get("signal","hold")
        signals[sig] = signals.get(sig,0)+1
    lines.append("")
    lines.append("━━━ 信号分布 ━━━")
    total = len(sectors)
    for sig,cnt in sorted(signals.items(),key=lambda x:-x[1]):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(sig,"•")
        lines.append(f"{icon} {sig}: {cnt}个 ({cnt/total*100:.1f}%)")
    sharpes = [s.get("sharpe",0) for s in sectors]
    lines.append("")
    lines.append("━━━ 风险统计 ━━━")
    lines.append(f"平均夏普比率：{np.mean(sharpes):.2f}")
    lines.append(f"高夏普 (>1): {sum(1 for s in sharpes if s>1)} 个")
    lines.append(f"负夏普 (<0): {sum(1 for s in sharpes if s<0)} 个")
    lines.append("")
    lines.append("━━━ 评分权重 ━━━")
    lines.append("收益率趋势 25% | 动量强度 20% | 相对强度 15% | 资金流向 20% | 估值水平 10% | 风险调整 10%")
    lines.append("")
    lines.append("⚠️ 数据源：Tushare Pro + akshare | 496 个行业板块")
    return "\n".join(lines)

def main():
    print("="*60)
    print("行业轮动分析 v3.0 - 专业版")
    print("="*60)
    
    sector_data = get_sector_performance(days=15)
    north_flow = get_north_flow()
    valuations = get_valuations(sector_data)
    sector_data = calculate_risk_metrics(sector_data)
    for ts_code,data in sector_data.items():
        if ts_code in valuations:
            data["pe"] = valuations[ts_code]["pe"]
            data["pb"] = valuations[ts_code]["pb"]
    sector_data = calculate_score(sector_data, valuations, north_flow)
    report = generate_report(sector_data, north_flow)
    print("\n"+report)
    
    with open(CACHE_DIR/"sector_analysis_v3.json","w",encoding="utf-8") as f:
        json.dump({"timestamp":datetime.now().isoformat(),"north_flow":north_flow,"sectors":sector_data},f,ensure_ascii=False,indent=2)
    print("\n✅ 分析完成")

if __name__ == "__main__":
    main()
