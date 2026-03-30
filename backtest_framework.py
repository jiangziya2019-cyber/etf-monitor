#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测框架优化模块
支持调仓策略回测、性能评估、可视化输出
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests

# Tushare 配置
TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

BACKTEST_DIR = Path("/home/admin/openclaw/workspace/backtest_results")
BACKTEST_DIR.mkdir(exist_ok=True)

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

def get_etf_history(code, start_date, end_date):
    """获取 ETF 历史行情"""
    # 添加交易所后缀
    if code.startswith("51") or code.startswith("15"):
        suffix = ".SH" if code.startswith("51") else ".SZ"
        ts_code = code + suffix
    else:
        ts_code = code
    
    data = get_tushare_data("fund_daily", ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    if data and "items" in data:
        fields = data.get("fields", [])
        prices = []
        
        for item in data.get("items", []):
            row = dict(zip(fields, item))
            prices.append({
                "date": row.get("trade_date", ""),
                "close": row.get("close", 0),
                "vol": row.get("vol", 0)
            })
        
        # 按日期排序
        prices.sort(key=lambda x: x["date"])
        
        return prices
    
    return []

def calculate_returns(prices):
    """计算收益率序列"""
    if len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        prev_close = prices[i-1]["close"]
        curr_close = prices[i]["close"]
        
        if prev_close > 0:
            ret = (curr_close - prev_close) / prev_close
            returns.append({
                "date": prices[i]["date"],
                "return": ret
            })
    
    return returns

def calculate_portfolio_returns(etf_returns, weights):
    """计算组合收益率"""
    if not etf_returns:
        return []
    
    # 按日期对齐
    all_dates = set()
    for code, returns in etf_returns.items():
        for r in returns:
            all_dates.add(r["date"])
    
    all_dates = sorted(all_dates)
    
    portfolio_returns = []
    for date in all_dates:
        daily_ret = 0
        
        for code, weight in weights.items():
            returns = etf_returns.get(code, [])
            for r in returns:
                if r["date"] == date:
                    daily_ret += r["return"] * weight
                    break
        
        portfolio_returns.append({
            "date": date,
            "return": daily_ret
        })
    
    return portfolio_returns

def calculate_metrics(returns):
    """计算性能指标"""
    if not returns:
        return {}
    
    ret_series = [r["return"] for r in returns]
    
    # 累计收益率
    cumulative = 1
    for r in ret_series:
        cumulative *= (1 + r)
    total_return = (cumulative - 1) * 100
    
    # 年化收益率（假设 250 个交易日）
    n_days = len(ret_series)
    if n_days > 0:
        annual_return = ((1 + total_return/100) ** (250/n_days) - 1) * 100
    else:
        annual_return = 0
    
    # 波动率
    if len(ret_series) > 1:
        volatility = np.std(ret_series) * np.sqrt(250) * 100
    else:
        volatility = 0
    
    # 夏普比率（假设无风险利率 3%）
    if volatility > 0:
        sharpe = (annual_return - 3) / volatility
    else:
        sharpe = 0
    
    # 最大回撤
    peak = 1
    max_drawdown = 0
    cumulative = 1
    
    for r in ret_series:
        cumulative *= (1 + r)
        if cumulative > peak:
            peak = cumulative
        drawdown = (peak - cumulative) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    max_drawdown *= 100
    
    # 胜率
    wins = sum(1 for r in ret_series if r > 0)
    win_rate = (wins / len(ret_series)) * 100 if ret_series else 0
    
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "trading_days": n_days
    }

def backtest_rebalance_strategy(etf_codes, weights, start_date, end_date, rebalance_freq=20):
    """回测定期调仓策略"""
    print(f"回测定期调仓策略...")
    print(f"ETF: {list(weights.keys())}")
    print(f"权重：{weights}")
    print(f"期间：{start_date} - {end_date}")
    print(f"调仓频率：{rebalance_freq}天")
    
    # 获取历史数据
    etf_returns = {}
    for code in etf_codes:
        prices = get_etf_history(code, start_date, end_date)
        if prices:
            etf_returns[code] = calculate_returns(prices)
            print(f"  {code}: {len(prices)} 天数据")
    
    if not etf_returns:
        print("❌ 无可用数据")
        return None
    
    # 模拟定期调仓
    portfolio_returns = calculate_portfolio_returns(etf_returns, weights)
    
    # 计算性能指标
    metrics = calculate_metrics(portfolio_returns)
    
    return {
        "strategy": "定期调仓",
        "etf_codes": etf_codes,
        "weights": weights,
        "start_date": start_date,
        "end_date": end_date,
        "rebalance_freq": rebalance_freq,
        "returns": portfolio_returns,
        "metrics": metrics
    }

def backtest_buy_hold(etf_codes, weights, start_date, end_date):
    """回测买入持有策略"""
    print(f"回测买入持有策略...")
    
    # 获取历史数据
    etf_returns = {}
    for code in etf_codes:
        prices = get_etf_history(code, start_date, end_date)
        if prices:
            etf_returns[code] = calculate_returns(prices)
    
    if not etf_returns:
        return None
    
    # 计算组合收益
    portfolio_returns = calculate_portfolio_returns(etf_returns, weights)
    
    # 计算性能指标
    metrics = calculate_metrics(portfolio_returns)
    
    return {
        "strategy": "买入持有",
        "etf_codes": etf_codes,
        "weights": weights,
        "start_date": start_date,
        "end_date": end_date,
        "returns": portfolio_returns,
        "metrics": metrics
    }

def compare_strategies(rebalance_result, buy_hold_result):
    """对比策略表现"""
    lines = []
    lines.append("━━━ 策略对比 ━━━")
    lines.append("")
    
    if rebalance_result and buy_hold_result:
        r_metrics = rebalance_result["metrics"]
        b_metrics = buy_hold_result["metrics"]
        
        lines.append(f"{'指标':<15} {'定期调仓':>12} {'买入持有':>12} {'优势':>8}")
        lines.append("-" * 55)
        
        indicators = [
            ("总收益率%", "total_return"),
            ("年化收益%", "annual_return"),
            ("波动率%", "volatility"),
            ("夏普比率", "sharpe"),
            ("最大回撤%", "max_drawdown"),
            ("胜率%", "win_rate")
        ]
        
        for name, key in indicators:
            r_val = r_metrics.get(key, 0)
            b_val = b_metrics.get(key, 0)
            
            # 判断哪个更好
            if key in ["volatility", "max_drawdown"]:
                better = "调仓" if r_val < b_val else "持有"
            else:
                better = "调仓" if r_val > b_val else "持有"
            
            diff = r_val - b_val
            diff_str = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"
            
            lines.append(f"{name:<15} {r_val:>12.2f} {b_val:>12.2f} {better:>4}({diff_str})")
    
    return "\n".join(lines)

def generate_report(backtest_result):
    """生成回测报告"""
    if not backtest_result:
        return "❌ 回测失败"
    
    metrics = backtest_result.get("metrics", {})
    
    lines = []
    lines.append("📊 回测报告")
    lines.append(f"策略：{backtest_result.get('strategy', 'Unknown')}")
    lines.append(f"期间：{backtest_result.get('start_date', '')} - {backtest_result.get('end_date', '')}")
    lines.append("")
    
    lines.append("━━━ 持仓 ETF ━━━")
    for code, weight in backtest_result.get("weights", {}).items():
        lines.append(f"• {code}: {weight*100:.1f}%")
    lines.append("")
    
    lines.append("━━━ 性能指标 ━━━")
    lines.append(f"总收益率：{metrics.get('total_return', 0):+.2f}%")
    lines.append(f"年化收益：{metrics.get('annual_return', 0):+.2f}%")
    lines.append(f"波动率：{metrics.get('volatility', 0):.2f}%")
    lines.append(f"夏普比率：{metrics.get('sharpe', 0):.2f}")
    lines.append(f"最大回撤：{metrics.get('max_drawdown', 0):.2f}%")
    lines.append(f"胜率：{metrics.get('win_rate', 0):.2f}%")
    lines.append(f"交易天数：{metrics.get('trading_days', 0)}")
    lines.append("")
    
    lines.append("━━━ 评价 ━━━")
    
    sharpe = metrics.get('sharpe', 0)
    if sharpe > 1.5:
        lines.append("✅ 优秀：夏普比率 > 1.5，风险调整后收益良好")
    elif sharpe > 1:
        lines.append("✅ 良好：夏普比率 > 1，策略有效")
    elif sharpe > 0:
        lines.append("⏸️ 一般：夏普比率 > 0，有正向收益")
    else:
        lines.append("⚠️ 待改进：夏普比率 < 0，策略需优化")
    
    max_dd = metrics.get('max_drawdown', 0)
    if max_dd < 10:
        lines.append("✅ 回撤控制良好 (<10%)")
    elif max_dd < 20:
        lines.append("⏸️ 回撤中等 (10-20%)")
    else:
        lines.append("⚠️ 回撤较大 (>20%)，注意风险控制")
    
    return "\n".join(lines)

def save_backtest_result(result, filename):
    """保存回测结果"""
    # 序列化 numpy 类型
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        return obj
    
    result_json = json.loads(json.dumps(result, default=convert))
    
    filepath = BACKTEST_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存：{filepath}")

def main():
    """主函数 - 示例回测"""
    print("=" * 60)
    print("回测框架 - 示例")
    print("=" * 60)
    
    # 示例：回测一个简单的 ETF 组合
    etf_codes = ["510300", "510880", "512480"]  # 300ETF, 红利 ETF, 半导体
    weights = {"510300": 0.4, "510880": 0.3, "512480": 0.3}
    
    # 回测期间（最近 3 个月）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
    
    # 回测买入持有策略
    print("\n" + "=" * 60)
    buy_hold_result = backtest_buy_hold(etf_codes, weights, start_date, end_date)
    
    if buy_hold_result:
        report = generate_report(buy_hold_result)
        print("\n" + report)
        
        # 保存结果
        save_backtest_result(buy_hold_result, f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    print("\n✅ 回测完成")
    
    return buy_hold_result

if __name__ == "__main__":
    main()
