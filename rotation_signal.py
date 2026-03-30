#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF-QuantaAlpha 轮动信号挖掘模块
发现行业轮动机会，输出调仓建议

第三阶段子任务 2：轮动信号挖掘
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

# ============ 配置区域 ============

SECTOR_MAPPING = {
    "512480": {"sector": "科技", "subsector": "半导体", "name": "半导体 ETF"},
    "159819": {"sector": "科技", "subsector": "AI", "name": "人工智能 ETF"},
    "159363": {"sector": "科技", "subsector": "AI", "name": "创业板 AI"},
    "515790": {"sector": "新能源", "subsector": "光伏", "name": "光伏 ETF"},
    "159566": {"sector": "新能源", "subsector": "储能", "name": "储能电池"},
    "159663": {"sector": "高端制造", "subsector": "机床", "name": "机床 ETF"},
    "159206": {"sector": "高端制造", "subsector": "卫星", "name": "卫星 ETF"},
    "512010": {"sector": "医药", "subsector": "医药", "name": "医药 ETF"},
    "160723": {"sector": "周期", "subsector": "原油", "name": "嘉实原油"},
    "510300": {"sector": "宽基", "subsector": "沪深 300", "name": "300ETF"},
    "510500": {"sector": "宽基", "subsector": "中证 500", "name": "500ETF"},
    "513110": {"sector": "海外", "subsector": "纳指", "name": "纳指 100"},
    "513500": {"sector": "海外", "subsector": "标普", "name": "标普 500"},
    "510880": {"sector": "策略", "subsector": "红利", "name": "红利 ETF"},
    "159937": {"sector": "商品", "subsector": "黄金", "name": "黄金 9999"},
}

# ============ 轮动分析器 ============

class SectorRotationAnalyzer:
    """行业轮动分析器"""
    
    def __init__(self):
        self.sector_data = {}
        self.rotation_signals = []
    
    def load_sector_data(self, etf_prices: Dict) -> None:
        """加载行业数据"""
        self.sector_data = {}
        
        for code, data in etf_prices.items():
            if code not in SECTOR_MAPPING:
                continue
            
            info = SECTOR_MAPPING[code]
            sector = info["sector"]
            
            if sector not in self.sector_data:
                self.sector_data[sector] = {
                    "etfs": [],
                    "avg_pe": 0,
                    "avg_return_20d": 0,
                    "avg_volume_ratio": 0,
                    "trend": "sideways"
                }
            
            self.sector_data[sector]["etfs"].append({
                "code": code,
                "name": data.get("name", info["name"]),
                "pe": data.get("pe_percentile", 50),
                "return_20d": data.get("return_20d", 0),
                "volume_ratio": data.get("volume_ratio", 1.0),
                "price": data.get("price", 0),
                "change_pct": data.get("change_pct", 0)
            })
        
        # 计算行业平均值
        for sector, data in self.sector_data.items():
            etfs = data["etfs"]
            if etfs:
                data["avg_pe"] = sum(e["pe"] for e in etfs) / len(etfs)
                data["avg_return_20d"] = sum(e["return_20d"] for e in etfs) / len(etfs)
                data["avg_volume_ratio"] = sum(e["volume_ratio"] for e in etfs) / len(etfs)
                
                if data["avg_return_20d"] > 5:
                    data["trend"] = "up"
                elif data["avg_return_20d"] < -5:
                    data["trend"] = "down"
                else:
                    data["trend"] = "sideways"
    
    def detect_rotation_signals(self) -> List[Dict]:
        """检测轮动信号"""
        signals = []
        sectors = list(self.sector_data.keys())
        
        for i, from_sector in enumerate(sectors):
            for to_sector in sectors[i+1:]:
                signal = self._analyze_pair(from_sector, to_sector)
                if signal and signal["confidence"] >= 0.6:
                    signals.append(signal)
        
        signals.sort(key=lambda x: x["confidence"], reverse=True)
        self.rotation_signals = signals
        return signals
    
    def _analyze_pair(self, from_sector: str, to_sector: str) -> Optional[Dict]:
        """分析两个行业之间的轮动机会"""
        from_data = self.sector_data.get(from_sector, {})
        to_data = self.sector_data.get(to_sector, {})
        
        if not from_data or not to_data:
            return None
        
        valuation_gap = from_data["avg_pe"] - to_data["avg_pe"]
        momentum_switch = to_data["avg_return_20d"] - from_data["avg_return_20d"]
        volume_confirm = to_data["avg_volume_ratio"] / max(from_data["avg_volume_ratio"], 0.1)
        
        valuation_score = min(abs(valuation_gap) / 100, 1.0)
        momentum_score = min(abs(momentum_switch) / 10, 1.0)
        volume_score = min(volume_confirm / 2, 1.0)
        
        trend_score = 0
        if to_data["trend"] == "up" and from_data["trend"] != "up":
            trend_score = 1.0
        elif to_data["trend"] == "sideways" and from_data["trend"] == "down":
            trend_score = 0.7
        elif to_data["trend"] == from_data["trend"]:
            trend_score = 0.3
        
        confidence = (valuation_score * 0.25 + momentum_score * 0.35 + 
                     volume_score * 0.20 + trend_score * 0.20)
        
        # 降低阈值，捕捉更多信号
        if confidence >= 0.45:
            if momentum_switch > 0 and valuation_gap > 0:
                direction = f"{from_sector} → {to_sector}"
                from_etfs = from_data["etfs"]
                to_etfs = to_data["etfs"]
            elif momentum_switch < 0 and valuation_gap < 0:
                direction = f"{to_sector} → {from_sector}"
                from_etfs = to_data["etfs"]
                to_etfs = from_data["etfs"]
            else:
                return None
            
            reasons = []
            if abs(valuation_gap) > 15:
                reasons.append("估值优势" if valuation_gap > 0 else "估值偏高")
            if abs(momentum_switch) > 5:
                reasons.append("动量切换" if momentum_switch > 0 else "动量减弱")
            if volume_confirm > 1.5:
                reasons.append("放量确认")
            
            return {
                "from_sector": from_sector if momentum_switch > 0 else to_sector,
                "to_sector": to_sector if momentum_switch > 0 else from_sector,
                "direction": direction,
                "valuation_gap": abs(valuation_gap),
                "momentum_switch": abs(momentum_switch),
                "volume_confirm": volume_confirm,
                "confidence": confidence,
                "confidence_level": "高" if confidence >= 0.75 else "中",
                "from_etfs": from_etfs[:2],
                "to_etfs": to_etfs[:2],
                "logic": "；".join(reasons) if reasons else "行业轮动信号",
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    def generate_report(self, top_n: int = 5) -> Dict:
        """生成轮动报告"""
        if not self.rotation_signals:
            self.detect_rotation_signals()
        
        return {
            "summary": {
                "total_signals": len(self.rotation_signals),
                "high_confidence": sum(1 for s in self.rotation_signals if s["confidence"] >= 0.75),
                "scan_time": datetime.now().isoformat()
            },
            "sector_overview": {
                sector: {
                    "trend": data["trend"],
                    "avg_pe": data["avg_pe"],
                    "avg_return_20d": data["avg_return_20d"],
                    "etf_count": len(data["etfs"])
                }
                for sector, data in self.sector_data.items()
            },
            "top_signals": self.rotation_signals[:top_n],
            "timestamp": datetime.now().isoformat()
        }


def scan_rotation_signals(etf_prices: Dict, top_n: int = 5) -> Dict:
    """扫描轮动信号"""
    analyzer = SectorRotationAnalyzer()
    analyzer.load_sector_data(etf_prices)
    analyzer.detect_rotation_signals()
    return analyzer.generate_report(top_n)


if __name__ == "__main__":
    print("=" * 80)
    print("ETF-QuantaAlpha 轮动信号挖掘测试")
    print("=" * 80)
    
    mock_prices = {
        "512480": {"name": "半导体 ETF", "pe_percentile": 20, "return_20d": 8.5, "volume_ratio": 2.5, "price": 1.462},
        "159819": {"name": "人工智能 ETF", "pe_percentile": 25, "return_20d": 10.2, "volume_ratio": 2.8, "price": 1.477},
        "515790": {"name": "光伏 ETF", "pe_percentile": 45, "return_20d": -8.2, "volume_ratio": 0.5, "price": 1.102},
        "159566": {"name": "储能电池", "pe_percentile": 35, "return_20d": -2.3, "volume_ratio": 0.8, "price": 2.250},
        "159663": {"name": "机床 ETF", "pe_percentile": 18, "return_20d": 12.8, "volume_ratio": 2.2, "price": 1.735},
        "159206": {"name": "卫星 ETF", "pe_percentile": 50, "return_20d": -1.9, "volume_ratio": 0.7, "price": 1.592},
        "510300": {"name": "300ETF", "pe_percentile": 10, "return_20d": -5.0, "volume_ratio": 1.1, "price": 4.501},
        "510500": {"name": "500ETF", "pe_percentile": 15, "return_20d": -3.7, "volume_ratio": 1.0, "price": 7.769},
        "513110": {"name": "纳指 100", "pe_percentile": 30, "return_20d": -6.9, "volume_ratio": 1.3, "price": 1.921},
        "513500": {"name": "标普 500", "pe_percentile": 25, "return_20d": -5.6, "volume_ratio": 1.2, "price": 2.200},
    }
    
    report = scan_rotation_signals(mock_prices, top_n=5)
    
    print(f"\n📊 轮动信号扫描结果")
    print(f"扫描时间：{report['summary']['scan_time']}")
    print(f"总信号数：{report['summary']['total_signals']}")
    print(f"高置信度：{report['summary']['high_confidence']}")
    
    print(f"\n📈 行业概览")
    print(f"{'行业':<10} {'趋势':<8} {'平均 PE':>10} {'20 日收益':>10}")
    print("-" * 45)
    for sector, data in report['sector_overview'].items():
        print(f"{sector:<10} {data['trend']:<8} {data['avg_pe']:>10.1f} {data['avg_return_20d']:>9.1f}%")
    
    print(f"\n🔄 Top 轮动信号")
    for i, signal in enumerate(report['top_signals'], 1):
        print(f"\n【信号{i}】{signal['direction']}")
        print(f"  置信度：{signal['confidence_level']} ({signal['confidence']:.2f})")
        print(f"  估值差：{signal['valuation_gap']:.1f}")
        print(f"  动量切换：{signal['momentum_switch']:.1f}%")
        print(f"  逻辑：{signal['logic']}")
        
        if signal['to_etfs']:
            print(f"  建议关注：{signal['to_etfs'][0]['name']} ({signal['to_etfs'][0]['code']})")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
