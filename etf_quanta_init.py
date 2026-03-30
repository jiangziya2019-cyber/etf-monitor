#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 融合分析框架 - 多样化初始化模块
版本：v0.1 | 创建：2026-03-27
"""

import sys
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

# 导入基础数据结构
from etf_quanta_framework import (
    ScreeningHypothesis, FilterRule, RuleType, MarketRegime,
    generate_id, current_timestamp
)


# ==================== 初始化方向定义 ====================

class InitDirection(Enum):
    """初始化方向"""
    MOMENTUM = "momentum"  # 动量轮动
    VALUE = "value"  # 均值回归
    FLOW = "flow"  # 资金流向
    VOLATILITY = "volatility"  # 波动率目标
    SECTOR = "sector"  # 行业景气
    ARBITRAGE = "arbitrage"  # 跨境套利


# ==================== 假设生成器 ====================

class HypothesisGenerator:
    """假设生成器 - 多样化初始化核心"""
    
    def __init__(self):
        self.generated_count = 0
        
    def generate_all_directions(self, 
                                 market_regime: MarketRegime = MarketRegime.UNKNOWN,
                                 seed_count: int = 2) -> List[ScreeningHypothesis]:
        """
        生成所有方向的初始假设
        
        Args:
            market_regime: 当前市场状态
            seed_count: 每个方向的种子假设数量
            
        Returns:
            假设列表
        """
        hypotheses = []
        
        # 1. 动量轮动方向
        hypotheses.extend(self._generate_momentum_hypotheses(market_regime, seed_count))
        
        # 2. 估值回归方向
        hypotheses.extend(self._generate_value_hypotheses(market_regime, seed_count))
        
        # 3. 资金流向方向
        hypotheses.extend(self._generate_flow_hypotheses(market_regime, seed_count))
        
        # 4. 波动率方向
        hypotheses.extend(self._generate_volatility_hypotheses(market_regime, seed_count))
        
        # 5. 行业景气方向
        hypotheses.extend(self._generate_sector_hypotheses(market_regime, seed_count))
        
        # 6. 跨境套利方向
        hypotheses.extend(self._generate_arbitrage_hypotheses(market_regime, seed_count))
        
        self.generated_count = len(hypotheses)
        print(f"[初始化] 生成 {len(hypotheses)} 个初始假设，覆盖 6 大方向")
        
        return hypotheses
    
    def _generate_momentum_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成动量轮动假设"""
        hypotheses = []
        
        # 假设 1: 短期动量
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_mom_"),
            name="短期动量效应",
            description="20 日收益率最高的 ETF 继续跑赢",
            rule_type=RuleType.MOMENTUM,
            market_regime=[MarketRegime.BULL, MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("return_20d", ">", 0.0),
                FilterRule("return_5d", ">", 0.0),
            ],
            sort_by="return_20d",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        # 假设 2: 中期动量
        h2 = ScreeningHypothesis(
            id=generate_id("hyp_mom_"),
            name="中期趋势延续",
            description="60 日收益率显示中期趋势，配合 20 日动量",
            rule_type=RuleType.MOMENTUM,
            market_regime=[MarketRegime.BULL],
            filters=[
                FilterRule("return_60d", ">", 5.0),
                FilterRule("return_20d", ">", 2.0),
                FilterRule("volatility_20d", "<", 0.03),  # 低波动趋势更可靠
            ],
            sort_by="return_60d",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h2)
        
        return hypotheses[:count]
    
    def _generate_value_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成估值回归假设"""
        hypotheses = []
        
        # 假设 1: 低估值
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_val_"),
            name="低估值修复",
            description="PE 分位低于 30% 的 ETF 有估值修复空间",
            rule_type=RuleType.VALUE,
            market_regime=[MarketRegime.BEAR, MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("pe_percentile", "<", 30.0),
                FilterRule("pb_percentile", "<", 30.0),
            ],
            sort_by="pe_percentile",
            ascending=True,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        # 假设 2: 估值 + 动量
        h2 = ScreeningHypothesis(
            id=generate_id("hyp_val_"),
            name="低估值 + 正动量",
            description="低估值且动量转正的 ETF，可能是反转信号",
            rule_type=RuleType.VALUE,
            market_regime=[MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("pe_percentile", "<", 40.0),
                FilterRule("return_20d", ">", 0.0),
                FilterRule("return_5d", ">", "return_1d"),  # 加速
            ],
            sort_by="return_20d",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h2)
        
        return hypotheses[:count]
    
    def _generate_flow_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成资金流向假设"""
        hypotheses = []
        
        # 假设 1: 资金净流入
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_flow_"),
            name="主力进场",
            description="资金持续净流入的 ETF 有上涨动力",
            rule_type=RuleType.FLOW,
            market_regime=[MarketRegime.BULL, MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("net_inflow", ">", 0),
                FilterRule("turnover_rate", ">", 0.02),  # 活跃交易
            ],
            sort_by="net_inflow",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        # 假设 2: 量价配合
        h2 = ScreeningHypothesis(
            id=generate_id("hyp_flow_"),
            name="量价齐升",
            description="价格上涨配合成交量放大",
            rule_type=RuleType.FLOW,
            market_regime=[MarketRegime.BULL],
            filters=[
                FilterRule("change_pct", ">", 0),
                FilterRule("volume", ">", 100000000),  # 成交额>1 亿
                FilterRule("turnover_rate", ">", 0.03),
            ],
            sort_by="change_pct",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h2)
        
        return hypotheses[:count]
    
    def _generate_volatility_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成波动率假设"""
        hypotheses = []
        
        # 假设 1: 低波动稳健
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_vol_"),
            name="低波动稳健",
            description="低波动率 ETF 在震荡市表现更稳",
            rule_type=RuleType.VOLATILITY,
            market_regime=[MarketRegime.SIDEWAYS, MarketRegime.BEAR],
            filters=[
                FilterRule("volatility_20d", "<", 0.015),
                FilterRule("return_20d", ">", -5.0),  # 不大幅下跌
            ],
            sort_by="volatility_20d",
            ascending=True,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        # 假设 2: 波动率收缩
        h2 = ScreeningHypothesis(
            id=generate_id("hyp_vol_"),
            name="波动率收缩突破",
            description="波动率收缩后可能有突破行情",
            rule_type=RuleType.VOLATILITY,
            market_regime=[MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("volatility_20d", "<", 0.01),  # 极低波动
                FilterRule("atr_14", "<", 0.02),
            ],
            sort_by="change_pct",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h2)
        
        return hypotheses[:count]
    
    def _generate_sector_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成行业景气假设"""
        hypotheses = []
        
        # 假设 1: 行业轮动
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_sec_"),
            name="行业景气轮动",
            description="景气度上升行业的 ETF 表现更好",
            rule_type=RuleType.SECTOR,
            market_regime=[MarketRegime.BULL, MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("return_20d", ">", 0),
                FilterRule("return_5d", ">", "return_20d"),  # 加速
            ],
            sort_by="return_5d",
            ascending=False,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        return hypotheses[:count]
    
    def _generate_arbitrage_hypotheses(self, regime: MarketRegime, count: int) -> List[ScreeningHypothesis]:
        """生成跨境套利假设"""
        hypotheses = []
        
        # 假设 1: 折价套利
        h1 = ScreeningHypothesis(
            id=generate_id("hyp_arb_"),
            name="折价套利机会",
            description="折价率高的 QDII ETF 有套利空间",
            rule_type=RuleType.ARBITRAGE,
            market_regime=[MarketRegime.SIDEWAYS],
            filters=[
                FilterRule("premium_rate", "<", -2.0),  # 折价>2%
            ],
            sort_by="premium_rate",
            ascending=True,
            created_at=current_timestamp()
        )
        hypotheses.append(h1)
        
        return hypotheses[:count]


# ==================== 规则编译器 ====================

class RuleCompiler:
    """规则编译器 - 将假设转换为可执行规则"""
    
    def __init__(self):
        self.compiled_count = 0
        
    def compile(self, hypothesis: ScreeningHypothesis) -> Dict:
        """
        编译假设为可执行规则
        
        Returns:
            编译后的规则字典
        """
        # 1. 语义一致性检查
        consistency_check = self._check_semantic_consistency(hypothesis)
        if not consistency_check['passed']:
            return {
                'success': False,
                'error': f"语义一致性检查失败：{consistency_check['reason']}"
            }
        
        # 2. 复杂度检查
        complexity_check = self._check_complexity(hypothesis)
        if not complexity_check['passed']:
            return {
                'success': False,
                'error': f"复杂度过高：{complexity_check['reason']}"
            }
        
        # 3. 生成可执行代码
        executable = self._generate_executable(hypothesis)
        
        self.compiled_count += 1
        
        return {
            'success': True,
            'hypothesis_id': hypothesis.id,
            'executable': executable,
            'filter_count': len(hypothesis.filters),
            'complexity_score': complexity_check['score']
        }
    
    def _check_semantic_consistency(self, hypothesis: ScreeningHypothesis) -> Dict:
        """检查语义一致性"""
        # 检查假设描述与规则是否匹配
        if not hypothesis.filters:
            return {'passed': False, 'reason': '没有筛选规则'}
        
        # 检查排序字段是否合理
        valid_sort_fields = [
            'return_1d', 'return_5d', 'return_20d', 'return_60d',
            'pe_percentile', 'pb_percentile', 'volatility_20d',
            'net_inflow', 'change_pct', 'premium_rate'
        ]
        if hypothesis.sort_by not in valid_sort_fields:
            return {'passed': False, 'reason': f'无效排序字段：{hypothesis.sort_by}'}
        
        return {'passed': True}
    
    def _check_complexity(self, hypothesis: ScreeningHypothesis) -> Dict:
        """检查复杂度"""
        # 规则数量
        rule_count = len(hypothesis.filters)
        max_rules = 5
        
        # 计算复杂度分数
        score = rule_count * 10  # 每条规则 10 分
        
        return {
            'passed': rule_count <= max_rules,
            'score': score,
            'reason': f'规则数量 {rule_count} 超过上限 {max_rules}' if rule_count > max_rules else ''
        }
    
    def _generate_executable(self, hypothesis: ScreeningHypothesis) -> str:
        """生成可执行代码字符串"""
        code_lines = [
            f"# {hypothesis.name}",
            f"# {hypothesis.description}",
            "",
            "def screen_etf(etf_data):",
            "    selected = []",
            "    for etf in etf_data:",
        ]
        
        # 添加过滤条件
        for i, rule in enumerate(hypothesis.filters):
            if rule.operator == '<':
                code_lines.append(f"        if not (etf.{rule.field} < {rule.value}): continue")
            elif rule.operator == '>':
                code_lines.append(f"        if not (etf.{rule.field} > {rule.value}): continue")
            elif rule.operator == '<=':
                code_lines.append(f"        if not (etf.{rule.field} <= {rule.value}): continue")
            elif rule.operator == '>=':
                code_lines.append(f"        if not (etf.{rule.field} >= {rule.value}): continue")
            elif rule.operator == 'between':
                code_lines.append(f"        if not ({rule.value[0]} <= etf.{rule.field} <= {rule.value[1]}): continue")
        
        code_lines.append("        selected.append(etf)")
        code_lines.append(f"    selected.sort(key=lambda x: x.{hypothesis.sort_by}, reverse={not hypothesis.ascending})")
        code_lines.append("    return selected")
        
        return "\n".join(code_lines)


# ==================== 主函数 ====================

def run_initialization(market_regime: str = "unknown") -> List[ScreeningHypothesis]:
    """
    运行初始化流程
    
    Returns:
        生成的假设列表
    """
    print("=" * 60)
    print("ETF-QuantaAlpha 多样化初始化")
    print("=" * 60)
    
    # 解析市场状态
    regime_map = {
        'bull': MarketRegime.BULL,
        'bear': MarketRegime.BEAR,
        'sideways': MarketRegime.SIDEWAYS,
        'unknown': MarketRegime.UNKNOWN
    }
    regime = regime_map.get(market_regime.lower(), MarketRegime.UNKNOWN)
    
    # 生成假设
    generator = HypothesisGenerator()
    hypotheses = generator.generate_all_directions(regime, seed_count=2)
    
    # 编译规则
    compiler = RuleCompiler()
    compiled_rules = []
    
    print("\n[编译] 开始编译规则...")
    for h in hypotheses:
        result = compiler.compile(h)
        if result['success']:
            compiled_rules.append(result)
            print(f"  ✅ {h.name} (复杂度：{result['complexity_score']})")
        else:
            print(f"  ❌ {h.name}: {result['error']}")
    
    print(f"\n[完成] 编译 {len(compiled_rules)}/{len(hypotheses)} 条规则")
    print("=" * 60)
    
    return hypotheses


if __name__ == "__main__":
    # 测试初始化模块
    hypotheses = run_initialization("sideways")
    
    print("\n=== 生成的假设列表 ===\n")
    for h in hypotheses:
        print(f"ID: {h.id}")
        print(f"名称：{h.name}")
        print(f"类型：{h.rule_type.value}")
        print(f"规则数：{len(h.filters)}")
        print(f"排序：{h.sort_by} ({'升序' if h.ascending else '降序'})")
        print("-" * 40)
