#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 智能触发器监控 v2.1 (Tushare 增强版)
改进：1. Tushare 主数据源 2. 多指数综合市场判断
多维评分 + 动态档位 + 智能仓位管理

监控频率：15 分钟
触发条件：综合评分≥60 分 + 连续 2 次确认
"""

import json
import time
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

# ============ 导入 Tushare 数据模块 ============
sys.path.insert(0, '/home/admin/openclaw/workspace')
from tushare_finance_data import get_etf_realtime_minute, get_index_realtime_minute

# ============ 配置区域 ============

MONITOR_INTERVAL = 900  # 15 分钟
TRIGGER_THRESHOLD = 60  # 综合评分≥60 分

WEIGHTS = {"price": 0.30, "volume": 0.25, "sector": 0.20, "technical": 0.15, "market": 0.10}

POSITION_CONFIG = {"light": 5.0, "heavy": 8.0, "light_ratio": 1.0, "normal_ratio": 0.5, "heavy_ratio": 0.0}

GRID_ADJUSTMENT = {"bull": [-3, -6, -10], "sideways": [-5, -10, -15], "bear": [-8, -15, -25]}

HOLDINGS_FILE = "/home/admin/openclaw/workspace/holdings_current.json"
TRIGGER_RECORD_FILE = "/home/admin/openclaw/workspace/trigger_records_v2.json"

FEISHU_APP_ID = "cli_a9493d702278dbb7"
FEISHU_APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
FEISHU_USER_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"
API_BASE = "https://open.feishu.cn/open-apis"

# ============ 多指数市场状态判断 ============

INDEX_POOL = {
    '300ETF': {'code': '510300', 'ts_code': '000300.SH', 'weight': 0.30, 'name': '沪深 300'},
    '500ETF': {'code': '510500', 'ts_code': '000905.SH', 'weight': 0.20, 'name': '中证 500'},
    '创业板': {'code': '159915', 'ts_code': '399006.SZ', 'weight': 0.20, 'name': '创业板指'},
    '科创 50': {'code': '588000', 'ts_code': '000688.SH', 'weight': 0.15, 'name': '科创 50'},
    '红利': {'code': '510880', 'ts_code': '000015.SH', 'weight': 0.15, 'name': '红利指数'},
}

def calculate_minute_change(latest_bar: Dict, pre_close: float, fallback_to_open: bool = True) -> float:
    """
    计算分钟线涨跌幅
    
    Args:
        latest_bar: 最新分钟 K 线数据
        pre_close: 昨日收盘价 (可能为 0)
        fallback_to_open: 如果没有 pre_close，是否使用开盘价估算
    
    Returns:
        涨跌幅百分比
    """
    current_price = latest_bar.get('close', 0)
    if current_price <= 0:
        return 0
    
    # 优先使用 pre_close
    if pre_close and pre_close > 0:
        return (current_price - pre_close) / pre_close * 100
    
    # 如果没有 pre_close，使用开盘价估算 (近似值)
    if fallback_to_open:
        open_price = latest_bar.get('open', 0)
        if open_price and open_price > 0:
            # 估算：假设开盘相对昨日收盘的涨跌幅较小
            # 实际涨跌幅 ≈ (当前价 - 开盘价) / 开盘价 * 100
            # 这是一个近似值，用于盘中监控
            return (current_price - open_price) / open_price * 100
    
    return 0

def detect_market_state_multi_index_minute() -> Dict:
    """
    多指数综合判断市场状态 (分钟级版本)
    
    Returns:
        {
            'state': 'bull'/'sideways'/'bear',
            'composite_change': 综合涨跌幅，
            'indices': 各指数详细数据，
            'breadth': 市场广度（涨跌比）
        }
    """
    try:
        # 获取指数实时分钟数据 (5 分钟)
        index_codes = [idx['ts_code'] for idx in INDEX_POOL.values()]
        
        # 使用 get_index_realtime_minute 获取分钟线
        from tushare_finance_data import get_index_realtime_minute
        index_data = get_index_realtime_minute(index_codes, freq='5MIN')
        
        if not index_data:
            print("⚠️ 获取指数分钟数据失败，使用日线数据降级")
            return detect_market_state_multi_index()
        
        # 计算加权综合涨跌
        composite_change = 0
        up_count = 0
        down_count = 0
        indices_detail = {}
        
        for name, config in INDEX_POOL.items():
            ts_code = config['ts_code']
            ts_code_short = ts_code.split('.')[0]
            code = config['code']
            weight = config['weight']
            
            # 尝试两种键名匹配
            data = index_data.get(ts_code) or index_data.get(ts_code_short)
            
            if data and data.get('data') and len(data['data']) > 0:
                # 取最新一根分钟 K 线
                latest_bar = data['data'][-1]
                pre_close = data.get('pre_close', latest_bar.get('open', 0))
                change_pct = calculate_minute_change(latest_bar, pre_close)
                
                # 计算加权贡献
                composite_change += change_pct * weight
                
                # 统计涨跌家数
                if change_pct > 0:
                    up_count += 1
                elif change_pct < 0:
                    down_count += 1
                
                indices_detail[code] = {
                    'name': config['name'],
                    'change_pct': change_pct,
                    'weight': weight,
                    'contribution': change_pct * weight,
                    'time': latest_bar.get('time', '')
                }
        
        # 计算市场广度
        total = up_count + down_count
        breadth = up_count / total if total > 0 else 1.0
        
        # 判断市场状态
        if composite_change > 1.0:
            state = 'bull'
        elif composite_change < -1.0:
            state = 'bear'
        else:
            state = 'sideways'
        
        return {
            'state': state,
            'composite_change': composite_change,
            'indices': indices_detail,
            'breadth': breadth
        }
        
    except Exception as e:
        print(f"⚠️ 多指数分钟判断失败：{e}")
        return detect_market_state_multi_index()

def detect_market_state_multi_index() -> Dict:
    """
    多指数综合判断市场状态
    
    Returns:
        {
            'state': 'bull'/'sideways'/'bear',
            'composite_change': 综合涨跌幅，
            'indices': 各指数详细数据，
            'breadth': 市场广度（涨跌比）
        }
    """
    try:
        # 获取指数实时数据
        index_codes = [idx['ts_code'] for idx in INDEX_POOL.values()]
        index_data = get_index_realtime_daily(index_codes)
        
        if not index_data:
            print("⚠️ 获取指数数据失败，使用默认震荡")
            return {
                'state': 'sideways',
                'composite_change': 0,
                'indices': {},
                'breadth': 1.0
            }
        
        # 计算加权综合涨跌
        composite_change = 0
        up_count = 0
        down_count = 0
        indices_detail = {}
        
        for name, config in INDEX_POOL.items():
            ts_code = config['ts_code']
            ts_code_short = ts_code.split('.')[0]  # 000300.SH → 000300
            code = config['code']
            weight = config['weight']
            
            # 尝试两种键名匹配
            data = index_data.get(ts_code) or index_data.get(ts_code_short)
            
            if data:
                # 获取涨跌幅
                change_pct = data.get('change_pct', 0)
                if change_pct is None:
                    change_pct = 0
                
                # 计算加权贡献
                composite_change += change_pct * weight
                
                # 统计涨跌家数
                if change_pct > 0:
                    up_count += 1
                elif change_pct < 0:
                    down_count += 1
                
                indices_detail[code] = {
                    'name': config['name'],
                    'change_pct': change_pct,
                    'weight': weight,
                    'contribution': change_pct * weight
                }
        
        # 计算市场广度
        total = up_count + down_count
        breadth = up_count / total if total > 0 else 1.0
        
        # 判断市场状态
        if composite_change > 1.0:
            state = 'bull'
        elif composite_change < -1.0:
            state = 'bear'
        else:
            state = 'sideways'
        
        return {
            'state': state,
            'composite_change': composite_change,
            'indices': indices_detail,
            'breadth': breadth
        }
        
    except Exception as e:
        print(f"⚠️ 多指数判断失败：{e}")
        return {
            'state': 'sideways',
            'composite_change': 0,
            'indices': {},
            'breadth': 1.0
        }

# ============ 智能评分器 ============

class SmartScorer:
    def __init__(self):
        self.market_state = "sideways"
    
    def set_market_state(self, state: str):
        self.market_state = state
    
    def score_price(self, change_pct: float, grid_level: int) -> float:
        if change_pct < -15: base = 100
        elif change_pct < -10: base = 85
        elif change_pct < -8: base = 70
        elif change_pct < -5: base = 55
        elif change_pct < -3: base = 40
        else: base = 20
        return min(base + grid_level * 5, 100)
    
    def score_volume(self, volume_ratio: float) -> float:
        if volume_ratio > 2.0: return 100
        elif volume_ratio > 1.5: return 80
        elif volume_ratio > 1.2: return 60
        elif volume_ratio > 0.8: return 40
        else: return 20
    
    def score_sector(self, code: str, outlook: Dict) -> float:
        data = outlook.get(code, {"outlook": 3})
        return data["outlook"] * 20
    
    def score_technical(self, rsi: float) -> float:
        if rsi < 20: return 100
        elif rsi < 30: return 80
        elif rsi < 40: return 55
        else: return 30
    
    def score_market(self, market_change: float) -> float:
        if market_change > 0: return 100
        elif market_change > -1: return 70
        elif market_change > -2: return 40
        else: return 20
    
    def total_score(self, code, change_pct, grid_level, volume_ratio, rsi, market_change, outlook) -> Dict:
        scores = {
            "price": self.score_price(change_pct, grid_level),
            "volume": self.score_volume(volume_ratio),
            "sector": self.score_sector(code, outlook),
            "technical": self.score_technical(rsi),
            "market": self.score_market(market_change)
        }
        weighted = sum(scores[k] * WEIGHTS[k] for k in scores)
        return {"scores": scores, "weighted": round(weighted, 1), "trigger": weighted >= TRIGGER_THRESHOLD}

# ============ 智能触发器 ============

class SmartTrigger:
    def __init__(self):
        self.scorer = SmartScorer()
        self.last_signals = {}
        self.holdings = {}
        self.outlook = {}
    
    def load_holdings(self) -> bool:
        try:
            if os.path.exists(HOLDINGS_FILE):
                with open(HOLDINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 支持两种格式：etfs 或 holdings
                    etf_list = data.get('etfs', data.get('holdings', []))
                    self.holdings = {item['code']: item for item in etf_list}
                print(f"✅ 加载持仓 {len(self.holdings)} 只")
                return True
        except Exception as e:
            print(f"❌ 加载持仓失败：{e}")
        return False
    
    def load_outlook(self):
        self.outlook = {
            "159937": {"sector": "黄金", "outlook": 4}, "512480": {"sector": "半导体", "outlook": 4},
            "513500": {"sector": "美股", "outlook": 3}, "510300": {"sector": "A 股", "outlook": 5},
            "510500": {"sector": "A 股", "outlook": 5}, "159363": {"sector": "AI", "outlook": 4},
            "160723": {"sector": "原油", "outlook": 3}, "159663": {"sector": "制造", "outlook": 4},
            "159566": {"sector": "新能源", "outlook": 4}, "159206": {"sector": "航天", "outlook": 4},
        }
    
    def get_position_ratio(self, weight: float) -> float:
        if weight < POSITION_CONFIG["light"]: return POSITION_CONFIG["light_ratio"]
        elif weight < POSITION_CONFIG["heavy"]: return POSITION_CONFIG["normal_ratio"]
        else: return POSITION_CONFIG["heavy_ratio"]
    
    def check_all_etfs(self, prices: Dict, market_info: Dict) -> list:
        signals = []
        market_change = market_info.get('composite_change', 0)
        market_state = market_info.get('state', 'sideways')
        self.scorer.set_market_state(market_state)
        grids = GRID_ADJUSTMENT.get(market_state, GRID_ADJUSTMENT["sideways"])
        
        print(f"\n📊 市场状态：{market_state} (综合 {market_change:+.2f}%), 网格：{grids}")
        print(f"   市场广度：{market_info.get('breadth', 1.0):.2f} (涨/跌)")
        
        for code, holding in self.holdings.items():
            if code not in prices: continue
            
            pdata = prices[code]
            change_pct = pdata.get("change_pct", 0)
            volume = pdata.get("volume", 0)
            volume_ratio = min(volume / 1000000, 3.0) if volume > 0 else 1.0
            
            grid_level = 0
            for i, grid in enumerate(grids, 1):
                if change_pct <= grid: grid_level = i
            
            if grid_level == 0: continue
            
            rsi = 50 + change_pct * 3  # 简化估算
            
            result = self.scorer.total_score(code, change_pct, grid_level, volume_ratio, rsi, market_change, self.outlook)
            
            if not result["trigger"]: continue
            
            weight = holding.get("weight", 0)
            position_ratio = self.get_position_ratio(weight)
            actual_amount = 5000 * position_ratio
            
            if actual_amount <= 0:
                print(f"  {holding['name']}: 评分{result['weighted']} 但重仓暂停")
                continue
            
            signal = {
                "code": code, "name": holding.get("name", pdata.get("name")),
                "grid_level": grid_level, "change_pct": change_pct, "weight": weight,
                "score": result["weighted"], "score_breakdown": result["scores"],
                "market_state": market_state, "actual_amount": actual_amount,
                "recommendation": f"{'✅ 建议加仓' if result['weighted']>=70 else '🟡 谨慎加仓'}",
                "timestamp": datetime.now().isoformat()
            }
            
            signal_key = f"{code}_grid_{grid_level}"
            if signal_key in self.last_signals:
                signal["confirmed"] = True
                signals.append(signal)
                print(f"  ✅ {holding['name']}: 评分{result['weighted']} 确认！加仓{actual_amount}元")
            else:
                signal["confirmed"] = False
                self.last_signals[signal_key] = signal
                print(f"  🟡 {holding['name']}: 评分{result['weighted']} 待确认 (1/2)")
        
        return signals

# ============ 飞书通知 ============

def get_feishu_token():
    import time
    cache = {"token": None, "expires_at": 0}
    if cache["token"] and time.time() < cache["expires_at"]:
        return cache["token"]
    try:
        resp = requests.post(f"{API_BASE}/auth/v3/tenant_access_token/internal",
                            json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            cache["token"] = data.get("tenant_access_token")
            cache["expires_at"] = time.time() + 7200
            return cache["token"]
    except Exception as e:
        print(f"❌ 飞书 token 失败：{e}")
    return None

def send_feishu_signal(signals: list):
    """发送触发信号到飞书"""
    if not signals: return
    
    token = get_feishu_token()
    if not token: return
    
    content = "## 📊 ETF 智能触发信号\n\n"
    for sig in signals:
        content += f"**{sig['name']} ({sig['code']})**\n"
        content += f"- 网格：第{sig['grid_level']}档 ({sig['change_pct']:.1f}%)\n"
        content += f"- 评分：{sig['score']}/100\n"
        content += f"- 加仓：{sig['actual_amount']:.0f}元\n"
        content += f"- 建议：{sig['recommendation']}\n\n"
    
    card = {
        "header": {"title": {"tag": "plain_text", "content": "📊 ETF 智能触发信号"}},
        "elements": [{"tag": "markdown", "content": content}]
    }
    
    try:
        resp = requests.post(f"{API_BASE}/im/v1/messages?receive_id_type=open_id",
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                            json={"receive_id": FEISHU_USER_ID, "msg_type": "interactive",
                                  "content": json.dumps(card)}, timeout=10)
        if resp.json().get("code") == 0:
            print(f"✅ 飞书通知已发送 ({len(signals)}个信号)")
    except Exception as e:
        print(f"❌ 飞书发送失败：{e}")

def send_feishu_status(market_info: Dict, etf_count: int, signal_count: int):
    """发送无信号时的状态报告"""
    token = get_feishu_token()
    if not token: return
    
    state = market_info.get('state', 'sideways')
    composite = market_info.get('composite_change', 0)
    breadth = market_info.get('breadth', 1.0)
    
    state_emoji = {'bull': '📈', 'bear': '📉', 'sideways': '➖'}.get(state, '➖')
    
    # 构建指数详情
    indices_text = ""
    for code, data in market_info.get('indices', {}).items():
        name = data.get('name', code)
        change = data.get('change_pct', 0)
        emoji = '📈' if change > 0 else ('📉' if change < 0 else '➖')
        indices_text += f"• {name}: {change:+.2f}% {emoji}\n"
    
    content = f"""⏰ ETF 智能触发器 v2.1 - {datetime.now().strftime('%H:%M')} 扫描

📊 扫描结果:
• 监控 ETF: {etf_count} 只
• 持仓 ETF: 20 只
• 触发信号：{signal_count} 个

{state_emoji} 市场状态:
• 综合涨跌：{composite:+.2f}%
• 市场广度：{breadth:.2f}
{indices_text}
✅ 无触发信号

💡 说明:
• 市场{state}整理，距离网格触发有距离
• 继续监控中...

⏭️ 下次扫描：{(datetime.now() + timedelta(minutes=15)).strftime('%H:%M')}

数据来源：Tushare Pro | 扫描时间：{datetime.now().strftime('%H:%M')}"""
    
    try:
        resp = requests.post(f"{API_BASE}/im/v1/messages?receive_id_type=open_id",
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                            json={"receive_id": FEISHU_USER_ID, "msg_type": "text",
                                  "content": json.dumps({"text": content})}, timeout=10)
        if resp.json().get("code") == 0:
            print(f"✅ 状态报告已发送")
    except Exception as e:
        print(f"❌ 飞书发送失败：{e}")

# ============ 主函数 ============

def main():
    print("=" * 80)
    print("ETF 智能触发器 v2.1 - 启动 (Tushare 增强版)")
    print(f"监控频率：15 分钟，触发阈值：{TRIGGER_THRESHOLD}分")
    print("=" * 80)
    
    trigger = SmartTrigger()
    if not trigger.load_holdings():
        print("❌ 加载持仓失败，退出")
        return
    
    trigger.load_outlook()
    
    # 步骤 1: 多指数综合判断市场状态 (使用分钟级数据)
    print("\n📊 多指数市场状态判断 (分钟级)...")
    market_info = detect_market_state_multi_index_minute()
    
    print(f"  市场状态：{market_info['state']} (综合 {market_info['composite_change']:+.2f}%)")
    print(f"  市场广度：{market_info['breadth']:.2f}")
    for code, data in market_info.get('indices', {}).items():
        print(f"    {data['name']}: {data['change_pct']:+.2f}% (权重{data['weight']*100:.0f}%)")
    
    # 步骤 2: 获取持仓 ETF 实时分钟数据 (Tushare 主数据源)
    print("\n📡 获取持仓 ETF 实时分钟数据 (Tushare Pro - 5 分钟)...")
    etf_codes = list(trigger.holdings.keys())
    
    try:
        # 获取 5 分钟分钟线数据
        minute_data = get_etf_realtime_minute(etf_codes, freq='5MIN')
        
        if not minute_data:
            print("⚠️ Tushare 分钟线数据不足，尝试降级...")
            prices = {}
        else:
            # 转换分钟线数据格式 (取最新一根 K 线)
            prices = {}
            for code in etf_codes:
                if code in minute_data:
                    data = minute_data[code]
                    # data 格式：{'code': '510300', 'freq': '5MIN', 'data': [...], 'count': N}
                    if data.get('data') and len(data['data']) > 0:
                        # 取最新一根 5 分钟 K 线
                        latest_bar = data['data'][-1]
                        
                        # 从持仓数据中获取 pre_close (昨日收盘价)
                        holding = trigger.holdings.get(code, {})
                        pre_close = holding.get('price', latest_bar.get('open', 0))
                        
                        prices[code] = {
                            'code': code,
                            'name': holding.get('name', data.get('name', '')),
                            'price': latest_bar.get('close', 0),
                            'change_pct': calculate_minute_change(latest_bar, pre_close),
                            'volume': latest_bar.get('vol', 0),
                            'time': latest_bar.get('time', ''),
                            'pre_close': pre_close,
                            'data_source': 'tushare_5min'
                        }
            print(f"✅ Tushare 分钟线获取 {len(prices)} 只 ETF 价格 (5 分钟级)")
    except Exception as e:
        print(f"❌ Tushare 分钟线获取失败：{e}")
        import traceback
        traceback.print_exc()
        prices = {}
    
    if not prices:
        print("⚠️ 无有效数据，退出")
        return
    
    # 步骤 3: 检查触发
    signals = trigger.check_all_etfs(prices, market_info)
    
    if signals:
        print(f"\n🎯 发现 {len(signals)} 个确认触发信号")
        send_feishu_signal(signals)
    else:
        print(f"\n✅ 无触发信号")
        # 发送状态报告
        send_feishu_status(market_info, len(prices), 0)
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()