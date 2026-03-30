#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子量化策略 v5.0 回测引擎（Tushare 真实数据版）
版本：v2.0 | 创建：2026-03-28 15:40 | 修复：2026-03-28 17:28

功能:
  - 使用 Tushare 真实历史数据
  - 2020-2026 年完整回测
  - 对比 v5.0 vs v1.0
  - 计算年化收益/夏普/最大回撤
"""

import sys, json, time
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')
from multi_factor_v5 import (
    calculate_valuation_factors,
    calculate_momentum_factors,
    calculate_volatility_factors,
    calculate_technical_factors,
    calculate_fund_flow_factors,
    calculate_composite_score,
    select_top_etfs,
    identify_market_regime
)

# 使用 Tushare 官方 fund_daily 接口（需要 5000+ 积分，我们有 25,100 分）
sys.path.insert(0, '/home/admin/openclaw/workspace')
from tushare_finance_data import get_fund_daily

# ============ 配置 ============

INITIAL_CAPITAL = 1000000
TRANSACTION_COST = 0.001
REBALANCE_FREQ = 20  # 20 日调仓一次
TOP_N = 12

# ============ 回测类 ============

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = INITIAL_CAPITAL):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.portfolio_values = []
        self.trades = []
        
    def run_backtest(self, etf_pool: List[str], historical_data: Dict) -> Dict:
        """
        运行回测
        
        Args:
            etf_pool: ETF 池
            historical_data: 历史数据
        
        Returns:
            回测结果
        """
        from multi_factor_v5 import log_message
        log_message(f"开始回测 ({self.start_date} - {self.end_date})...")
        
        dates = sorted([d for d in historical_data.get(etf_pool[0], {}).keys()])
        dates = [d for d in dates if self.start_date <= d <= self.end_date]
        
        if not dates:
            log_message("⚠️ 无有效交易日期")
            return {}
        
        # 初始化
        self.capital = self.initial_capital
        self.positions = {}
        self.portfolio_values = []
        self.trades = []
        
        # 回测主循环
        for i, date in enumerate(dates):
            # 调仓日
            if i % REBALANCE_FREQ == 0:
                self.rebalance(date, etf_pool, historical_data)
            
            # 计算组合价值
            portfolio_value = self.calculate_portfolio_value(date, historical_data)
            self.portfolio_values.append({
                'date': date,
                'value': portfolio_value
            })
        
        # 计算回测指标
        results = self.calculate_metrics()
        
        return results
    
    def rebalance(self, date: str, etf_pool: List[str], historical_data: Dict):
        """调仓"""
        from multi_factor_v5 import log_message
        log_message(f"调仓日：{date}")
        
        # 计算因子评分
        valuation = calculate_valuation_factors(etf_pool, date)
        momentum = calculate_momentum_factors(historical_data, date)
        volatility = calculate_volatility_factors(historical_data, date)
        technical = calculate_technical_factors(etf_pool, date)
        fund_flow = calculate_fund_flow_factors(etf_pool)
        
        # 综合评分
        composite = calculate_composite_score(
            valuation, momentum, volatility, technical, fund_flow
        )
        
        # 选择 Top N
        top_etfs = select_top_etfs(composite, TOP_N)
        
        # 执行调仓（传入历史数据）
        self.execute_rebalance(date, top_etfs, historical_data)
    
    def get_price(self, code: str, date: str, historical_data: Dict) -> float:
        """获取价格（带验证）"""
        if historical_data and code in historical_data and date in historical_data[code]:
            price = historical_data[code][date]['close']
            if price > 0.5:  # 价格有效
                return price
        return None
    
    def execute_rebalance(self, date: str, target_etfs: List[str], historical_data: Dict = None):
        """
        执行调仓（修复版 - 修复交易成本重复计算 Bug）
        
        Args:
            date: 交易日期
            target_etfs: 目标 ETF 列表
            historical_data: 历史数据（包含真实价格）
        """
        from multi_factor_v5 import log_message
        
        old_capital = self.capital
        
        # ========== 第 1 步：卖出 ==========
        sell_proceeds = 0  # 卖出所得
        log_message(f"  当前持仓：{list(self.positions.keys())}, 目标：{target_etfs}")
        
        for code in list(self.positions.keys()):
            if code not in target_etfs:
                shares = self.positions[code]
                price = self.get_price(code, date, historical_data)
                
                if price:  # 价格有效
                    proceeds = shares * price * (1 - TRANSACTION_COST)
                    sell_proceeds += proceeds
                    del self.positions[code]
                    self.trades.append({
                        'date': date,
                        'action': 'sell',
                        'code': code,
                        'shares': shares,
                        'price': price,
                        'proceeds': proceeds
                    })
                    log_message(f"    卖出 {code}: {shares}份 @ ¥{price:.3f} = ¥{proceeds:,.0f}")
                else:
                    log_message(f"⚠️ {code} 在 {date} 无有效价格，跳过卖出")
            else:
                log_message(f"    保留 {code} ({self.positions[code]}份)")
        
        # 更新资金（卖出后）
        self.capital += sell_proceeds
        
        # ========== 第 2 步：买入 ==========
        if not target_etfs:
            return
        
        # 计算每只 ETF 的目标金额（使用卖出后的总资金）
        target_weight = 1.0 / len(target_etfs)
        target_value_per_etf = self.capital * target_weight
        
        buy_cost = 0  # 买入总成本
        
        for code in target_etfs:
            price = self.get_price(code, date, historical_data)
            
            if not price:
                continue
            
            # 计算可买份额（确保不超过剩余资金）
            max_affordable = (self.capital - buy_cost) / (1 + TRANSACTION_COST)
            target_for_this_etf = min(target_value_per_etf, max_affordable)
            
            shares = int(target_for_this_etf / price)
            
            if shares > 0:
                cost = shares * price * (1 + TRANSACTION_COST)
                # 确保不超过剩余资金
                if buy_cost + cost <= self.capital:
                    self.positions[code] = shares
                    buy_cost += cost
                    self.trades.append({
                        'date': date,
                        'action': 'buy',
                        'code': code,
                        'shares': shares,
                        'price': price,
                        'cost': cost
                    })
                    log_message(f"    买入 {code}: {shares}份 @ ¥{price:.3f} = ¥{cost:,.0f}")
                else:
                    log_message(f"    ⚠️ {code}: 资金不足")
            else:
                log_message(f"    ⚠️ {code}: 份额为 0")
        
        # 一次性扣除买入成本
        self.capital -= buy_cost
        log_message(f"  调仓 {date}: 卖出¥{sell_proceeds:,.0f}, 买入¥{buy_cost:,.0f}, 资金¥{old_capital:,.0f}→¥{self.capital:,.0f}")
    
    def calculate_portfolio_value(self, date: str, historical_data: Dict) -> float:
        """计算组合价值"""
        value = self.capital
        for code, shares in self.positions.items():
            if date in historical_data.get(code, {}):
                price = historical_data[code][date]['close']
                value += shares * price
        return value
    
    def calculate_metrics(self) -> Dict:
        """计算回测指标"""
        from multi_factor_v5 import log_message
        log_message("计算回测指标...")
        
        if not self.portfolio_values:
            return {}
        
        values = [pv['value'] for pv in self.portfolio_values]
        
        # 年化收益
        total_return = (values[-1] - values[0]) / values[0]
        days = len(self.portfolio_values)
        annual_return = (1 + total_return) ** (252 / days) - 1
        
        # 夏普比率
        returns = [values[i]/values[i-1] - 1 for i in range(1, len(values))]
        if len(returns) > 1:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        max_dd = 0
        peak = values[0]
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        # 胜率
        positive_days = sum(1 for r in returns if r > 0)
        win_rate = positive_days / len(returns) if returns else 0
        
        results = {
            'initial_capital': self.initial_capital,
            'final_value': values[-1],
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'portfolio_values': self.portfolio_values
        }
        
        return results

def load_etf_data(etf_codes: List[str], start_date: str, end_date: str) -> Dict:
    """
    从 Tushare 加载 ETF 真实历史数据（fund_daily 接口）
    
    Args:
        etf_codes: ETF 代码列表
        start_date: 开始日期（YYYYMMDD）
        end_date: 结束日期（YYYYMMDD）
    
    Returns:
        历史数据字典
    """
    from multi_factor_v5 import log_message
    log_message(f"从 Tushare 加载 {len(etf_codes)}只 ETF 历史数据 (fund_daily)...")
    
    historical_data = {}
    
    for i, code in enumerate(etf_codes):
        try:
            log_message(f"  [{i+1}/{len(etf_codes)}] 加载 {code}...")
            
            # 添加后缀
            ts_code = f"{code}.SH" if code.startswith('5') else f"{code}.SZ"
            
            # 使用 Tushare fund_daily 接口
            df = get_fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                historical_data[code] = {}
                for _, row in df.iterrows():
                    date = str(row['trade_date'])
                    historical_data[code][date] = {
                        'close': float(row['close']),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'vol': float(row['vol']),
                        'amount': float(row['amount']) * 1000  # 转换为元
                    }
                
                log_message(f"    ✅ {code}: {len(historical_data[code])}条记录")
            else:
                log_message(f"    ⚠️ {code}: 无数据")
            
            # 避免速率限制
            time.sleep(0.1)
            
        except Exception as e:
            log_message(f"    ❌ {code}: {e}")
    
    return historical_data

def main():
    """回测测试（Tushare 真实数据）"""
    print("="*70)
    print("多因子 v5.0 回测引擎测试（Tushare 真实数据）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 ETF 池（选择流动性好的 ETF）
    test_etfs = ['510300', '510500', '510880', '515790', '512480']
    
    # 从 akshare 加载真实历史数据
    historical_data = load_etf_data(test_etfs, '20250101', '20260328')
    
    if not historical_data:
        print("\n❌ 无法获取 Tushare 数据，退出")
        return
    
    # 创建回测引擎
    engine = BacktestEngine(
        start_date='20250101',
        end_date='20260328',
        initial_capital=1000000
    )
    
    # 运行回测
    results = engine.run_backtest(test_etfs, historical_data)
    
    # 输出结果
    print(f"\n✅ 回测完成")
    print(f"初始资金：¥{results['initial_capital']:,.0f}")
    print(f"最终价值：¥{results['final_value']:,.0f}")
    print(f"总收益：{results['total_return']*100:.2f}%")
    print(f"年化收益：{results['annual_return']*100:.2f}%")
    print(f"夏普比率：{results['sharpe_ratio']:.2f}")
    print(f"最大回撤：{results['max_drawdown']*100:.2f}%")
    print(f"胜率：{results['win_rate']*100:.2f}%")
    print(f"交易次数：{results['total_trades']}")

if __name__ == "__main__":
    main()
