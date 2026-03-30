#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 智能触发器监控 v2.0
多维评分系统 + 动态档位 + 智能仓位管理

监控频率：15 分钟
触发条件：综合评分≥70 分
"""

import json
import time
from datetime import datetime
from typing import Dict, Optional

# ============ 配置区域 ============

MONITOR_INTERVAL = 900  # 15 分钟
TRIGGER_THRESHOLD = 60  # 综合评分≥60 分

WEIGHTS = {
    "price": 0.30, "volume": 0.25, "sector": 0.20,
    "technical": 0.15, "market": 0.10
}

POSITION_CONFIG = {
    "light": 5.0, "heavy": 8.0,
    "light_ratio": 1.0, "normal_ratio": 0.5, "heavy_ratio": 0.0
}

GRID_ADJUSTMENT = {
    "bull": [-3, -6, -10],
    "sideways": [-5, -10, -15],
    "bear": [-8, -15, -25]
}

SECTOR_OUTLOOK = {
    "159937": {"sector": "黄金", "outlook": 4},
    "512480": {"sector": "半导体", "outlook": 4},
    "513500": {"sector": "美股", "outlook": 3},
    "510300": {"sector": "A 股", "outlook": 5},
    "510500": {"sector": "A 股", "outlook": 5},
    "159363": {"sector": "AI", "outlook": 4},
    "160723": {"sector": "原油", "outlook": 3},
    "159663": {"sector": "制造", "outlook": 4},
    "159566": {"sector": "新能源", "outlook": 4},
    "159206": {"sector": "航天", "outlook": 4},
}

# ============ 智能评分器 ============

class SmartScorer:
    def __init__(self):
        self.market_state = "sideways"
    
    def score_price(self, change_pct: float, grid_level: int) -> float:
        """价格信号评分 (0-100 分，后续会加权)"""
        if change_pct < -15: base = 100
        elif change_pct < -10: base = 85
        elif change_pct < -8: base = 70
        elif change_pct < -5: base = 55
        elif change_pct < -3: base = 40
        else: base = 20
        
        grid_bonus = grid_level * 5
        total = min(base + grid_bonus, 100)
        return total
    
    def score_volume(self, volume_ratio: float) -> float:
        """成交量评分 (0-100 分)"""
        if volume_ratio > 2.0: return 100
        elif volume_ratio > 1.5: return 80
        elif volume_ratio > 1.2: return 60
        elif volume_ratio > 0.8: return 40
        else: return 20
    
    def score_sector(self, code: str) -> float:
        """行业趋势评分 (0-100 分)"""
        outlook = SECTOR_OUTLOOK.get(code, {"outlook": 3})
        return outlook["outlook"] * 20  # 5 分=100, 4 分=80, 3 分=60
    
    def score_technical(self, rsi: float) -> float:
        """技术指标评分 (0-100 分)"""
        if rsi < 20: return 100
        elif rsi < 30: return 80
        elif rsi < 40: return 55
        else: return 30
    
    def score_market(self, market_change: float) -> float:
        """市场情绪评分 (0-100 分)"""
        if market_change > 0: return 100
        elif market_change > -1: return 70
        elif market_change > -2: return 40
        else: return 20
    
    def total_score(self, code: str, change_pct: float, grid_level: int,
                    volume_ratio: float, rsi: float, market_change: float) -> Dict:
        """计算综合评分"""
        scores = {
            "price": self.score_price(change_pct, grid_level),
            "volume": self.score_volume(volume_ratio),
            "sector": self.score_sector(code),
            "technical": self.score_technical(rsi),
            "market": self.score_market(market_change)
        }
        
        weighted = sum(scores[k] * WEIGHTS[k] for k in scores)
        
        return {
            "scores": scores,
            "weighted": weighted,
            "max_score": 100,
            "threshold": TRIGGER_THRESHOLD,
            "trigger": weighted >= TRIGGER_THRESHOLD
        }

# ============ 智能触发器 ============

class SmartTrigger:
    def __init__(self):
        self.scorer = SmartScorer()
        self.last_signals = {}  # 缓存上次信号，用于确认
    
    def detect_market_state(self, etf_300_change: float) -> str:
        """判断市场状态"""
        if etf_300_change > 2:
            return "bull"
        elif etf_300_change < -10:
            return "bear"
        else:
            return "sideways"
    
    def get_dynamic_grids(self, market_state: str) -> list:
        """获取动态网格档位"""
        return GRID_ADJUSTMENT.get(market_state, GRID_ADJUSTMENT["sideways"])
    
    def get_position_ratio(self, weight: float) -> float:
        """根据仓位获取加仓比例"""
        if weight < POSITION_CONFIG["light"]:
            return POSITION_CONFIG["light_ratio"]
        elif weight < POSITION_CONFIG["heavy"]:
            return POSITION_CONFIG["normal_ratio"]
        else:
            return POSITION_CONFIG["heavy_ratio"]
    
    def check_trigger(self, code: str, name: str, current_price: float,
                      cost: float, weight: float, etf_data: Dict) -> Optional[Dict]:
        """
        检查是否触发智能加仓
        
        Returns:
            触发信号或 None
        """
        # 获取动态网格
        market_state = self.detect_market_state(etf_data.get("market_change", 0))
        grids = self.get_dynamic_grids(market_state)
        
        # 计算跌幅
        change_pct = etf_data.get("change_pct", 0)
        
        # 判断触及哪一档
        grid_level = 0
        for i, grid_pct in enumerate(grids, 1):
            if change_pct <= grid_pct:
                grid_level = i
        
        if grid_level == 0:
            return None  # 未触及网格
        
        # 计算综合评分
        volume_ratio = etf_data.get("volume_ratio", 1.0)
        rsi = etf_data.get("rsi", 50)
        market_change = etf_data.get("market_change", 0)
        
        result = self.scorer.total_score(
            code=code,
            change_pct=change_pct,
            grid_level=grid_level,
            volume_ratio=volume_ratio,
            rsi=rsi,
            market_change=market_change
        )
        
        if not result["trigger"]:
            return None  # 评分不足
        
        # 计算加仓金额
        base_amount = 5000
        position_ratio = self.get_position_ratio(weight)
        actual_amount = base_amount * position_ratio
        
        if actual_amount <= 0:
            return None  # 重仓暂停加仓
        
        # 生成信号
        signal = {
            "code": code,
            "name": name,
            "type": "grid_buy",
            "grid_level": grid_level,
            "grid_price_pct": grids[grid_level-1],
            "current_price": current_price,
            "change_pct": change_pct,
            "weight": weight,
            "score": result["weighted"],
            "score_breakdown": result["scores"],
            "market_state": market_state,
            "base_amount": base_amount,
            "position_ratio": position_ratio,
            "actual_amount": actual_amount,
            "recommendation": self._generate_recommendation(result, weight, market_state),
            "timestamp": datetime.now().isoformat()
        }
        
        # 确认机制（需要连续 2 次信号）
        signal_key = f"{code}_grid_{grid_level}"
        if signal_key in self.last_signals:
            signal["confirmed"] = True
            signal["confirm_count"] = 2
        else:
            signal["confirmed"] = False
            signal["confirm_count"] = 1
            self.last_signals[signal_key] = signal
        
        return signal
    
    def _generate_recommendation(self, result: Dict, weight: float, market_state: str) -> str:
        """生成操作建议"""
        score = result["weighted"]
        
        if score >= 85:
            rec = "✅ 强烈建议加仓"
        elif score >= 70:
            rec = "✅ 建议加仓"
        else:
            rec = "🟡 谨慎加仓"
        
        if weight >= POSITION_CONFIG["heavy"]:
            rec += " (但仓位已重，建议暂停)"
        elif weight >= POSITION_CONFIG["light"]:
            rec += " (仓位适中，减半加仓)"
        
        if market_state == "bear":
            rec += " (熊市谨慎)"
        
        return rec

# ============ 测试 ============

if __name__ == "__main__":
    print("=" * 80)
    print("ETF 智能触发器 v2.0 测试")
    print("=" * 80)
    
    trigger = SmartTrigger()
    
    # 测试场景 1: 黄金 9999 触及第 2 档网格
    print("\n【测试 1】黄金 9999 触及第 2 档网格 (-10%)")
    signal = trigger.check_trigger(
        code="159937",
        name="黄金 9999",
        current_price=9.412,
        cost=10.671,
        weight=9.46,
        etf_data={
            "change_pct": -10.5,
            "volume_ratio": 1.8,
            "rsi": 25,
            "market_change": -0.5
        }
    )
    
    if signal:
        print(f"  触发：✅ 是")
        print(f"  综合评分：{signal['score']:.1f}/100")
        print(f"  评分明细：{signal['score_breakdown']}")
        print(f"  市场状态：{signal['market_state']}")
        print(f"  建议：{signal['recommendation']}")
        print(f"  加仓金额：{signal['actual_amount']}元")
    else:
        print(f"  触发：❌ 否")
    
    # 测试场景 2: 半导体触及第 1 档
    print("\n【测试 2】半导体触及第 1 档网格 (-5%)")
    signal = trigger.check_trigger(
        code="512480",
        name="半导体",
        current_price=1.462,
        cost=1.572,
        weight=2.85,
        etf_data={
            "change_pct": -5.2,
            "volume_ratio": 2.1,
            "rsi": 28,
            "market_change": 0.3
        }
    )
    
    if signal:
        print(f"  触发：✅ 是")
        print(f"  综合评分：{signal['score']:.1f}/100")
        print(f"  建议：{signal['recommendation']}")
        print(f"  加仓金额：{signal['actual_amount']}元")
    else:
        print(f"  触发：❌ 否")
    
    # 测试场景 3: 300ETF 轻微下跌
    print("\n【测试 3】300ETF 轻微下跌 (-2%)")
    signal = trigger.check_trigger(
        code="510300",
        name="300ETF",
        current_price=4.501,
        cost=4.592,
        weight=7.98,
        etf_data={
            "change_pct": -2.0,
            "volume_ratio": 0.9,
            "rsi": 45,
            "market_change": -0.3
        }
    )
    
    if signal:
        print(f"  触发：✅ 是")
    else:
        print(f"  触发：❌ 否 (未达网格)")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
