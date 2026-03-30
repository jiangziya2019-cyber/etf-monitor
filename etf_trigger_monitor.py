#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 实时触发器监控脚本（带智能分析）
监控时间：交易日 9:00-15:00
功能：网格加仓/止盈/止损触发 + 自动分析建议
"""

import json
import time
import os
from datetime import datetime, timedelta

# ============ 配置区域 ============

# 网格加仓监控
GRID_MONITOR = {
    "159663": {"name": "科创芯片 ETF", "grid_5": 1.606, "grid_10": 1.522, "grid_15": 1.437, "amount": 5000},
    "517520": {"name": "新能源车 ETF", "grid_5": 2.014, "grid_10": 1.908, "grid_15": 1.802, "amount": 5000},
    "159243": {"name": "科创 50ETF", "grid_5": 1.018, "grid_10": 0.965, "grid_15": 0.911, "amount": 5000},
    "159819": {"name": "人工智能 ETF", "grid_5": 1.397, "grid_10": 1.324, "grid_15": 1.250, "amount": 5000},
    "515790": {"name": "光伏 ETF", "grid_5": 1.049, "grid_10": 0.994, "grid_15": 0.938, "amount": 5000},
    "512480": {"name": "半导体 ETF", "grid_5": 1.378, "grid_10": 1.305, "grid_15": 1.233, "amount": 5000},
    "159241": {"name": "恒生科技 ETF", "grid_5": 1.213, "grid_10": 1.149, "grid_15": 1.085, "amount": 5000},
    "159227": {"name": "碳中和 ETF", "grid_5": 1.188, "grid_10": 1.125, "grid_15": 1.063, "amount": 5000},
    "518880": {"name": "黄金 ETF", "grid_5": 8.977, "grid_10": 8.504, "grid_15": 8.032, "amount": 5000},
    "159937": {"name": "黄金 9999", "grid_5": 8.951, "grid_10": 8.480, "grid_15": 8.009, "amount": 5000},
    "512010": {"name": "医药 ETF", "grid_5": 0.334, "grid_10": 0.317, "grid_15": 0.299, "amount": 5000},
    "510500": {"name": "500ETF", "grid_5": 7.302, "grid_10": 6.917, "grid_15": 6.533, "amount": 5000},
    "510300": {"name": "300ETF", "grid_5": 4.256, "grid_10": 4.032, "grid_15": 3.808, "amount": 5000},
    "159770": {"name": "机器人 AI", "grid_5": 0.907, "grid_10": 0.860, "grid_15": 0.812, "amount": 5000},
    "159399": {"name": "现金流 ETF", "grid_5": 1.059, "grid_10": 1.004, "grid_15": 0.948, "amount": 5000},
    "159206": {"name": "卫星 ETF", "grid_5": 1.512, "grid_10": 1.433, "grid_15": 1.353, "amount": 5000},
    "159566": {"name": "储能电池", "grid_5": 2.132, "grid_10": 2.020, "grid_15": 1.907, "amount": 5000},
    "513110": {"name": "纳指 ETF", "grid_5": 1.848, "grid_10": 1.751, "grid_15": 1.653, "amount": 5000},
    "510880": {"name": "红利 ETF", "grid_5": 3.102, "grid_10": 2.939, "grid_15": 2.775, "amount": 5000},
    "513500": {"name": "标普 500ETF", "grid_5": 2.109, "grid_10": 1.998, "grid_15": 1.887, "amount": 5000},
}

# 止盈监控
TAKE_PROFIT_MONITOR = {
    "160723": {"name": "嘉实原油", "tp_20": 1.301, "tp_40": 1.518},
    "159663": {"name": "机床", "tp_20": 2.118, "tp_40": 2.471},
    "159566": {"name": "储能电池", "tp_20": 2.579, "tp_40": 3.009},
    "159206": {"name": "卫星 ETF", "tp_20": 2.051, "tp_40": 2.393},
}

# 止损监控
STOP_LOSS_MONITOR = {
    "159937": {"name": "黄金 9999", "sl_10": 9.604, "sl_15": 9.070},
    "512480": {"name": "半导体", "sl_10": 1.415, "sl_15": 1.336},
    "513500": {"name": "标普 500", "sl_10": 2.055, "sl_15": 1.941},
    "510300": {"name": "300ETF", "sl_10": 4.133, "sl_15": 3.903},
    "510500": {"name": "500ETF", "sl_10": 7.115, "sl_15": 6.719},
    "159363": {"name": "创业板 AI", "sl_10": 0.970, "sl_15": 0.916},
}

# 持仓数据
HOLDINGS = {
    "159937": {"name": "黄金 9999", "cost": 10.671, "weight": 9.46},
    "512480": {"name": "半导体", "cost": 1.572, "weight": 2.83},
    "513500": {"name": "标普 500", "cost": 2.283, "weight": 6.02},
    "510300": {"name": "300ETF", "cost": 4.592, "weight": 7.94},
    "510500": {"name": "500ETF", "cost": 7.905, "weight": 4.09},
    "159363": {"name": "创业板 AI", "cost": 1.078, "weight": 6.29},
    "160723": {"name": "嘉实原油", "cost": 1.084, "weight": 3.86},
    "159663": {"name": "机床", "cost": 1.765, "weight": 3.20},
    "159566": {"name": "储能电池", "cost": 2.149, "weight": 8.22},
    "159206": {"name": "卫星 ETF", "cost": 1.709, "weight": 4.05},
}

# 行业前景评估
INDUSTRY_OUTLOOK = {
    "159937": {"sector": "黄金", "outlook": 4, "logic": "美联储降息 + 地缘避险支撑，但估值偏高"},
    "512480": {"sector": "半导体", "outlook": 4, "logic": "AI 算力需求 + 国产替代，长期逻辑好"},
    "513500": {"sector": "美股宽基", "outlook": 3, "logic": "美股估值偏高 + 衰退预期，但长期向好"},
    "510300": {"sector": "A 股宽基", "outlook": 5, "logic": "估值历史低位 + 经济复苏，配置价值高"},
    "510500": {"sector": "A 股宽基", "outlook": 5, "logic": "中小盘代表 + 估值低，长期必涨"},
    "159363": {"sector": "AI 科技", "outlook": 4, "logic": "AI 长期趋势好，但短期估值偏高"},
    "160723": {"sector": "原油", "outlook": 3, "logic": "地缘支撑但波动大，已大幅盈利"},
    "159663": {"sector": "高端制造", "outlook": 4, "logic": "工业母机政策支持，趋势良好"},
    "159566": {"sector": "新能源", "outlook": 4, "logic": "储能需求爆发 + 碳中和长期趋势"},
    "159206": {"sector": "航天卫星", "outlook": 4, "logic": "低轨卫星组网加速，但估值偏高"},
}

TRIGGER_RECORD_FILE = "/home/admin/openclaw/workspace/trigger_records.json"

# 飞书 App Bot 配置
FEISHU_APP_ID = "cli_a9493d702278dbb7"
FEISHU_APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
FEISHU_USER_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"  # 老板的飞书 open_id
FEISHU_RECEIVE_ID_TYPE = "open_id"  # user_id | open_id | union_id | email | phone
API_BASE = "https://open.feishu.cn/open-apis"

# Token 缓存
_feishu_token_cache = {"token": None, "expires_at": 0}

def get_feishu_token():
    """获取飞书 tenant_access_token"""
    import time
    if _feishu_token_cache["token"] and time.time() < _feishu_token_cache["expires_at"]:
        return _feishu_token_cache["token"]
    
    import requests
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        token = data.get("tenant_access_token")
        _feishu_token_cache["token"] = token
        _feishu_token_cache["expires_at"] = time.time() + 7200
        return token
    return None

def get_feishu_user_info_by_phone(phone):
    """通过手机号获取用户 ID"""
    import requests
    token = get_feishu_token()
    if not token:
        return None
    resp = requests.get(
        f"{API_BASE}/contact/v3/users?user_id_type=open_id",
        headers={"Authorization": f"Bearer {token}"},
        params={"mobile": phone},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0 and data.get("data"):
        return data["data"]["user"]
    return None

def get_feishu_user_id():
    """获取老板的飞书 user_id"""
    if FEISHU_USER_ID:
        return FEISHU_USER_ID
    # 如果没有配置，尝试通过手机号获取（需要老板提供）
    return None

def send_feishu_card(title, content, template="blue"):
    """发送飞书交互式卡片消息（私聊）"""
    import requests
    import json
    
    token = get_feishu_token()
    if not token:
        print("❌ 飞书 token 获取失败")
        return False
    
    receive_id = FEISHU_USER_ID
    receive_id_type = FEISHU_RECEIVE_ID_TYPE
    
    if not receive_id:
        print("❌ 飞书用户 ID 未配置，无法发送私聊")
        return False
    
    card = {
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": template
        },
        "elements": [
            {"tag": "markdown", "content": content},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": f"触发时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}]}
        ]
    }
    
    resp = requests.post(
        f"{API_BASE}/im/v1/messages?receive_id_type={receive_id_type}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card)
        },
        timeout=10
    )
    result = resp.json()
    if result.get("code") == 0:
        print(f"✅ 飞书通知已发送：{title}")
        return True
    else:
        print(f"❌ 飞书通知失败：{result}")
        return False

def load_trigger_records():
    if os.path.exists(TRIGGER_RECORD_FILE):
        with open(TRIGGER_RECORD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"grid": {}, "take_profit": {}, "stop_loss": {}}

def save_trigger_records(records):
    with open(TRIGGER_RECORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def get_etf_prices():
    """获取 ETF 实时价格（使用优化后的双数据源模块）"""
    from data_fetcher import get_etf_prices as fetch_prices
    return fetch_prices(use_cache=True)



def analyze_trigger(code, trigger_type, level, price, trigger_price):
    """分析触发后是否应该执行操作（增强版：集成 QuantaAlpha 评估器）"""
    try:
        # 尝试使用 QuantaAlpha 智能评估器
        from quantaalpha_evaluator import analyze_trigger_smart
        
        holdings = HOLDINGS.get(code, {})
        outlook = INDUSTRY_OUTLOOK.get(code, {})
        
        name = holdings.get('name', '未知')
        cost = holdings.get('cost', 0)
        weight = holdings.get('weight', 0)
        sector = outlook.get('sector', '未知')
        
        if cost > 0:
            profit_pct = ((price - cost) / cost) * 100
        else:
            profit_pct = 0
        
        # 调用 QuantaAlpha 智能评估
        result = analyze_trigger_smart(
            code=code,
            name=name,
            trigger_type=trigger_type,
            sector=sector,
            weight=weight,
            profit_pct=profit_pct,
            trigger_price=trigger_price,
            current_price=price
        )
        
        recommendation = result['recommendation']['recommendation']
        confidence = result['recommendation']['confidence_level']
        reasons = result['recommendation']['reasons']
        industry_score = result['industry']['score']
        
        print(f"  📊 [QuantaAlpha] 行业评分：{industry_score}/5, 建议：{recommendation}")
        
    except Exception as e:
        # 降级到旧版逻辑
        print(f"  ⚠️  QuantaAlpha 评估失败，使用旧版逻辑：{e}")
        result = analyze_trigger_legacy(code, trigger_type, level, price, trigger_price)
        recommendation = result['recommendation']
        confidence = result['confidence']
        reasons = result['reasons']
        industry_score = result['industry_score']
        weight = result['weight']
        profit_pct = result['profit_pct']
    
    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasons": reasons,
        "industry_score": industry_score,
        "weight": weight,
        "profit_pct": profit_pct
    }

def analyze_trigger_legacy(code, trigger_type, level, price, trigger_price):
    """分析触发后是否应该执行操作（旧版逻辑，作为降级备份）"""
    holdings = HOLDINGS.get(code, {})
    outlook = INDUSTRY_OUTLOOK.get(code, {})
    
    name = holdings.get('name', '未知')
    cost = holdings.get('cost', 0)
    weight = holdings.get('weight', 0)
    sector = outlook.get('sector', '未知')
    industry_score = outlook.get('outlook', 3)
    industry_logic = outlook.get('logic', '')
    
    if cost > 0:
        profit_pct = ((price - cost) / cost) * 100
    else:
        profit_pct = 0
    
    recommendation = ""
    confidence = ""
    reasons = []
    
    if trigger_type == "stop_loss":
        level_pct = int(level.replace('sl_', ''))
        if industry_score >= 4:
            recommendation = "⚠️ 暂缓执行"
            confidence = "中等"
            reasons.append(f"✅ {sector}行业前景良好（评分{industry_score}/5）")
            reasons.append(f"✅ {industry_logic}")
            reasons.append(f"⚠️ 当前亏损{profit_pct:.1f}%，建议观察 3-5 个交易日")
            reasons.append(f"💡 如继续下跌{level_pct-5}%再考虑止损")
        elif industry_score == 3:
            recommendation = "🟡 部分执行"
            confidence = "中等"
            reasons.append(f"🟡 {sector}行业前景中性（评分{industry_score}/5）")
            reasons.append(f"🟡 仓位{weight}%，建议减仓 50% 控制风险")
            reasons.append(f"💡 剩余仓位设置更严格止损")
        else:
            recommendation = "✅ 建议执行"
            confidence = "高"
            reasons.append(f"❌ {sector}行业前景不明（评分{industry_score}/5）")
            reasons.append(f"❌ 亏损已达{profit_pct:.1f}%，及时止损保住本金")
    
    elif trigger_type == "take_profit":
        level_pct = int(level.replace('tp_', ''))
        if industry_score >= 4 and profit_pct < 50:
            recommendation = "⚠️ 暂缓执行"
            confidence = "中等"
            reasons.append(f"✅ {sector}行业前景良好，可继续持有")
            reasons.append(f"✅ 当前盈利{profit_pct:.1f}%，还有上涨空间")
            reasons.append(f"💡 建议设置移动止盈（回撤 10% 再止盈）")
        elif weight > 8:
            recommendation = "🟡 部分执行"
            confidence = "高"
            reasons.append(f"⚠️ 仓位{weight}%过重，建议减仓 50% 锁定利润")
            reasons.append(f"✅ 剩余仓位继续享受上涨")
            reasons.append(f"💡 减仓后仓位降至{weight/2:.1f}%")
        else:
            recommendation = "✅ 建议执行"
            confidence = "高"
            reasons.append(f"✅ 盈利{profit_pct:.1f}%已达到目标")
            reasons.append(f"✅ 锁定利润，落袋为安")
            reasons.append(f"💡 回笼资金等待其他机会")
    
    elif trigger_type == "grid":
        level_pct = int(level.replace('grid_', ''))
        if industry_score >= 4 and weight < 10:
            recommendation = "✅ 建议执行"
            confidence = "高"
            reasons.append(f"✅ {sector}行业前景良好（评分{industry_score}/5）")
            reasons.append(f"✅ 当前仓位{weight}%，加仓后风险可控")
            reasons.append(f"✅ 下跌{level_pct}%是加仓机会")
            reasons.append(f"💡 建议加仓 5000 元")
        elif industry_score == 3:
            recommendation = "🟡 谨慎执行"
            confidence = "中等"
            reasons.append(f"🟡 {sector}行业前景中性")
            reasons.append(f"⚠️ 建议只加仓 50%（2500 元）")
            reasons.append(f"💡 保留资金等待更好机会")
        else:
            recommendation = "❌ 不建议执行"
            confidence = "高"
            reasons.append(f"❌ {sector}行业前景不明（评分{industry_score}/5）")
            reasons.append(f"❌ 可能继续下跌，避免接飞刀")
            reasons.append(f"💡 等待行业逻辑明确后再加仓")
    
    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasons": reasons,
        "industry_score": industry_score,
        "weight": weight,
        "profit_pct": profit_pct
    }

def check_triggers():
    """检查所有触发条件"""
    prices = get_etf_prices()
    if not prices:
        print("❌ 未获取到价格数据")
        return
    
    records = load_trigger_records()
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    print(f"\n{'='*50}")
    print(f"检查时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # 检查网格加仓
    for code, config in GRID_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config['name']
        
        for level in ['grid_5', 'grid_10', 'grid_15']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('grid', {}):
                continue
            
            trigger_price = config[level]
            if price <= trigger_price:
                level_pct = level.replace('grid_', '')
                analysis = analyze_trigger(code, "grid", level, price, trigger_price)
                
                template_color = "green" if "✅ 建议执行" in analysis['recommendation'] else "blue" if "🟡" in analysis['recommendation'] else "red"
                
                title = f"🔔 网格加仓触发 | {name}({code})"
                content = f"""**{name}**({code}) 触发网格加仓！

📊 触发条件
- 下跌幅度：**- {level_pct}%**
- 当前价格：**{price}** 元
- 触发价格：**{trigger_price}** 元
- 建议加仓：**5000** 元

🧠 智能分析
- 行业前景：{analysis['industry_score']}/5 分
- 当前仓位：{analysis['weight']}%
- 分析结果：**{analysis['recommendation']}**
- 置信度：{analysis['confidence']}

📋 分析理由
""" + "\n".join([f"- {r}" for r in analysis['reasons']]) + f"""

⚠️ 以上建议仅供参考，最终决策请老板确认"""
                
                send_feishu_card(title, content, template_color)
                records.setdefault('grid', {})[trigger_key] = True
                print(f"🔔 网格加仓触发：{name} -{level_pct}% | 建议：{analysis['recommendation']}")
    
    # 检查止盈
    for code, config in TAKE_PROFIT_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config['name']
        
        for level in ['tp_20', 'tp_40']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('take_profit', {}):
                continue
            
            trigger_price = config[level]
            if price >= trigger_price:
                level_pct = level.replace('tp_', '')
                analysis = analyze_trigger(code, "take_profit", level, price, trigger_price)
                
                title = f"🎯 止盈触发 | {name}({code})"
                content = f"""**{name}**({code}) 触发止盈！

📊 触发条件
- 上涨幅度：**+{level_pct}%**
- 当前价格：**{price}** 元
- 触发价格：**{trigger_price}** 元

🧠 智能分析
- 行业前景：{analysis['industry_score']}/5 分
- 当前仓位：{analysis['weight']}%
- 当前盈利：{analysis['profit_pct']:.1f}%
- 分析结果：**{analysis['recommendation']}**
- 置信度：{analysis['confidence']}

📋 分析理由
""" + "\n".join([f"- {r}" for r in analysis['reasons']]) + f"""

⚠️ 以上建议仅供参考，最终决策请老板确认"""
                
                send_feishu_card(title, content, "green")
                records.setdefault('take_profit', {})[trigger_key] = True
                print(f"🎯 止盈触发：{name} +{level_pct}% | 建议：{analysis['recommendation']}")
    
    # 检查止损
    for code, config in STOP_LOSS_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config['name']
        
        for level in ['sl_10', 'sl_15']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('stop_loss', {}):
                continue
            
            trigger_price = config[level]
            if price <= trigger_price:
                level_pct = level.replace('sl_', '')
                analysis = analyze_trigger(code, "stop_loss", level, price, trigger_price)
                
                title = f"⛔ 止损触发 | {name}({code})"
                content = f"""**{name}**({code}) 触发止损！

📊 触发条件
- 下跌幅度：**- {level_pct}%**
- 当前价格：**{price}** 元
- 触发价格：**{trigger_price}** 元
- 当前亏损：{analysis['profit_pct']:.1f}%

🧠 智能分析
- 行业前景：{analysis['industry_score']}/5 分
- 当前仓位：{analysis['weight']}%
- 分析结果：**{analysis['recommendation']}**
- 置信度：{analysis['confidence']}

📋 分析理由
""" + "\n".join([f"- {r}" for r in analysis['reasons']]) + f"""

⚠️ 以上建议仅供参考，最终决策请老板确认"""
                
                send_feishu_card(title, content, "red")
                records.setdefault('stop_loss', {})[trigger_key] = True
                print(f"⛔ 止损触发：{name} -{level_pct}% | 建议：{analysis['recommendation']}")
    
    save_trigger_records(records)
    print(f"\n✅ 检查完成，共检查{len(prices)}只 ETF")

if __name__ == "__main__":
    check_triggers()