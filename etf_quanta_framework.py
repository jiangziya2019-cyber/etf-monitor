#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 融合分析框架 - 基础数据结构
版本：v0.1 | 创建：2026-03-27
"""

import json
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


# ==================== 枚举定义 ====================

class MarketRegime(Enum):
    """市场状态"""
    BULL = "bull"  # 牛市
    BEAR = "bear"  # 熊市
    SIDEWAYS = "sideways"  # 震荡
    UNKNOWN = "unknown"  # 未知


class RuleType(Enum):
    """规则类型"""
    MOMENTUM = "momentum"  # 动量
    VALUE = "value"  # 估值
    FLOW = "flow"  # 资金流
    VOLATILITY = "volatility"  # 波动率
    SECTOR = "sector"  # 行业景气
    ARBITRAGE = "arbitrage"  # 跨境套利


class ActionStatus(Enum):
    """行动状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Recommendation(Enum):
    """建议类型"""
    STRONG_BUY = "strong_buy"  # 强烈建议
    BUY = "buy"  # 建议
    HOLD = "hold"  # 观望
    REDUCE = "reduce"  # 减仓
    SELL = "sell"  # 卖出


# ==================== 数据结构 ====================

@dataclass
class ETFData:
    """ETF 基础数据"""
    code: str
    name: str
    price: float
    change_pct: float
    volume: float
    amount: float  # 成交额
    nav: float = 0.0  # 净值
    premium_rate: float = 0.0  # 溢价率
    
    # 估值指标
    pe: float = 0.0
    pb: float = 0.0
    pe_percentile: float = 0.0  # PE 历史分位
    pb_percentile: float = 0.0  # PB 历史分位
    
    # 动量指标
    return_1d: float = 0.0
    return_5d: float = 0.0
    return_20d: float = 0.0
    return_60d: float = 0.0
    
    # 波动率指标
    atr_14: float = 0.0
    volatility_20d: float = 0.0
    
    # 资金流
    net_inflow: float = 0.0  # 净流入
    turnover_rate: float = 0.0  # 换手率
    
    # 元数据
    update_time: str = ""
    source: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FilterRule:
    """筛选规则"""
    field: str  # 字段名，如 'pe_percentile'
    operator: str  # 操作符：'<', '>', '<=', '>=', '==', 'between'
    value: Any  # 阈值或范围
    weight: float = 1.0  # 权重
    
    def evaluate(self, etf: ETFData) -> bool:
        """评估规则是否满足"""
        etf_dict = etf.to_dict()
        if self.field not in etf_dict:
            return False
        
        actual_value = etf_dict[self.field]
        
        if self.operator == '<':
            return actual_value < self.value
        elif self.operator == '>':
            return actual_value > self.value
        elif self.operator == '<=':
            return actual_value <= self.value
        elif self.operator == '>=':
            return actual_value >= self.value
        elif self.operator == '==':
            return actual_value == self.value
        elif self.operator == 'between':
            return self.value[0] <= actual_value <= self.value[1]
        return False
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScreeningHypothesis:
    """筛选假设"""
    id: str
    name: str
    description: str  # 自然语言描述
    rule_type: RuleType
    market_regime: List[MarketRegime]  # 适用市场状态
    
    # 规则列表
    filters: List[FilterRule] = field(default_factory=list)
    
    # 排序规则
    sort_by: str = "return_20d"  # 按哪个字段排序
    ascending: bool = False  # True=升序，False=降序
    
    # 元数据
    created_at: str = ""
    parent_id: Optional[str] = None  # 父假设 ID（用于追踪进化）
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['rule_type'] = self.rule_type.value
        d['market_regime'] = [m.value for m in self.market_regime]
        return d


@dataclass
class ScreeningResult:
    """筛选结果"""
    hypothesis_id: str
    selected_etfs: List[str]  # ETF 代码列表
    total_candidates: int  # 候选总数
    selected_count: int  # 选中数量
    
    # 绩效指标
    avg_return_20d: float = 0.0
    avg_pe_percentile: float = 0.0
    avg_volatility: float = 0.0
    
    # 回测指标（如有）
    backtest_ic: float = 0.0
    backtest_arr: float = 0.0
    backtest_mdd: float = 0.0
    
    # 评估时间
    evaluated_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TrajectoryStep:
    """轨迹步骤"""
    step_id: int
    action_type: str  # 'hypothesis_gen', 'rule_build', 'backtest', 'evaluate'
    description: str
    status: ActionStatus
    result: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d


@dataclass
class MiningTrajectory:
    """挖掘轨迹 - 核心数据结构"""
    id: str
    hypothesis: ScreeningHypothesis
    
    # 步骤序列
    steps: List[TrajectoryStep] = field(default_factory=list)
    
    # 终端结果
    result: Optional[ScreeningResult] = None
    reward: float = 0.0  # 轨迹质量评分
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    iteration: int = 0  # 所属迭代轮次
    
    def add_step(self, action_type: str, description: str, 
                 status: ActionStatus, result: Optional[Dict] = None,
                 error: Optional[str] = None):
        """添加步骤"""
        step = TrajectoryStep(
            step_id=len(self.steps),
            action_type=action_type,
            description=description,
            status=status,
            result=result,
            error=error,
            timestamp=datetime.now().isoformat()
        )
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()
    
    def set_result(self, result: ScreeningResult):
        """设置结果"""
        self.result = result
        self.updated_at = datetime.now().isoformat()
    
    def calculate_reward(self):
        """计算轨迹奖励（简化版）"""
        if not self.result:
            return 0.0
        
        # 奖励 = IC * 0.5 + 年化收益 * 0.3 - 回撤 * 0.2
        reward = (
            self.result.backtest_ic * 0.5 +
            self.result.backtest_arr * 0.01 * 0.3 -
            abs(self.result.backtest_mdd) * 0.01 * 0.2
        )
        self.reward = reward
        return reward
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['hypothesis'] = self.hypothesis.to_dict()
        d['steps'] = [s.to_dict() for s in self.steps]
        d['result'] = self.result.to_dict() if self.result else None
        return d


@dataclass
class EvolutionFeedback:
    """进化反馈"""
    trajectory_id: str
    feedback_type: str  # 'mutation', 'crossover', 'selection'
    
    # 诊断信息
    diagnosis: str  # 问题分析
    suggested_action: str  # 建议行动
    
    # 具体修改
    modifications: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ==================== 规则池管理 ====================

class RulePool:
    """规则池 - 管理所有筛选规则"""
    
    def __init__(self):
        self.rules: Dict[str, ScreeningHypothesis] = {}
        self.performance_history: Dict[str, List[ScreeningResult]] = {}
        self.max_rules = 20  # 最大规则数量
        
    def add_rule(self, hypothesis: ScreeningHypothesis):
        """添加规则"""
        if len(self.rules) >= self.max_rules:
            # 移除表现最差的规则
            self._remove_worst_rule()
        
        self.rules[hypothesis.id] = hypothesis
        self.performance_history[hypothesis.id] = []
    
    def remove_rule(self, rule_id: str):
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
        if rule_id in self.performance_history:
            del self.performance_history[rule_id]
    
    def record_performance(self, rule_id: str, result: ScreeningResult):
        """记录绩效"""
        if rule_id in self.performance_history:
            self.performance_history[rule_id].append(result)
    
    def get_top_rules(self, n: int = 5, metric: str = 'avg_ic') -> List[Tuple[str, float]]:
        """获取 Top N 规则"""
        if not self.performance_history:
            return []
        
        rule_scores = []
        for rule_id, results in self.performance_history.items():
            if not results:
                continue
            
            if metric == 'avg_ic':
                score = sum(r.backtest_ic for r in results) / len(results)
            elif metric == 'avg_arr':
                score = sum(r.backtest_arr for r in results) / len(results)
            elif metric == 'avg_mdd':
                score = -sum(abs(r.backtest_mdd) for r in results) / len(results)
            else:
                score = 0.0
            
            rule_scores.append((rule_id, score))
        
        rule_scores.sort(key=lambda x: x[1], reverse=True)
        return rule_scores[:n]
    
    def _remove_worst_rule(self):
        """移除表现最差的规则"""
        top_rules = self.get_top_rules(n=self.max_rules - 1)
        worst_rule_ids = set(self.rules.keys()) - set(r[0] for r in top_rules)
        
        if worst_rule_ids:
            worst_id = list(worst_rule_ids)[0]
            self.remove_rule(worst_id)
    
    def to_dict(self) -> Dict:
        return {
            'rules': {k: v.to_dict() for k, v in self.rules.items()},
            'performance_count': {k: len(v) for k, v in self.performance_history.items()}
        }


# ==================== 辅助函数 ====================

def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    timestamp = datetime.now().isoformat()
    hash_id = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"{prefix}{hash_id}" if prefix else hash_id


def current_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().isoformat()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 测试数据结构
    print("=== ETF-QuantaAlpha 数据结构测试 ===\n")
    
    # 创建测试 ETF
    etf = ETFData(
        code="510300",
        name="沪深 300ETF",
        price=4.125,
        change_pct=0.85,
        volume=125000000,
        amount=515625000,
        pe=12.5,
        pb=1.35,
        pe_percentile=35.2,
        pb_percentile=28.7,
        return_20d=5.3,
        return_60d=8.2,
        volatility_20d=0.018,
        update_time=current_timestamp()
    )
    
    # 创建筛选规则
    rule1 = FilterRule(
        field="pe_percentile",
        operator="<",
        value=40.0,
        weight=1.0
    )
    
    rule2 = FilterRule(
        field="return_20d",
        operator=">",
        value=0.0,
        weight=1.0
    )
    
    # 创建假设
    hypothesis = ScreeningHypothesis(
        id=generate_id("hyp_"),
        name="低估值 + 正动量",
        description="选择 PE 分位低于 40% 且 20 日收益为正的 ETF",
        rule_type=RuleType.VALUE,
        market_regime=[MarketRegime.BULL, MarketRegime.SIDEWAYS],
        filters=[rule1, rule2],
        sort_by="return_20d",
        ascending=False,
        created_at=current_timestamp()
    )
    
    # 创建轨迹
    trajectory = MiningTrajectory(
        id=generate_id("traj_"),
        hypothesis=hypothesis,
        created_at=current_timestamp()
    )
    
    # 添加步骤
    trajectory.add_step(
        action_type="hypothesis_gen",
        description="生成筛选假设",
        status=ActionStatus.COMPLETED
    )
    
    trajectory.add_step(
        action_type="rule_build",
        description="构建筛选规则",
        status=ActionStatus.COMPLETED
    )
    
    # 创建结果
    result = ScreeningResult(
        hypothesis_id=hypothesis.id,
        selected_etfs=["510300", "510500", "159915"],
        total_candidates=1917,
        selected_count=15,
        avg_return_20d=4.2,
        avg_pe_percentile=32.5,
        backtest_ic=0.065,
        backtest_arr=12.5,
        backtest_mdd=-8.3,
        evaluated_at=current_timestamp()
    )
    
    trajectory.set_result(result)
    trajectory.calculate_reward()
    
    # 输出结果
    print(f"轨迹 ID: {trajectory.id}")
    print(f"假设：{hypothesis.name}")
    print(f"步骤数：{len(trajectory.steps)}")
    print(f"选中 ETF: {len(result.selected_etfs)} 只")
    print(f"奖励评分：{trajectory.reward:.4f}")
    print(f"\n轨迹字典:\n{json.dumps(trajectory.to_dict(), indent=2, ensure_ascii=False)[:500]}...")
    
    print("\n=== 测试完成 ===")
