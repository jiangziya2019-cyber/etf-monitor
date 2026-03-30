#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析 v4.0 - 增强版
整合美林时钟 + 情绪面指标 + 国际局势影响
"""

import json
import requests
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"
CACHE_DIR = Path("/home/admin/openclaw/workspace/sector_rotation_cache_v4")
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
    print("0. 获取板块数据...")
    sector_data = {}
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        data = get_tushare_data("dc_daily", trade_date=date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            for item in data.get("items", []):
                row = dict(zip(fields, item))
                if row.get("category") != "行业板块": continue
                ts_code = row.get("ts_code", "")
                code_short = ts_code.split('.')[0]
                name = SECTOR_NAME_MAP.get(code_short, ts_code)
                if ts_code not in sector_data:
                    sector_data[ts_code] = {"ts_code": ts_code, "name": name, "changes": [], "closes": []}
                pct = row.get("pct_change")
                close = row.get("close")
                if pct is not None: sector_data[ts_code]["changes"].append(float(pct))
                if close and close > 0: sector_data[ts_code]["closes"].append(float(close))
    
    for ts_code, data in sector_data.items():
        changes = data["changes"]
        data["avg_change"] = sum(changes)/len(changes) if changes else 0
        data["momentum_5d"] = sum(changes[:5]) if len(changes)>=5 else sum(changes)
        if len(changes)>=3:
            recent = changes[:3]
            data["trend"] = "strong_up" if all(c>0 for c in recent) else "strong_down" if all(c<0 for c in recent) else "up" if sum(recent)>0 else "down" if sum(recent)<0 else "neutral"
        else: data["trend"] = "neutral"
        # 基础评分
        score = 0
        avg = data["avg_change"]
        mom = data["momentum_5d"]
        if avg>3: score+=7.5
        elif avg>1: score+=5
        elif avg>0: score+=2.5
        elif avg>-2: score+=1
        else: score-=1
        if mom>10: score+=6
        elif mom>5: score+=4
        elif mom>0: score+=2
        else: score-=2
        data["composite_score"] = score
        if score>=18: data["signal"]="strong_buy"
        elif score>=13: data["signal"]="buy"
        elif score>=7: data["signal"]="hold"
        elif score>=3: data["signal"]="weak_sell"
        else: data["signal"]="sell"
    
    print(f"   获取 {len(sector_data)} 个板块")
    return sector_data

def get_macro_data():
    print("1. 获取宏观经济数据...")
    macro = {"gdp_growth": 5.0, "cpi": 0.5, "pmi": 50.5}
    data = get_tushare_data("cpi", y=2026)
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        macro["cpi"] = dict(zip(fields, data["items"][-1])).get("cpi_m", 0.5)
    data = get_tushare_data("pmi", y=2026)
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        macro["pmi"] = dict(zip(fields, data["items"][-1])).get("pmi", 50.5)
    print(f"   GDP:{macro['gdp_growth']}% CPI:{macro['cpi']}% PMI:{macro['pmi']}")
    return macro

def identify_meilin_clock(macro):
    print("2. 识别美林时钟周期...")
    gdp, cpi, pmi = macro.get("gdp_growth",5), macro.get("cpi",0.5), macro.get("pmi",50)
    growth_strong = gdp>6 or pmi>52
    growth_weak = gdp<4 or pmi<48
    inflation_high = cpi>3
    inflation_low = cpi<0
    if growth_strong and inflation_low: cycle, asset, sectors, desc = "复苏期", "股票", ["科技","周期","金融"], "经济复苏→超配股票"
    elif growth_strong and inflation_high: cycle, asset, sectors, desc = "过热期", "商品", ["商品","能源","材料"], "经济过热→超配商品"
    elif growth_weak and inflation_high: cycle, asset, sectors, desc = "滞胀期", "现金", ["防御","医药","公用事业"], "经济滞胀→持有现金"
    elif growth_weak and inflation_low: cycle, asset, sectors, desc = "衰退期", "债券", ["债券","防御"], "经济衰退→超配债券"
    else: cycle, asset, sectors, desc = "过渡期", "均衡", ["均衡配置"], "周期转换→均衡配置"
    result = {"cycle":cycle, "asset_bias":asset, "sector_bias":sectors, "description":desc}
    print(f"   周期:{cycle} 配置:{asset} 偏好:{','.join(sectors)}")
    return result

def get_sentiment():
    print("3. 获取情绪面指标...")
    data = get_tushare_data("index_dailybasic", ts_code="000300.SH", trade_date=datetime.now().strftime("%Y%m%d"))
    turnover = 1.5
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        turnover = dict(zip(fields, data["items"][0])).get("turnover_rate", 1.5)
    score = 50
    if turnover>2: score+=15
    elif turnover>1: score+=5
    else: score-=10
    score = min(100, max(0, score))
    level = "极度乐观" if score>=70 else "乐观" if score>=60 else "中性" if score>=40 else "悲观" if score>=30 else "极度悲观"
    action = "谨慎追高" if score>=70 else "适度参与" if score>=60 else "观望为主" if score>=40 else "控制仓位" if score>=30 else "寻找机会"
    result = {"score":score, "level":level, "action":action, "turnover":turnover}
    print(f"   评分:{score}/100 等级:{level} 建议:{action}")
    return result

def get_global_events():
    print("4. 评估国际局势...")
    events = {"geopolitical":"stable", "commodity":"neutral", "overall":"neutral"}
    indices = ["DJI","SPX","IXIC","HSI"]
    vols = []
    for idx in indices:
        data = get_tushare_data("index_global", ts_code=idx)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            pct = dict(zip(fields, data["items"][-1])).get("pct_chg", 0)
            if pct: vols.append(abs(pct))
    avg_vol = np.mean(vols) if vols else 1
    if avg_vol>3: events["geopolitical"],events["overall"] = "tense","negative"
    elif avg_vol>2: events["geopolitical"],events["overall"] = "cautious","cautious"
    data = get_tushare_data("fut_daily", ts_code="SC.INE")
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        oil = dict(zip(fields, data["items"][-1])).get("pct_chg", 0)
        if oil and abs(oil)>5: events["commodity"] = "shock" if oil>0 else "drop"
    print(f"   地缘:{events['geopolitical']} 商品:{events['commodity']} 影响:{events['overall']}")
    return events

def adjust_scores(sector_data, meilin, sentiment, global_events):
    print("5. 宏观因子调整评分...")
    sectors_bias = meilin.get("sector_bias", [])
    sent_score = sentiment.get("score", 50)
    global_impact = global_events.get("overall", "neutral")
    adjusted = 0
    for ts_code, data in sector_data.items():
        adj = 0
        name = data.get("name", "")
        for bias in sectors_bias:
            if bias in name: adj += 3; break
        if sent_score>=70: adj += 1
        elif sent_score<=30: adj -= 2
        if global_impact=="negative": adj -= 2
        elif global_impact=="cautious": adj -= 1
        new_score = data.get("composite_score", 0) + adj
        data["adjusted_score"] = new_score
        data["adjustment"] = adj
        if adj != 0: adjusted += 1
        if new_score>=18: data["signal"]="strong_buy"
        elif new_score>=13: data["signal"]="buy"
        elif new_score>=7: data["signal"]="hold"
        elif new_score>=3: data["signal"]="weak_sell"
        else: data["signal"]="sell"
    print(f"   调整{adjusted}个板块")
    return sector_data

def generate_report(sector_data, meilin, sentiment, global_events):
    sectors = sorted(sector_data.values(), key=lambda x: x.get("adjusted_score", x.get("composite_score",0)), reverse=True)
    lines = ["📊 行业轮动 v4.0（增强版）", f"时间:{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append("━━━ 美林时钟 ━━━")
    lines.append(f"周期:{meilin.get('cycle')} 配置:{meilin.get('asset_bias')} 偏好:{','.join(meilin.get('sector_bias',[]))}")
    lines.append(f"说明:{meilin.get('description')}")
    lines.append("")
    lines.append("━━━ 情绪面 ━━━")
    lines.append(f"评分:{sentiment.get('score')}/100 等级:{sentiment.get('level')} 建议:{sentiment.get('action')}")
    lines.append("")
    lines.append("━━━ 国际局势 ━━━")
    lines.append(f"地缘:{global_events.get('geopolitical')} 商品:{global_events.get('commodity')} 影响:{global_events.get('overall')}")
    lines.append("")
    lines.append("━━━ 推荐 TOP10 ━━━")
    for i,s in enumerate(sectors[:10],1):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(s.get("signal","hold"), "•")
        adj = s.get("adjustment",0)
        adj_str = f" (调整{adj:+d})" if adj else ""
        lines.append(f"{i}. {icon} {s['name']}: {s.get('adjusted_score',s.get('composite_score',0)):.1f}{adj_str}")
    lines.append("")
    signals = {}
    for s in sectors:
        sig = s.get("signal","hold")
        signals[sig] = signals.get(sig,0)+1
    lines.append("━━━ 信号分布 ━━━")
    total = len(sectors)
    for sig,cnt in sorted(signals.items(),key=lambda x:-x[1]):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(sig,"•")
        lines.append(f"{icon} {sig}:{cnt}个 ({cnt/total*100:.1f}%)")
    lines.append("")
    lines.append("⚠️ 数据源:Tushare+ 宏观 + 情绪 + 国际局势")
    return "\n".join(lines)

def main():
    print("="*60)
    print("行业轮动 v4.0 - 增强版")
    print("="*60)
    sector_data = get_sector_performance(days=15)
    macro = get_macro_data()
    meilin = identify_meilin_clock(macro)
    sentiment = get_sentiment()
    global_events = get_global_events()
    sector_data = adjust_scores(sector_data, meilin, sentiment, global_events)
    report = generate_report(sector_data, meilin, sentiment, global_events)
    print("\n"+report)
    with open(CACHE_DIR/"sector_analysis_v4.json","w",encoding="utf-8") as f:
        json.dump({"timestamp":datetime.now().isoformat(),"meilin":meilin,"sentiment":sentiment,"global":global_events,"sectors":sector_data},f,ensure_ascii=False,indent=2)
    print("\n✅ 完成")

if __name__ == "__main__":
    main()
