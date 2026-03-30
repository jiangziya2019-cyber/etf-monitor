#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析模块 - 简化版
基于 ETF 持仓的行业分析和资金流向
"""

import json
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path("/home/admin/openclaw/workspace/sector_rotation_cache")
CACHE_DIR.mkdir(exist_ok=True)

# 行业分类映射（基于常见 ETF）
SECTOR_MAP = {
    "科技": ["创业板 AI", "创业智能", "AI 智能", "半导体", "卫星 ETF", "机床 ETF", "储能电池", "纳指 100"],
    "医药": ["医药 ETF"],
    "周期": ["光伏 ETF", "航空 ETF", "航空航天"],
    "商品": ["嘉实原油", "黄金 9999"],
    "宽基": ["创业 50", "300ETF", "500ETF", "标普 500"],
    "策略": ["现金流", "红利 ETF"]
}

def analyze_holdings_sectors(holdings_file="/home/admin/openclaw/workspace/holdings_current.json"):
    """分析持仓的行业分布"""
    
    with open(holdings_file, "r") as f:
        holdings = json.load(f)
    
    etfs = holdings["etfs"]
    total_value = holdings["total_market_value"]
    
    sector_data = {}
    
    for sector, etf_names in SECTOR_MAP.items():
        sector_etfs = [e for e in etfs if e["name"] in etf_names]
        
        if sector_etfs:
            total_mv = sum(e["market_value"] for e in sector_etfs)
            total_profit = sum(e["profit"] for e in sector_etfs)
            avg_yield = sum(e["yield"] for e in sector_etfs) / len(sector_etfs)
            
            # 计算权重
            weight = (total_mv / total_value) * 100 if total_value > 0 else 0
            
            sector_data[sector] = {
                "name": sector,
                "market_value": total_mv,
                "profit": total_profit,
                "avg_yield": avg_yield,
                "weight": weight,
                "etf_count": len(sector_etfs),
                "etfs": [e["name"] for e in sector_etfs]
            }
    
    return sector_data

def generate_rotation_signals(sector_data):
    """生成轮动信号"""
    signals = []
    
    for sector, data in sector_data.items():
        score = 0
        signal = "hold"
        
        # 收益率评分
        if data["avg_yield"] > 5:
            score += 3
            signal = "buy"
        elif data["avg_yield"] > 0:
            score += 2
        elif data["avg_yield"] > -3:
            score += 1
        else:
            score -= 1
            signal = "sell"
        
        # 权重评分（重仓且盈利加分）
        if data["weight"] > 20 and data["avg_yield"] > 0:
            score += 2
        elif data["weight"] > 10:
            score += 1
        
        # 确定最终信号
        if score >= 5:
            signal = "strong_buy"
        elif score >= 3:
            signal = "buy"
        elif score <= 0:
            signal = "sell"
        else:
            signal = "hold"
        
        signals.append({
            "sector": sector,
            "score": score,
            "signal": signal,
            **data
        })
    
    # 按评分排序
    signals.sort(key=lambda x: x["score"], reverse=True)
    
    return signals

def generate_report(signals):
    """生成轮动分析报告"""
    lines = []
    lines.append("📊 行业轮动分析报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    lines.append("━━━ 行业配置概览 ━━━")
    for s in signals:
        weight_bar = "█" * int(s["weight"] / 5)
        lines.append(f"{s['sector']}: {s['weight']:.1f}% {weight_bar} ({s['etf_count']}只，{s['avg_yield']:+.2f}%)")
    lines.append("")
    
    lines.append("━━━ 推荐关注 ━━━")
    buy_signals = [s for s in signals if s["signal"] in ["strong_buy", "buy"]]
    for s in buy_signals:
        icon = "🔥" if s["signal"] == "strong_buy" else "✅"
        lines.append(f"{icon} {s['sector']}: 评分{s['score']} (收益率{s['avg_yield']:+.2f}%, 仓位{s['weight']:.1f}%)")
    
    if not buy_signals:
        lines.append("暂无强烈推荐")
    lines.append("")
    
    lines.append("━━━ 建议回避 ━━━")
    sell_signals = [s for s in signals if s["signal"] == "sell"]
    for s in sell_signals:
        lines.append(f"⚠️ {s['sector']}: 评分{s['score']} (收益率{s['avg_yield']:+.2f}%)")
    
    if not sell_signals:
        lines.append("无需特别回避")
    lines.append("")
    
    lines.append("━━━ 轮动策略建议 ━━━")
    
    # 找出最佳和最差行业
    if signals:
        best = signals[0]
        worst = signals[-1]
        
        lines.append(f"• 最强行业：{best['sector']} ({best['avg_yield']:+.2f}%)")
        lines.append(f"• 最弱行业：{worst['sector']} ({worst['avg_yield']:+.2f}%)")
        
        # 再平衡建议
        if best["score"] - worst["score"] > 3:
            lines.append(f"• 建议：考虑从{worst['sector']}向{best['sector']}适度调仓")
        else:
            lines.append("• 建议：行业配置相对均衡，维持现有配置")
    
    lines.append("")
    lines.append("⚠️ 提示：基于持仓分析，完整轮动需结合全市场数据")
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("=" * 60)
    print("行业轮动分析（持仓版）")
    print("=" * 60)
    
    try:
        sector_data = analyze_holdings_sectors()
        signals = generate_rotation_signals(sector_data)
        report = generate_report(signals)
        
        print("\n" + report)
        
        # 保存数据
        with open(CACHE_DIR / "sector_analysis.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "sector_data": sector_data,
                "signals": signals
            }, f, ensure_ascii=False, indent=2)
        
        print("\n✅ 分析完成")
        
        return signals
        
    except Exception as e:
        print(f"❌ 分析失败：{e}")
        return []

if __name__ == "__main__":
    main()
