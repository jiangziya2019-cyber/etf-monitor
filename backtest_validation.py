#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号回测验证模块
验证行业轮动策略历史表现
"""

import json
import requests
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"
BACKTEST_DIR = Path("/home/admin/openclaw/workspace/backtest_cache")
BACKTEST_DIR.mkdir(exist_ok=True)

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

def get_historical_signals(days=120):
    """获取历史信号"""
    print("获取历史板块数据...")
    
    history = []
    dates = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        data = get_tushare_data("dc_daily", trade_date=date)
        
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            day_data = []
            
            for item in data.get("items", []):
                row = dict(zip(fields, item))
                if row.get("category") != "行业板块":
                    continue
                
                ts_code = row.get("ts_code", "")
                code_short = ts_code.split('.')[0]
                name = SECTOR_NAME_MAP.get(code_short, ts_code)
                pct_change = row.get("pct_change") or 0
                
                day_data.append({
                    "ts_code": ts_code,
                    "name": name,
                    "pct_change": float(pct_change)
                })
            
            # 计算当日信号
            day_data.sort(key=lambda x: x["pct_change"], reverse=True)
            
            # Top 10 为 buy 信号，Bottom 10 为 sell 信号
            for item in day_data[:10]:
                item["signal"] = "buy"
            for item in day_data[-10:]:
                item["signal"] = "sell"
            for item in day_data[10:-10]:
                item["signal"] = "hold"
            
            history.append({"date": date, "sectors": day_data})
            dates.append(date)
    
    print(f"   获取 {len(history)} 个交易日数据")
    return history, dates

def backtest_strategy(history, holding_days=5):
    """回测策略：买入 Top 10，持有 N 天"""
    print(f"回测策略：买入 Top10，持有{holding_days}天...")
    
    trades = []
    cumulative_return = 1.0
    daily_returns = []
    
    for i in range(len(history) - holding_days):
        day = history[i]
        buy_sectors = [s for s in day["sectors"] if s["signal"] == "buy"]
        
        if not buy_sectors:
            daily_returns.append(0)
            continue
        
        # 计算持有期收益
        future_day = history[i + holding_days]
        future_map = {s["ts_code"]: s["pct_change"] for s in future_day["sectors"]}
        
        portfolio_return = 0
        for sector in buy_sectors:
            future_ret = future_map.get(sector["ts_code"], 0)
            portfolio_return += future_ret / len(buy_sectors)
        
        trade_return = portfolio_return / 100 * holding_days  # 简化
        cumulative_return *= (1 + trade_return)
        daily_returns.append(trade_return)
        
        trades.append({
            "date": day["date"],
            "return": trade_return,
            "cumulative": cumulative_return
        })
    
    print(f"   完成 {len(trades)} 笔交易")
    return trades, daily_returns, cumulative_return

def calculate_metrics(trades, daily_returns):
    """计算回测指标"""
    if not trades:
        return {}
    
    # 基础统计
    total_return = (trades[-1]["cumulative"] - 1) * 100
    n_trades = len(trades)
    
    # 胜率
    wins = sum(1 for t in trades if t["return"] > 0)
    win_rate = (wins / n_trades) * 100 if n_trades > 0 else 0
    
    # 盈亏比
    avg_win = np.mean([t["return"] for t in trades if t["return"] > 0]) if wins > 0 else 0
    avg_loss = np.mean([t["return"] for t in trades if t["return"] < 0]) if (n_trades - wins) > 0 else 0
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    # 年化收益
    n_days = len(trades)
    annual_return = ((1 + total_return/100) ** (250/n_days) - 1) * 100 if n_days > 0 else 0
    
    # 波动率
    volatility = np.std(daily_returns) * np.sqrt(250) * 100 if len(daily_returns) > 1 else 0
    
    # 夏普比率
    sharpe = (annual_return - 3) / volatility if volatility > 0 else 0
    
    # 最大回撤
    peak = 1
    max_dd = 0
    cumulative = 1
    for t in trades:
        cumulative = t["cumulative"]
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak
        if dd > max_dd:
            max_dd = dd
    
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "win_rate": win_rate,
        "profit_loss_ratio": profit_loss_ratio,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_dd * 100,
        "n_trades": n_trades,
        "avg_win": avg_win * 100,
        "avg_loss": avg_loss * 100
    }

def generate_report(metrics, holding_days):
    """生成回测报告"""
    lines = ["📊 信号回测验证报告", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    lines.append("━━━ 策略说明 ━━━")
    lines.append(f"策略：买入当日 Top10 板块，持有{holding_days}天")
    lines.append(f"回测期间：最近 120 个交易日")
    lines.append("")
    
    lines.append("━━━ 核心指标 ━━━")
    lines.append(f"总收益率：{metrics.get('total_return', 0):+.2f}%")
    lines.append(f"年化收益：{metrics.get('annual_return', 0):+.2f}%")
    lines.append(f"波动率：{metrics.get('volatility', 0):.2f}%")
    lines.append(f"夏普比率：{metrics.get('sharpe', 0):.2f}")
    lines.append(f"最大回撤：{metrics.get('max_drawdown', 0):.2f}%")
    lines.append("")
    
    lines.append("━━━ 交易统计 ━━━")
    lines.append(f"交易次数：{metrics.get('n_trades', 0)}")
    lines.append(f"胜率：{metrics.get('win_rate', 0):.1f}%")
    lines.append(f"盈亏比：{metrics.get('profit_loss_ratio', 0):.2f}")
    lines.append(f"平均盈利：{metrics.get('avg_win', 0):+.2f}%")
    lines.append(f"平均亏损：{metrics.get('avg_loss', 0):.2f}%")
    lines.append("")
    
    lines.append("━━━ 策略评价 ━━━")
    sharpe = metrics.get('sharpe', 0)
    win_rate = metrics.get('win_rate', 0)
    max_dd = metrics.get('max_drawdown', 0)
    
    if sharpe > 1.5:
        lines.append("✅ 夏普比率优秀 (>1.5)")
    elif sharpe > 1:
        lines.append("✅ 夏普比率良好 (>1)")
    elif sharpe > 0:
        lines.append("⏸️ 夏普比率一般 (>0)")
    else:
        lines.append("⚠️ 夏普比率较差 (<0)")
    
    if win_rate > 60:
        lines.append("✅ 胜率优秀 (>60%)")
    elif win_rate > 50:
        lines.append("⏸️ 胜率一般 (>50%)")
    else:
        lines.append("⚠️ 胜率较低 (<50%)")
    
    if max_dd < 10:
        lines.append("✅ 回撤控制优秀 (<10%)")
    elif max_dd < 20:
        lines.append("⏸️ 回撤控制一般 (<20%)")
    else:
        lines.append("⚠️ 回撤较大 (>20%)")
    
    lines.append("")
    lines.append("━━━ 改进建议 ━━━")
    if sharpe < 0:
        lines.append("• 策略无正向收益，需重新设计信号逻辑")
    if win_rate < 50:
        lines.append("• 胜率偏低，考虑增加过滤条件")
    if max_dd > 20:
        lines.append("• 回撤偏大，建议增加止损机制")
    if metrics.get('profit_loss_ratio', 0) < 1:
        lines.append("• 盈亏比偏低，建议优化止盈止损")
    
    lines.append("")
    lines.append("⚠️ 回测结果仅供参考，不代表未来表现")
    return "\n".join(lines)

def main():
    print("="*60)
    print("信号回测验证")
    print("="*60)
    
    # 1. 获取历史数据
    history, dates = get_historical_signals(days=120)
    
    # 2. 回测策略
    trades, daily_returns, cumulative = backtest_strategy(history, holding_days=5)
    
    # 3. 计算指标
    metrics = calculate_metrics(trades, daily_returns)
    
    # 4. 生成报告
    report = generate_report(metrics, holding_days=5)
    print("\n" + report)
    
    # 5. 保存结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "strategy": "Top10 持有 5 天",
        "metrics": metrics,
        "trades": trades[-20:]  # 只保存最近 20 笔
    }
    
    with open(BACKTEST_DIR / "backtest_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存：{BACKTEST_DIR / 'backtest_result.json'}")
    print("✅ 回测完成")

if __name__ == "__main__":
    main()
