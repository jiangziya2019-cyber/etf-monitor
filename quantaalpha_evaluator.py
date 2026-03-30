#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 智能评估模块
为触发器提供行业前景、仓位分析、置信度评估

对接第三阶段：止损/止盈增强
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

# ============ 配置区域 ============

# 仓位阈值
HEAVY_POSITION_THRESHOLD = 8.0  # >8% 为重仓
LIGHT_POSITION_THRESHOLD = 5.0  # <5% 为轻仓

# 行业前景评分映射
OUTLOOK_SCORE_MAP = {
    5: "非常好",
    4: "良好",
    3: "中性",
    2: "谨慎",
    1: "悲观"
}

# 置信度阈值
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.50

# ============ 核心评估器 ============

class QuantaAlphaEvaluator:
    """QuantaAlpha 智能评估器"""
    
    def __init__(self):
        self.sector_factors = {}  # 行业因子缓存
        self.market_state = self._detect_market_state()
    
    def _detect_market_state(self) -> str:
        """检测当前市场状态"""
        # TODO: 对接真实数据，目前简化处理
        # 可根据 300ETF、500ETF 的 20/60 日均线判断
        return "震荡"
    
    def evaluate_sector(self, code: str, sector: str) -> Dict:
        """
        评估行业前景
        
        Args:
            code: ETF 代码
            sector: 行业名称
        
        Returns:
            {
                "score": 4,  # 1-5 分
                "trend": "up",  # up/down/sideways
                "confidence": 0.75,  # 0-1
                "factors": ["因子 1", "因子 2"]
            }
        """
        # TODO: 对接 QuantaAlpha 行业因子模型
        # 目前使用预设评估
        
        outlook_data = {
            "黄金": {"score": 4, "trend": "sideways", "factors": ["美联储降息预期", "地缘避险"]},
            "半导体": {"score": 4, "trend": "up", "factors": ["AI 算力需求", "国产替代"]},
            "美股宽基": {"score": 3, "trend": "up", "factors": ["估值偏高", "长期向好"]},
            "A 股宽基": {"score": 5, "trend": "sideways", "factors": ["估值低位", "经济复苏"]},
            "AI 科技": {"score": 4, "trend": "up", "factors": ["AI 趋势", "估值偏高"]},
            "原油": {"score": 3, "trend": "sideways", "factors": ["地缘支撑", "波动大"]},
            "高端制造": {"score": 4, "trend": "up", "factors": ["政策支持", "趋势良好"]},
            "新能源": {"score": 4, "trend": "up", "factors": ["储能需求", "碳中和"]},
            "航天卫星": {"score": 4, "trend": "up", "factors": ["组网加速", "估值偏高"]},
        }
        
        default = {"score": 3, "trend": "sideways", "factors": ["数据不足"]}
        result = outlook_data.get(sector, default)
        
        # 计算置信度
        confidence = 0.60  # 基础置信度
        if len(result["factors"]) >= 2:
            confidence += 0.15
        if self.market_state == "震荡" and result["trend"] == "sideways":
            confidence += 0.10
        
        return {
            "score": result["score"],
            "trend": result["trend"],
            "confidence": min(confidence, 0.95),
            "factors": result["factors"],
            "market_state": self.market_state
        }
    
    def analyze_position(self, weight: float, profit_pct: float) -> Dict:
        """
        分析仓位风险
        
        Args:
            weight: 持仓权重 (%)
            profit_pct: 盈亏比例 (%)
        
        Returns:
            {
                "level": "heavy",  # heavy/normal/light
                "risk": "medium",  # high/medium/low
                "suggestion": "谨慎加仓"
            }
        """
        if weight >= HEAVY_POSITION_THRESHOLD:
            level = "heavy"
            if profit_pct > 10:
                risk = "low"
                suggestion = "盈利丰厚，可继续持有"
            elif profit_pct > 0:
                risk = "medium"
                suggestion = "盈利中，注意止盈"
            else:
                risk = "high"
                suggestion = "重仓亏损，建议减仓"
        elif weight >= LIGHT_POSITION_THRESHOLD:
            level = "normal"
            risk = "medium"
            suggestion = "仓位适中，根据信号操作"
        else:
            level = "light"
            risk = "low"
            suggestion = "轻仓可适度加仓"
        
        return {
            "level": level,
            "risk": risk,
            "suggestion": suggestion,
            "weight": weight,
            "profit_pct": profit_pct
        }
    
    def generate_recommendation(self, 
                                trigger_type: str,
                                industry_score: int,
                                position_risk: str,
                                profit_pct: float,
                                confidence: float) -> Dict:
        """
        生成综合建议
        
        Args:
            trigger_type: stop_loss / take_profit / grid
            industry_score: 行业前景评分 (1-5)
            position_risk: high/medium/low
            profit_pct: 盈亏比例
            confidence: 置信度 (0-1)
        
        Returns:
            {
                "action": "hold",  # sell/sell_partial/hold/buy
                "recommendation": "⚠️ 暂缓执行",
                "confidence_level": "中",
                "reasons": ["原因 1", "原因 2"]
            }
        """
        reasons = []
        action = "hold"
        recommendation = ""
        
        if trigger_type == "stop_loss":
            # 止损场景
            if industry_score >= 4:
                action = "hold"
                recommendation = "⚠️ 暂缓执行"
                reasons.append(f"✅ 行业前景良好（评分{industry_score}/5）")
                reasons.append(f"✅ 可能是暂时波动，建议观察 3-5 个交易日")
            elif industry_score == 3:
                if position_risk == "high":
                    action = "sell_partial"
                    recommendation = "🟡 部分执行"
                    reasons.append(f"🟡 行业前景中性 + 仓位风险高")
                    reasons.append(f"💡 建议减仓 50% 控制风险")
                else:
                    action = "sell"
                    recommendation = "✅ 建议执行"
                    reasons.append(f"🟡 行业前景中性")
                    reasons.append(f"✅ 及时止损保住本金")
            else:
                action = "sell"
                recommendation = "✅ 建议执行"
                reasons.append(f"❌ 行业前景不明（评分{industry_score}/5）")
                reasons.append(f"✅ 亏损已达阈值，执行纪律")
        
        elif trigger_type == "take_profit":
            # 止盈场景
            if industry_score >= 4 and profit_pct < 50:
                action = "hold"
                recommendation = "✅ 继续持有"
                reasons.append(f"✅ 行业前景良好，趋势未变")
                reasons.append(f"✅ 盈利{profit_pct:.1f}% 还有空间")
            elif industry_score >= 4:
                action = "sell_partial"
                recommendation = "🟡 部分止盈"
                reasons.append(f"✅ 行业前景好，但盈利已丰厚")
                reasons.append(f"💡 建议止盈 30-50%，保留底仓")
            elif industry_score == 3:
                action = "sell_partial"
                recommendation = "🟡 部分止盈"
                reasons.append(f"🟡 行业前景中性")
                reasons.append(f"💡 锁定部分利润，落袋为安")
            else:
                action = "sell"
                recommendation = "✅ 建议止盈"
                reasons.append(f"❌ 行业前景不明")
                reasons.append(f"✅ 及时止盈，避免回撤")
        
        elif trigger_type == "grid":
            # 网格加仓场景
            if industry_score >= 4:
                if position_risk == "low":
                    action = "buy"
                    recommendation = "✅ 建议加仓"
                    reasons.append(f"✅ 行业前景好 + 轻仓")
                    reasons.append(f"✅ 网格触发，可执行")
                elif position_risk == "medium":
                    action = "buy"
                    recommendation = "✅ 建议加仓"
                    reasons.append(f"✅ 行业前景好")
                    reasons.append(f"🟡 仓位适中，按计划加仓")
                else:
                    action = "hold"
                    recommendation = "⚠️ 暂缓加仓"
                    reasons.append(f"✅ 行业前景好")
                    reasons.append(f"❌ 但仓位已重，谨慎加仓")
            elif industry_score == 3:
                action = "buy"
                recommendation = "🟡 谨慎加仓"
                reasons.append(f"🟡 行业前景中性")
                reasons.append(f"💡 小仓位执行网格")
            else:
                action = "hold"
                recommendation = "⚠️ 暂缓加仓"
                reasons.append(f"❌ 行业前景不明")
                reasons.append(f"💡 等待更好时机")
        
        # 置信度等级
        if confidence >= CONFIDENCE_HIGH:
            confidence_level = "高"
        elif confidence >= CONFIDENCE_MEDIUM:
            confidence_level = "中"
        else:
            confidence_level = "低"
        
        return {
            "action": action,
            "recommendation": recommendation,
            "confidence_level": confidence_level,
            "confidence_score": confidence,
            "reasons": reasons,
            "timestamp": datetime.now().isoformat()
        }
    
    def full_analysis(self,
                      code: str,
                      name: str,
                      trigger_type: str,
                      sector: str,
                      weight: float,
                      profit_pct: float,
                      trigger_price: float,
                      current_price: float) -> Dict:
        """
        完整分析流程
        
        Returns:
            完整的分析报告
        """
        # 1. 行业前景评估
        sector_eval = self.evaluate_sector(code, sector)
        
        # 2. 仓位分析
        position_eval = self.analyze_position(weight, profit_pct)
        
        # 3. 综合置信度
        combined_confidence = (sector_eval["confidence"] * 0.6 + 
                              (0.8 if position_eval["risk"] != "high" else 0.4) * 0.4)
        
        # 4. 生成建议
        recommendation = self.generate_recommendation(
            trigger_type=trigger_type,
            industry_score=sector_eval["score"],
            position_risk=position_eval["risk"],
            profit_pct=profit_pct,
            confidence=combined_confidence
        )
        
        # 5. 组装报告
        report = {
            "etf": {
                "code": code,
                "name": name,
                "sector": sector,
                "current_price": current_price,
                "trigger_price": trigger_price
            },
            "trigger": {
                "type": trigger_type,
            },
            "position": {
                "weight": weight,
                "profit_pct": profit_pct,
                "level": position_eval["level"],
                "risk": position_eval["risk"]
            },
            "industry": {
                "score": sector_eval["score"],
                "score_text": OUTLOOK_SCORE_MAP.get(sector_eval["score"], "未知"),
                "trend": sector_eval["trend"],
                "factors": sector_eval["factors"]
            },
            "recommendation": recommendation,
            "market_state": self.market_state,
            "timestamp": datetime.now().isoformat()
        }
        
        return report


# ============ 便捷函数 ============

_evaluator = None

def get_evaluator() -> QuantaAlphaEvaluator:
    """获取评估器单例"""
    global _evaluator
    if _evaluator is None:
        _evaluator = QuantaAlphaEvaluator()
    return _evaluator

def analyze_trigger_smart(code: str,
                          name: str,
                          trigger_type: str,
                          sector: str,
                          weight: float,
                          profit_pct: float,
                          trigger_price: float,
                          current_price: float) -> Dict:
    """
    智能分析触发条件
    
    Args:
        code: ETF 代码
        name: ETF 名称
        trigger_type: stop_loss / take_profit / grid
        sector: 所属行业
        weight: 持仓权重 (%)
        profit_pct: 盈亏比例 (%)
        trigger_price: 触发价格
        current_price: 当前价格
    
    Returns:
        完整分析报告
    """
    evaluator = get_evaluator()
    return evaluator.full_analysis(
        code=code,
        name=name,
        trigger_type=trigger_type,
        sector=sector,
        weight=weight,
        profit_pct=profit_pct,
        trigger_price=trigger_price,
        current_price=current_price
    )


# ============ 测试 ============

if __name__ == "__main__":
    print("=" * 80)
    print("ETF-QuantaAlpha 智能评估模块测试")
    print("=" * 80)
    
    # 测试场景 1：止损触发 - 行业前景好
    print("\n【测试 1】黄金 9999 止损触发（行业前景好）")
    result = analyze_trigger_smart(
        code="159937",
        name="黄金 9999",
        trigger_type="stop_loss",
        sector="黄金",
        weight=9.46,
        profit_pct=-11.8,
        trigger_price=9.604,
        current_price=9.412
    )
    
    print(f"行业评分：{result['industry']['score']}/5 ({result['industry']['score_text']})")
    print(f"仓位风险：{result['position']['risk']}")
    print(f"建议：{result['recommendation']['recommendation']}")
    print(f"置信度：{result['recommendation']['confidence_level']}")
    print(f"原因:")
    for reason in result['recommendation']['reasons']:
        print(f"  - {reason}")
    
    # 测试场景 2：止盈触发 - 原油
    print("\n【测试 2】嘉实原油止盈触发（盈利 150%）")
    result = analyze_trigger_smart(
        code="160723",
        name="嘉实原油",
        trigger_type="take_profit",
        sector="原油",
        weight=3.68,
        profit_pct=150.0,
        trigger_price=1.301,
        current_price=2.710
    )
    
    print(f"行业评分：{result['industry']['score']}/5")
    print(f"建议：{result['recommendation']['recommendation']}")
    print(f"原因:")
    for reason in result['recommendation']['reasons']:
        print(f"  - {reason}")
    
    # 测试场景 3：网格加仓 - 半导体
    print("\n【测试 3】半导体网格加仓触发")
    result = analyze_trigger_smart(
        code="512480",
        name="半导体",
        trigger_type="grid",
        sector="半导体",
        weight=2.85,
        profit_pct=-7.0,
        trigger_price=1.378,
        current_price=1.462
    )
    
    print(f"行业评分：{result['industry']['score']}/5")
    print(f"建议：{result['recommendation']['recommendation']}")
    print(f"原因:")
    for reason in result['recommendation']['reasons']:
        print(f"  - {reason}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
