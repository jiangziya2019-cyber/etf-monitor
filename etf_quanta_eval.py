#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 融合分析框架 - 评估反馈系统
版本：v0.1 | 创建：2026-03-27
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from etf_quanta_framework import (
    MiningTrajectory, ScreeningResult, ScreeningHypothesis,
    FilterRule, EvolutionFeedback, RulePool,
    ActionStatus, RuleType, MarketRegime,
    generate_id, current_timestamp
)


class TrajectoryEvaluator:
    """轨迹评估器"""
    
    def __init__(self):
        self.evaluation_count = 0
    
    def evaluate(self, trajectory: MiningTrajectory, etf_pool: List[Dict]) -> ScreeningResult:
        """评估轨迹表现"""
        hypothesis = trajectory.hypothesis
        selected_etfs = self._apply_filters(etf_pool, hypothesis.filters)
        selected_etfs.sort(key=lambda x: x.get(hypothesis.sort_by, 0), reverse=not hypothesis.ascending)
        
        result = ScreeningResult(
            hypothesis_id=hypothesis.id,
            selected_etfs=[e['code'] for e in selected_etfs[:20]],  # 返回代码列表
            total_candidates=1917,
            selected_count=len(selected_etfs),
            evaluated_at=current_timestamp()
        )
        
        # 模拟回测指标
        result.backtest_ic = random.uniform(0.03, 0.08)
        result.backtest_arr = random.uniform(8.0, 18.0)
        result.backtest_mdd = -random.uniform(5.0, 15.0)
        
        self.evaluation_count += 1
        return result
    
    def _apply_filters(self, etf_pool: List[Dict], filters: List[FilterRule]) -> List[Dict]:
        """应用过滤规则"""
        selected = []
        for etf_dict in etf_pool:
            passed = True
            for rule in filters:
                if rule.field not in etf_dict:
                    continue
                value = etf_dict[rule.field]
                if rule.operator == '<' and not (value < rule.value):
                    passed = False
                elif rule.operator == '>' and not (value > rule.value):
                    passed = False
                if not passed:
                    break
            if passed:
                selected.append(etf_dict)
        return selected


class FeedbackGenerator:
    """反馈生成器"""
    
    def generate_mutation_feedback(self, trajectory: MiningTrajectory) -> EvolutionFeedback:
        """生成变异反馈"""
        result = trajectory.result
        if not result:
            return EvolutionFeedback(
                trajectory_id=trajectory.id, feedback_type="mutation",
                diagnosis="无评估结果", suggested_action="重新评估",
                created_at=current_timestamp()
            )
        
        diagnosis = []
        modifications = {}
        
        if result.backtest_ic < 0.05:
            diagnosis.append(f"IC 过低 ({result.backtest_ic:.3f})")
            modifications["relax_filter"] = "放宽阈值"
        
        if abs(result.backtest_mdd) > 12.0:
            diagnosis.append(f"回撤过大 ({result.backtest_mdd:.1f}%)")
            modifications["add_volatility_filter"] = "增加波动率过滤"
        
        return EvolutionFeedback(
            trajectory_id=trajectory.id,
            feedback_type="mutation",
            diagnosis="; ".join(diagnosis) if diagnosis else "表现良好",
            suggested_action="针对性修正" if diagnosis else "保持当前规则",
            modifications=modifications,
            created_at=current_timestamp()
        )
    
    def generate_crossover_feedback(self, parent1: MiningTrajectory, parent2: MiningTrajectory) -> EvolutionFeedback:
        """生成交叉反馈"""
        return EvolutionFeedback(
            trajectory_id=f"{parent1.id}_{parent2.id}",
            feedback_type="crossover",
            diagnosis=f"融合 {parent1.hypothesis.name} + {parent2.hypothesis.name}",
            suggested_action="组合优势规则",
            modifications={"combine": True},
            created_at=current_timestamp()
        )


class EvolutionEngine:
    """进化引擎"""
    
    def __init__(self):
        self.rule_pool = RulePool()
        self.evaluator = TrajectoryEvaluator()
        self.feedback_gen = FeedbackGenerator()
        self.iteration = 0
        self.trajectories: List[MiningTrajectory] = []
    
    def run_iteration(self, etf_pool: List[Dict]) -> Dict:
        """运行一次进化迭代"""
        self.iteration += 1
        print(f"\n{'='*60}\n进化迭代 #{self.iteration}\n{'='*60}")
        
        if self.iteration == 1:
            trajectories = self._initialize_trajectories()
        else:
            trajectories = self._evolve_trajectories()
        
        print(f"\n[评估] 评估 {len(trajectories)} 条轨迹...")
        for traj in trajectories:
            result = self.evaluator.evaluate(traj, etf_pool)
            traj.set_result(result)
            traj.calculate_reward()
        
        trajectories.sort(key=lambda t: t.reward, reverse=True)
        top_trajectories = trajectories[:10]
        
        for traj in top_trajectories:
            if traj.hypothesis.id not in self.rule_pool.rules:
                self.rule_pool.add_rule(traj.hypothesis)
                self.rule_pool.record_performance(traj.hypothesis.id, traj.result)
        
        self._print_results(top_trajectories)
        self.trajectories = top_trajectories
        
        return {
            'iteration': self.iteration,
            'count': len(trajectories),
            'top_reward': top_trajectories[0].reward if top_trajectories else 0
        }
    
    def _initialize_trajectories(self) -> List[MiningTrajectory]:
        """初始化轨迹"""
        from etf_quanta_init import HypothesisGenerator
        generator = HypothesisGenerator()
        hypotheses = generator.generate_all_directions(MarketRegime.SIDEWAYS, seed_count=2)
        
        trajectories = []
        for h in hypotheses:
            traj = MiningTrajectory(id=generate_id("traj_"), hypothesis=h, created_at=current_timestamp(), iteration=self.iteration)
            traj.add_step("hypothesis_gen", "生成假设", ActionStatus.COMPLETED)
            trajectories.append(traj)
        return trajectories
    
    def _evolve_trajectories(self) -> List[MiningTrajectory]:
        """进化轨迹"""
        new_trajectories = []
        
        # 变异低绩效
        low_performers = [t for t in self.trajectories if t.reward < 0.03]
        for traj in low_performers[:3]:
            feedback = self.feedback_gen.generate_mutation_feedback(traj)
            mutated = self._apply_mutation(traj, feedback)
            if mutated:
                new_trajectories.append(mutated)
        
        # 交叉高绩效
        high_performers = [t for t in self.trajectories if t.reward >= 0.03]
        for i in range(0, min(len(high_performers)-1, 4), 2):
            crossed = self._apply_crossover(high_performers[i], high_performers[i+1])
            if crossed:
                new_trajectories.append(crossed)
        
        new_trajectories.extend(high_performers[:5])
        return new_trajectories
    
    def _apply_mutation(self, trajectory: MiningTrajectory, feedback: EvolutionFeedback) -> Optional[MiningTrajectory]:
        """应用变异"""
        new_filters = []
        for f in trajectory.hypothesis.filters:
            try:
                new_value = f.value * 1.2 if f.operator == '<' else f.value * 0.8
            except TypeError:
                new_value = f.value
            new_filters.append(FilterRule(f.field, f.operator, new_value))
        
        new_hypothesis = ScreeningHypothesis(
            id=generate_id("hyp_mut_"),
            name=f"{trajectory.hypothesis.name}_v2",
            description=trajectory.hypothesis.description,
            rule_type=trajectory.hypothesis.rule_type,
            market_regime=trajectory.hypothesis.market_regime,
            filters=new_filters,
            sort_by=trajectory.hypothesis.sort_by,
            ascending=trajectory.hypothesis.ascending,
            created_at=current_timestamp(),
            parent_id=trajectory.hypothesis.id
        )
        
        new_traj = MiningTrajectory(id=generate_id("traj_mut_"), hypothesis=new_hypothesis, created_at=current_timestamp(), iteration=self.iteration)
        new_traj.add_step("mutation", feedback.diagnosis, ActionStatus.COMPLETED)
        return new_traj
    
    def _apply_crossover(self, traj1: MiningTrajectory, traj2: MiningTrajectory) -> Optional[MiningTrajectory]:
        """应用交叉"""
        combined_filters = traj1.hypothesis.filters + traj2.hypothesis.filters[:1]
        new_hypothesis = ScreeningHypothesis(
            id=generate_id("hyp_cross_"),
            name=f"{traj1.hypothesis.name}+{traj2.hypothesis.name}",
            description=f"融合规则",
            rule_type=traj1.hypothesis.rule_type,
            market_regime=traj1.hypothesis.market_regime,
            filters=combined_filters,
            sort_by=traj1.hypothesis.sort_by,
            ascending=traj1.hypothesis.ascending,
            created_at=current_timestamp()
        )
        
        new_traj = MiningTrajectory(id=generate_id("traj_cross_"), hypothesis=new_hypothesis, created_at=current_timestamp(), iteration=self.iteration)
        new_traj.add_step("crossover", f"{traj1.hypothesis.name} x {traj2.hypothesis.name}", ActionStatus.COMPLETED)
        return new_traj
    
    def _print_results(self, trajectories: List[MiningTrajectory]):
        """打印结果"""
        print(f"\n[Top 5 轨迹]")
        for i, traj in enumerate(trajectories[:5], 1):
            r = traj.result
            print(f"  {i}. {traj.hypothesis.name}: 奖励={traj.reward:.4f}, IC={r.backtest_ic:.3f}, ARR={r.backtest_arr:.1f}%, MDD={r.backtest_mdd:.1f}%")


if __name__ == "__main__":
    print("="*60 + "\nETF-QuantaAlpha 评估反馈系统测试\n" + "="*60)
    
    # 模拟 ETF 池
    etf_pool = [
        {'code': '510300', 'pe_percentile': 35.0, 'return_20d': 5.2, 'volatility_20d': 0.018},
        {'code': '510500', 'pe_percentile': 25.0, 'return_20d': 3.8, 'volatility_20d': 0.015},
        {'code': '159915', 'pe_percentile': 45.0, 'return_20d': 8.1, 'volatility_20d': 0.025},
    ] * 10
    
    engine = EvolutionEngine()
    
    # 运行 3 轮迭代
    for i in range(3):
        result = engine.run_iteration(etf_pool)
        print(f"\n迭代 {i+1} 完成：评估{result['count']}条轨迹，最佳奖励={result['top_reward']:.4f}")
    
    print("\n" + "="*60 + "\n测试完成\n" + "="*60)
