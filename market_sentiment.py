#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪指标模块
监控恐慌指数、成交量、市场宽度等情绪指标
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Tushare 配置
TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

CACHE_DIR = Path("/home/admin/openclaw/workspace/sentiment_cache")
CACHE_DIR.mkdir(exist_ok=True)

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
        print(f"请求失败：{e}")
        return None

def get_vix_like_index():
    """获取类 VIX 恐慌指数（使用 A 股波动率替代）"""
    # 获取上证 50ETF 期权隐含波动率（如果有）
    # 或使用市场波动率替代
    
    # 这里使用 300ETF 的波动率作为替代
    data = get_tushare_data("index_dailybasic", ts_code="000300.SH", start_date=(datetime.now()-timedelta(days=30)).strftime("%Y%m%d"))
    
    if data and "items" in data:
        items = data.get("items", [])
        if items:
            # 取最近的数据
            latest = items[-1]
            fields = data.get("fields", [])
            row = dict(zip(fields, latest))
            
            # 使用涨跌幅标准差作为波动率代理
            return {
                "value": row.get("pct_chg", 0),
                "level": "high" if abs(row.get("pct_chg", 0)) > 3 else "normal"
            }
    
    return {"value": 0, "level": "unknown"}

def get_market_breadth():
    """获取市场宽度指标（涨跌家数比）"""
    try:
        # 获取涨跌分布
        data = get_tushare_data("daily_info", trade_date=datetime.now().strftime("%Y%m%d"))
        
        if data and "items" in data:
            items = data.get("items", [])
            
            up_count = 0
            down_count = 0
            
            for item in items:
                fields = data.get("fields", [])
                row = dict(zip(fields, item))
                pct_chg = row.get("pct_chg", 0)
                
                if pct_chg > 0:
                    up_count += 1
                elif pct_chg < 0:
                    down_count += 1
            
            total = up_count + down_count
            ratio = up_count / down_count if down_count > 0 else float('inf')
            
            return {
                "up_count": up_count,
                "down_count": down_count,
                "ratio": ratio,
                "sentiment": "bullish" if ratio > 1.5 else "bearish" if ratio < 0.7 else "neutral"
            }
    except Exception as e:
        print(f"获取市场宽度失败：{e}")
    
    return {"up_count": 0, "down_count": 0, "ratio": 1, "sentiment": "unknown"}

def get_volume_analysis():
    """成交量分析"""
    # 获取 300ETF 成交量数据
    data = get_tushare_data("index_daily", ts_code="000300.SH", start_date=(datetime.now()-timedelta(days=20)).strftime("%Y%m%d"))
    
    if data and "items" in data:
        items = data.get("items", [])
        if len(items) >= 5:
            # 计算 5 日平均成交量
            fields = data.get("fields", [])
            volumes = []
            
            for item in items[:5]:
                row = dict(zip(fields, item))
                vol = row.get("vol", 0)
                if vol:
                    volumes.append(vol)
            
            if volumes:
                avg_vol = sum(volumes) / len(volumes)
                latest_vol = volumes[0] if volumes else 0
                vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1
                
                return {
                    "latest_vol": latest_vol,
                    "avg_vol": avg_vol,
                    "ratio": vol_ratio,
                    "sentiment": "high" if vol_ratio > 1.5 else "low" if vol_ratio < 0.7 else "normal"
                }
    
    return {"latest_vol": 0, "avg_vol": 0, "ratio": 1, "sentiment": "unknown"}

def get_north_flow():
    """北向资金流向"""
    try:
        # 获取北向资金数据
        data = get_tushare_data("moneyflow_hsgt", start_date=(datetime.now()-timedelta(days=5)).strftime("%Y%m%d"))
        
        if data and "items" in data:
            items = data.get("items", [])
            if items:
                fields = data.get("fields", [])
                
                # 计算最近 5 日净流入
                total_inflow = 0
                for item in items[:5]:
                    row = dict(zip(fields, item))
                    inflow = row.get("net_in", 0)
                    if inflow:
                        total_inflow += inflow
                
                return {
                    "total_inflow": total_inflow,
                    "avg_daily": total_inflow / min(len(items), 5),
                    "sentiment": "inflow" if total_inflow > 0 else "outflow"
                }
    except Exception as e:
        print(f"获取北向资金失败：{e}")
    
    return {"total_inflow": 0, "avg_daily": 0, "sentiment": "unknown"}

def calculate_sentiment_score(vix, breadth, volume, north_flow):
    """计算综合情绪评分"""
    score = 50  # 中性起点
    
    # 波动率影响（高波动减分）
    if vix.get("level") == "high":
        score -= 15
    elif vix.get("level") == "normal":
        score += 0
    
    # 市场宽度影响
    breadth_sentiment = breadth.get("sentiment", "neutral")
    if breadth_sentiment == "bullish":
        score += 15
    elif breadth_sentiment == "bearish":
        score -= 15
    
    # 成交量影响
    vol_sentiment = volume.get("sentiment", "normal")
    if vol_sentiment == "high":
        score += 10  # 放量通常利好
    elif vol_sentiment == "low":
        score -= 5
    
    # 北向资金影响
    if north_flow.get("sentiment") == "inflow":
        score += 10
    elif north_flow.get("sentiment") == "outflow":
        score -= 10
    
    # 限制在 0-100 范围
    score = max(0, min(100, score))
    
    # 情绪等级
    if score >= 70:
        level = "极度乐观"
        action = "谨慎追高"
    elif score >= 60:
        level = "乐观"
        action = "适度参与"
    elif score >= 40:
        level = "中性"
        action = "观望为主"
    elif score >= 30:
        level = "悲观"
        action = "控制仓位"
    else:
        level = "极度悲观"
        action = "寻找机会"
    
    return {
        "score": score,
        "level": level,
        "action": action
    }

def generate_report(vix, breadth, volume, north_flow, sentiment):
    """生成情绪报告"""
    lines = []
    lines.append("📊 市场情绪指标")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("━━━ 综合情绪 ━━━")
    score_bar = "█" * int(sentiment["score"] / 10)
    lines.append(f"情绪评分：{sentiment['score']}/100 {score_bar}")
    lines.append(f"情绪等级：{sentiment['level']}")
    lines.append(f"操作建议：{sentiment['action']}")
    lines.append("")
    
    lines.append("━━━ 分项指标 ━━━")
    
    # 波动率
    vix_icon = "⚠️" if vix.get("level") == "high" else "✅"
    lines.append(f"{vix_icon} 波动率：{vix.get('value', 0):.2f}% ({vix.get('level', 'unknown')})")
    
    # 市场宽度
    breadth_icon = {"bullish": "🐂", "bearish": "🐻", "neutral": "➖"}.get(breadth.get("sentiment"), "❓")
    lines.append(f"{breadth_icon} 涨跌比：{breadth.get('ratio', 0):.2f} (涨{breadth.get('up_count', 0)}/跌{breadth.get('down_count', 0)})")
    
    # 成交量
    vol_icon = {"high": "📈", "low": "📉", "normal": "➖"}.get(volume.get("sentiment"), "❓")
    lines.append(f"{vol_icon} 成交量：{volume.get('ratio', 0):.2f}x 均值 ({volume.get('sentiment', 'unknown')})")
    
    # 北向资金
    flow_icon = "💰" if north_flow.get("sentiment") == "inflow" else "💸" if north_flow.get("sentiment") == "outflow" else "❓"
    lines.append(f"{flow_icon} 北向资金：{north_flow.get('total_inflow', 0)/10000:.2f}亿 ({north_flow.get('sentiment', 'unknown')})")
    
    lines.append("")
    lines.append("━━━ 情绪解读 ━━━")
    
    if sentiment["score"] >= 70:
        lines.append("市场情绪过热，注意回调风险，不宜追高")
    elif sentiment["score"] >= 60:
        lines.append("市场情绪积极，可适度参与强势品种")
    elif sentiment["score"] >= 40:
        lines.append("市场情绪中性，观望为主，等待明确信号")
    elif sentiment["score"] >= 30:
        lines.append("市场情绪偏冷，控制仓位，关注防御品种")
    else:
        lines.append("市场情绪极度悲观，可能是布局机会")
    
    lines.append("")
    lines.append("⚠️ 提示：情绪指标仅供参考，需结合技术面和基本面")
    
    return "\n".join(lines)

def save_cache(data, filename):
    """保存缓存"""
    with open(CACHE_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    print("=" * 60)
    print("市场情绪指标")
    print("=" * 60)
    
    # 获取各项指标
    print("获取波动率数据...")
    vix = get_vix_like_index()
    
    print("获取市场宽度数据...")
    breadth = get_market_breadth()
    
    print("获取成交量数据...")
    volume = get_volume_analysis()
    
    print("获取北向资金数据...")
    north_flow = get_north_flow()
    
    # 计算综合情绪
    sentiment = calculate_sentiment_score(vix, breadth, volume, north_flow)
    
    # 生成报告
    report = generate_report(vix, breadth, volume, north_flow, sentiment)
    print("\n" + report)
    
    # 保存数据
    save_cache({
        "timestamp": datetime.now().isoformat(),
        "vix": vix,
        "breadth": breadth,
        "volume": volume,
        "north_flow": north_flow,
        "sentiment": sentiment
    }, "sentiment_data.json")
    
    print("\n✅ 分析完成")
    
    return sentiment

if __name__ == "__main__":
    main()
