#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析 v2.0 - 增强版（使用 dc_daily 数据）
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tushare 配置
TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

CACHE_DIR = Path("/home/admin/openclaw/workspace/sector_rotation_cache_v2")
CACHE_DIR.mkdir(exist_ok=True)

# 加载板块名称映射
NAME_MAP_FILE = Path("/home/admin/openclaw/workspace/sector_name_map.json")
SECTOR_NAME_MAP = {}
if NAME_MAP_FILE.exists():
    with open(NAME_MAP_FILE, "r", encoding="utf-8") as f:
        SECTOR_NAME_MAP = json.load(f)

def get_tushare_data(api_name, **params):
    """调用 Tushare Pro API"""
    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params
    }
    try:
        response = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = response.json()
        if result.get("code") == 0:
            return result.get("data", {})
        return None
    except Exception as e:
        return None

def get_sector_performance(days=10):
    """获取板块涨跌数据"""
    print("获取板块涨跌数据...")
    
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
                category = row.get("category", "")
                
                # 只处理行业板块
                if category != "行业板块":
                    continue
                
                # 使用 ts_code 作为 key，从映射表获取名称
                if ts_code and ts_code not in sector_data:
                    # 提取代码部分（去掉.DC 后缀）
                    code_short = ts_code.split('.')[0] if '.' in ts_code else ts_code
                    name = SECTOR_NAME_MAP.get(code_short, row.get("name") or ts_code)
                    
                    sector_data[ts_code] = {
                        "ts_code": ts_code,
                        "name": name,
                        "changes": [],
                        "closes": [],
                        "dates": []
                    }
                
                pct_change = row.get("pct_change")
                close = row.get("close")
                trade_date = row.get("trade_date", "")
                
                if pct_change is not None and trade_date:
                    if trade_date not in sector_data[ts_code]["dates"]:
                        sector_data[ts_code]["changes"].append(float(pct_change))
                        sector_data[ts_code]["dates"].append(trade_date)
                        if close and close > 0:
                            sector_data[ts_code]["closes"].append(float(close))
    
    # 计算指标
    for ts_code, data in sector_data.items():
        changes = data["changes"]
        closes = data["closes"]
        
        data["avg_change"] = sum(changes) / len(changes) if changes else 0
        
        # 趋势
        if len(changes) >= 3:
            recent = changes[:3]
            if all(c > 0 for c in recent):
                data["trend"] = "strong_up"
            elif all(c < 0 for c in recent):
                data["trend"] = "strong_down"
            elif sum(recent) > 0:
                data["trend"] = "up"
            else:
                data["trend"] = "down"
        else:
            data["trend"] = "neutral"
        
        # 动量
        data["momentum_5d"] = sum(changes[:5]) if len(changes) >= 5 else sum(changes)
        
        # 价格变化
        if len(closes) >= 2:
            data["price_change"] = ((closes[0] - closes[-1]) / closes[-1]) * 100 if closes[-1] > 0 else 0
        
        # 更新名称（如果有）
        if data["name"] == ts_code:
            data["name"] = f"行业{ts_code[:6]}"
    
    print(f"  获取 {len(sector_data)} 个行业板块 (有效交易日：{valid_days})")
    return sector_data

def calculate_score(sector_data):
    """计算综合评分"""
    for ts_code, data in sector_data.items():
        score = 0
        
        # 收益率趋势 (30%)
        avg = data.get("avg_change", 0)
        if avg > 3: score += 9
        elif avg > 1: score += 6
        elif avg > 0: score += 3
        elif avg > -2: score += 1
        else: score -= 2
        
        # 动量强度 (25%)
        mom = data.get("momentum_5d", 0)
        if mom > 10: score += 7.5
        elif mom > 5: score += 5
        elif mom > 0: score += 2.5
        else: score -= 2.5
        
        # 相对强度 (20%)
        pc = data.get("price_change", 0)
        if pc > 10: score += 6
        elif pc > 5: score += 4
        elif pc > 0: score += 2
        else: score -= 1
        
        # 趋势信号 (15%)
        trend = data.get("trend", "neutral")
        if trend == "strong_up": score += 4.5
        elif trend == "up": score += 3
        elif trend == "neutral": score += 1.5
        elif trend == "down": score -= 1.5
        else: score -= 3
        
        # 波动性 (10%) - 低波动加分
        changes = data.get("changes", [])
        if changes:
            vol = sum(abs(c) for c in changes) / len(changes)
            if vol < 2: score += 3
            elif vol < 3: score += 2
            elif vol < 4: score += 1
            else: score -= 1
        
        data["composite_score"] = score
        
        # 信号
        if score >= 18: data["signal"] = "strong_buy"
        elif score >= 13: data["signal"] = "buy"
        elif score >= 6: data["signal"] = "hold"
        elif score >= 2: data["signal"] = "weak_sell"
        else: data["signal"] = "sell"
    
    return sector_data

def generate_report(sector_data):
    """生成报告"""
    sectors = sorted(sector_data.values(), key=lambda x: x.get("composite_score", 0), reverse=True)
    
    lines = ["📊 行业轮动分析 v2.0（增强版）"]
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("━━━ 推荐关注 TOP10 ━━━")
    
    for i, s in enumerate(sectors[:10], 1):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(s.get("signal","hold"), "•")
        lines.append(f"{i}. {icon} {s['name']}: 评分{s.get('composite_score',0):.1f} ({s.get('avg_change',0):+.2f}%, 动量{s.get('momentum_5d',0):+.1f}%)")
    
    lines.append("")
    lines.append("━━━ 建议回避 TOP5 ━━━")
    for i, s in enumerate(sectors[-5:], 1):
        lines.append(f"{i}. ❌ {s['name']}: 评分{s.get('composite_score',0):.1f} ({s.get('avg_change',0):+.2f}%)")
    
    # 信号分布
    signals = {}
    for s in sectors:
        sig = s.get("signal", "hold")
        signals[sig] = signals.get(sig, 0) + 1
    
    lines.append("")
    lines.append("━━━ 信号分布 ━━━")
    for sig, cnt in sorted(signals.items()):
        icon = {"strong_buy":"🔥","buy":"✅","hold":"⏸️","weak_sell":"⚠️","sell":"❌"}.get(sig, "•")
        lines.append(f"{icon} {sig}: {cnt}个")
    
    lines.append("")
    lines.append("━━━ 评分权重 ━━━")
    lines.append("• 收益率趋势：30%  • 动量强度：25%  • 相对强度：20%")
    lines.append("• 趋势信号：15%  • 波动性：10%")
    lines.append("")
    lines.append("⚠️ 数据源：Tushare Pro 板块指数（496 个行业板块）")
    
    return "\n".join(lines)

def main():
    print("=" * 60)
    print("行业轮动分析 v2.0 - 增强版")
    print("=" * 60)
    
    sector_data = get_sector_performance(days=10)
    sector_data = calculate_score(sector_data)
    report = generate_report(sector_data)
    
    print("\n" + report)
    
    # 保存
    with open(CACHE_DIR / "sector_analysis_v2.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "sectors": sector_data}, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 分析完成")

if __name__ == "__main__":
    main()
