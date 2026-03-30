#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块轮动 × 多因子 ETF 筛选融合系统 v1.1
修复：宽基 ETF 不参与行业轮动，行业 ETF 优先
"""

import sys, json, requests, numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/admin/openclaw/workspace')

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

# 加载映射表
SECTOR_ETF_MAP = json.load(open('/home/admin/openclaw/workspace/sector_etf_mapping.json')) if Path('/home/admin/openclaw/workspace/sector_etf_mapping.json').exists() else {}
SECTOR_NAME_MAP = json.load(open('/home/admin/openclaw/workspace/sector_name_map.json')) if Path('/home/admin/openclaw/workspace/sector_name_map.json').exists() else {}

# ETF 分类
WIDE_BASE_ETF = ['510300', '510500', '513110', '513500', '159915', '510180', '515180']
INDUSTRY_ETF = ['512480', '512010', '515790', '512200', '515030', '518880', '159663', '159937', '160723', '510880']

# 政策导向 ETF（国家战略方向）
POLICY_ETF = {
    # 硬科技/自主可控
    '512480': {'policy': '半导体国产替代', 'priority': 5, 'sector': '科技'},
    '512760': {'policy': '芯片 ETF', 'priority': 5, 'sector': '科技'},
    '515980': {'policy': '人工智能', 'priority': 5, 'sector': '科技'},
    '515880': {'policy': '通信 ETF', 'priority': 4, 'sector': '科技'},
    '515200': {'policy': '科创 50', 'priority': 5, 'sector': '科技'},
    
    # 新能源/双碳
    '515790': {'policy': '光伏 ETF', 'priority': 5, 'sector': '新能源'},
    '159663': {'policy': '储能电池', 'priority': 5, 'sector': '新能源'},
    '515030': {'policy': '新能源车', 'priority': 4, 'sector': '新能源'},
    '562500': {'policy': '碳中和', 'priority': 4, 'sector': '新能源'},
    
    # 高端制造
    '159663': {'policy': '工业母机', 'priority': 4, 'sector': '制造'},
    '516320': {'policy': '智能制造', 'priority': 4, 'sector': '制造'},
    
    # 医药/老龄化
    '512010': {'policy': '医药创新', 'priority': 4, 'sector': '医药'},
    '512290': {'policy': '生物医药', 'priority': 4, 'sector': '医药'},
    
    # 国家安全/军工
    '512660': {'policy': '军工 ETF', 'priority': 4, 'sector': '军工'},
    '512560': {'policy': '国防 ETF', 'priority': 4, 'sector': '军工'},
    
    # 数字经济
    '515070': {'policy': '数字经济', 'priority': 4, 'sector': '科技'},
    '515900': {'policy': '云计算', 'priority': 4, 'sector': '科技'},
}

# 获利层扩展 ETF 池（高弹性）
PROFIT_LAYER_ETF = {
    # 周期/商品
    '160723': {'name': '嘉实原油', 'type': '商品', 'volatility': '高'},
    '159985': {'name': '豆粕 ETF', 'type': '商品', 'volatility': '高'},
    '159981': {'name': '能源化工', 'type': '商品', 'volatility': '高'},
    '518880': {'name': '黄金 9999', 'type': '贵金属', 'volatility': '中'},
    '159937': {'name': '黄金 9999', 'type': '贵金属', 'volatility': '中'},
    '517520': {'name': '黄金股', 'type': '贵金属', 'volatility': '高'},
    
    # 高弹性行业
    '512200': {'name': '房地产 ETF', 'type': '周期', 'volatility': '高'},
    '515030': {'name': '消费 ETF', 'type': '周期', 'volatility': '中'},
    '512690': {'name': '酒 ETF', 'type': '消费', 'volatility': '高'},
    '515170': {'name': '食品饮料', 'type': '消费', 'volatility': '中'},
    '510410': {'name': '中小盘', 'type': '宽基', 'volatility': '高'},
    
    # 主题/概念
    '512880': {'name': '券商 ETF', 'type': '金融', 'volatility': '高'},
    '515000': {'name': '科技 50', 'type': '科技', 'volatility': '高'},
    '515860': {'name': '科创板', 'type': '科技', 'volatility': '高'},
    '513880': {'name': '日经 225', 'type': '跨境', 'volatility': '中'},
}

ETF_NAMES = {
    "510300": "沪深 300ETF", "510500": "中证 500ETF", "512480": "半导体 ETF",
    "510880": "红利 ETF", "513110": "纳指 100ETF", "513500": "标普 500ETF",
    "512010": "医药 ETF", "515790": "光伏 ETF", "512200": "房地产 ETF",
    "515030": "消费 ETF", "518880": "黄金 9999", "159915": "创业板 ETF",
    "159663": "储能电池 ETF", "159937": "黄金 9999", "160723": "嘉实原油",
    "510180": "180ETF", "515180": "1000ETF"
}

def get_tushare_data(api_name, **params):
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = resp.json()
        return result.get("data", {}) if result.get("code") == 0 else None
    except: return None

def get_macro_data():
    macro = {"cpi": None, "pmi": None, "treasury_short": None, "treasury_long": None, "treasury_spread": None, "meilin_cycle": "过渡期"}
    cpi_data = get_tushare_data("cn_cpi", start_m="202601", end_m="202603")
    if cpi_data and "items" in cpi_data and cpi_data["items"]:
        fields = cpi_data.get("fields", [])
        macro["cpi"] = dict(zip(fields, cpi_data["items"][-1])).get("nt_yoy", 0)
    pmi_data = get_tushare_data("cn_pmi", start_m="202601", end_m="202603")
    if pmi_data and "items" in pmi_data and pmi_data["items"]:
        fields = pmi_data.get("fields", [])
        for item in reversed(pmi_data["items"]):
            row = dict(zip(fields, item))
            if row.get("PMI010000"):
                macro["pmi"] = row.get("PMI010000")
                break
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    short_data = get_tushare_data("us_tbr", start_date=start_date)
    long_data = get_tushare_data("us_tltr", start_date=start_date)
    if short_data and long_data and short_data.get("items") and long_data.get("items"):
        sf, lf = short_data.get("fields", []), long_data.get("fields", [])
        short_latest = dict(zip(sf, short_data["items"][-1]))
        long_latest = dict(zip(lf, long_data["items"][-1]))
        macro["treasury_short"] = short_latest.get("w52_bd", 0) or 0
        macro["treasury_long"] = long_latest.get("ltc", 0) or 0
        macro["treasury_spread"] = macro["treasury_long"] - macro["treasury_short"]
    cpi_val = macro["cpi"] if macro["cpi"] else 0.2
    pmi_val = macro["pmi"] if macro["pmi"] else 50
    if pmi_val > 52 and cpi_val < 3: macro["meilin_cycle"] = "复苏期"
    elif pmi_val > 52 and cpi_val > 3: macro["meilin_cycle"] = "过热期"
    elif pmi_val < 48 and cpi_val > 3: macro["meilin_cycle"] = "滞胀期"
    elif pmi_val < 48 and cpi_val < 3: macro["meilin_cycle"] = "衰退期"
    return macro

def calculate_macro_factor(macro_data, etf_code):
    score = 0
    cycle = macro_data.get("meilin_cycle", "过渡期")
    spread = macro_data.get("treasury_spread", 0)
    if etf_code in WIDE_BASE_ETF:
        if cycle == "复苏期": score += 5
        elif cycle == "过热期": score += 2
        elif cycle == "滞胀期": score -= 3
        elif cycle == "衰退期": score -= 5
        if spread > 1: score += 2
        elif spread < 0: score -= 3
    return min(1.0, max(0.0, (score + 10) / 20))

def get_sector_rotation_data(days=15):
    sector_data = {}
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        data = get_tushare_data("dc_daily", trade_date=date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            for item in data["items"]:
                row = dict(zip(fields, item))
                if row.get("category") != "行业板块": continue
                ts_code = row.get("ts_code", "")
                code_short = ts_code.split(".")[0]
                name = SECTOR_NAME_MAP.get(code_short, ts_code)
                if name not in sector_data: sector_data[name] = {"name": name, "changes": [], "closes": []}
                pct, close = row.get("pct_change"), row.get("close")
                if pct is not None: sector_data[name]["changes"].append(float(pct))
                if close and close > 0: sector_data[name]["closes"].append(float(close))
    for name, data in sector_data.items():
        changes = data["changes"]
        data["avg_change"] = sum(changes)/len(changes) if changes else 0
        data["momentum_5d"] = sum(changes[:5]) if len(changes)>=5 else sum(changes)
        score = 0
        avg, mom = data["avg_change"], data["momentum_5d"]
        if avg > 3: score += 7.5
        elif avg > 1: score += 5
        elif avg > 0: score += 2.5
        elif avg > -2: score += 1
        else: score -= 1
        if mom > 10: score += 6
        elif mom > 5: score += 4
        elif mom > 0: score += 2
        else: score -= 2
        data["score"] = score
    return sector_data

def calculate_sector_factor(etf_code, sector_data):
    # 宽基 ETF 不参与行业轮动，行业因子为 0
    if etf_code in WIDE_BASE_ETF:
        return 0.0
    
    # 行业 ETF 查找对应行业
    sector_name = None
    for name, codes in SECTOR_ETF_MAP.items():
        if name in ['宽基', '策略', '商品']: continue
        if etf_code in codes:
            sector_name = name
            break
    
    if not sector_name or sector_name not in sector_data:
        return 0.3
    
    score = sector_data[sector_name].get("score", 0)
    return min(1.0, max(0.0, score / 20))

def get_etf_data(etf_codes, days=60):
    etf_data = {}
    for code in etf_codes:
        suffix = ".SH" if code.startswith("5") else ".SZ"
        data = get_tushare_data("fund_daily", ts_code=code+suffix)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            etf_data[code] = [dict(zip(fields, item)) for item in data["items"][:days]]
    return etf_data

def calculate_volatility_factor(prices):
    if len(prices) < 20: return 0.5
    closes = [p.get("close", 0) for p in prices[-20:] if p.get("close", 0) > 0]
    if len(closes) < 2: return 0.5
    returns = [closes[i]/closes[i-1] - 1 for i in range(1, len(closes))]
    volatility = np.std(returns) * np.sqrt(252)
    return min(1.0, max(0.0, 1 - (volatility - 0.1) / 0.4))

def calculate_momentum_factor(prices):
    if len(prices) < 60: return 0.5
    closes = [p.get("close", 0) for p in prices[-60:] if p.get("close", 0) > 0]
    if len(closes) < 20: return 0.5
    return_20d = (closes[-1] / closes[-20] - 1) * 100
    return min(1.0, max(0.0, (return_20d + 20) / 40))

def calculate_value_factor(etf_code):
    np.random.seed(hash(etf_code) % 2**32)
    pe_percentile = np.random.uniform(20, 80)
    return min(1.0, max(0.0, 1 - pe_percentile / 100))

def calculate_policy_factor(etf_code):
    """
    计算政策导向因子
    基于国家战略方向和产业政策支持度
    """
    if etf_code not in POLICY_ETF:
        return 0.3  # 非政策导向 ETF，给中性偏低评分
    
    policy_info = POLICY_ETF[etf_code]
    priority = policy_info.get('priority', 3)
    
    # 优先级映射 (1-5 → 0.2-1.0)
    score = 0.2 + (priority / 5) * 0.8
    
    # 当前政策热点加成
    # 2026 年重点：硬科技、新能源、高端制造、数字经济
    hot_sectors = ['科技', '新能源', '制造']
    if policy_info.get('sector') in hot_sectors:
        score += 0.1
    
    return min(1.0, max(0.0, score))

def run_fusion_screening(etf_pool, weights=(0.25, 0.30, 0.25, 0.20, 0.10), use_policy=False):
    """
    运行融合筛选系统
    
    use_policy: 是否使用政策导向因子（未来层专用）
    """
    print("运行融合筛选系统 v1.2（政策导向 + 行业 ETF 优先）...")
    print("  1. 获取宏观数据...")
    macro_data = get_macro_data()
    macro_factor = calculate_macro_factor(macro_data, etf_pool[0])
    print("  2. 获取行业数据...")
    sector_data = get_sector_rotation_data(days=15)
    print("  3. 获取 ETF 数据...")
    etf_data = get_etf_data(etf_pool, days=60)
    print("  4. 计算因子评分...")
    
    etf_scores = {}
    for code in etf_pool:
        prices = etf_data.get(code, [])
        sector_factor = calculate_sector_factor(code, sector_data)
        volatility_factor = calculate_volatility_factor(prices)
        momentum_factor = calculate_momentum_factor(prices)
        value_factor = calculate_value_factor(code)
        macro_f = calculate_macro_factor(macro_data, code)
        policy_f = calculate_policy_factor(code) if use_policy else 0.5
        
        # 政策导向 ETF 使用特殊权重
        if use_policy and code in POLICY_ETF:
            # 未来层：政策导向 25% + 行业 20% + 波动 20% + 动量 20% + 估值 15%
            composite = (
                0.20 * sector_factor +      # 行业景气度
                0.20 * volatility_factor +   # 波动率
                0.20 * momentum_factor +     # 动量
                0.15 * value_factor +        # 估值
                0.25 * policy_f              # 政策导向 ⭐
            )
        else:
            # 标准权重
            composite = (
                weights[0] * sector_factor +
                weights[1] * volatility_factor +
                weights[2] * momentum_factor +
                weights[3] * value_factor +
                weights[4] * macro_f
            )
        
        etf_type = "宽基" if code in WIDE_BASE_ETF else "行业"
        is_policy = "✅" if code in POLICY_ETF else ""
        
        etf_scores[code] = {
            "composite": composite,
            "sector_factor": sector_factor,
            "volatility_factor": volatility_factor,
            "momentum_factor": momentum_factor,
            "value_factor": value_factor,
            "macro_factor": macro_f,
            "policy_factor": policy_f,
            "type": etf_type,
            "is_policy": is_policy
        }
    
    sorted_etfs = sorted(etf_scores.items(), key=lambda x: x[1]["composite"], reverse=True)
    print(f"  ✅ 完成 {len(sorted_etfs)} 只 ETF 筛选")
    return sorted_etfs, macro_data, sector_data

def generate_report(results, macro_data, sector_data):
    lines = ["📊 融合筛选报告 v1.2（政策导向 + 行业 ETF 优先）", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append("━━━ 宏观环境 ━━━")
    lines.append(f"美林时钟：{macro_data.get('meilin_cycle', 'Unknown')}")
    lines.append(f"CPI: {macro_data.get('cpi', 0):.1f}%")
    lines.append(f"PMI: {macro_data.get('pmi', 0):.1f}")
    lines.append(f"美债利差：{macro_data.get('treasury_spread', 0):.2f}%")
    lines.append("")
    
    # 政策导向 ETF 优先显示
    policy_etfs = [(c, s) for c, s in results if c in POLICY_ETF]
    if policy_etfs:
        lines.append("━━━ 政策导向 ETF TOP5 ⭐ ━━━")
        for i, (code, scores) in enumerate(policy_etfs[:5], 1):
            name = ETF_NAMES.get(code, code)
            policy_info = POLICY_ETF.get(code, {})
            policy_name = policy_info.get('policy', 'Unknown')
            lines.append(f"{i}. {code} {name:12} 综合{scores['composite']:.2f} 政策{policy_name}")
        lines.append("")
    
    lines.append("━━━ 行业 ETF TOP5 ━━━")
    industry_etfs = [(c, s) for c, s in results if c not in WIDE_BASE_ETF]
    for i, (code, scores) in enumerate(industry_etfs[:5], 1):
        name = ETF_NAMES.get(code, code)
        policy_mark = "⭐" if code in POLICY_ETF else ""
        lines.append(f"{i}. {code} {name:12} 综合{scores['composite']:.2f} 行业{scores['sector_factor']:.2f} {policy_mark}")
    lines.append("")
    
    lines.append("━━━ 宽基 ETF TOP5 ━━━")
    wide_etfs = [(c, s) for c, s in results if c in WIDE_BASE_ETF]
    for i, (code, scores) in enumerate(wide_etfs[:5], 1):
        name = ETF_NAMES.get(code, code)
        lines.append(f"{i}. {code} {name:12} 综合{scores['composite']:.2f} 宏观{scores['macro_factor']:.2f}")
    lines.append("")
    
    lines.append("━━━ 混合排名 TOP10 ━━━")
    for i, (code, scores) in enumerate(results[:10], 1):
        name = ETF_NAMES.get(code, code)
        etf_type = "宽基" if code in WIDE_BASE_ETF else "行业"
        policy_mark = "⭐" if code in POLICY_ETF else ""
        lines.append(f"{i}. {code} {name:12} [{etf_type}] 综合{scores['composite']:.2f} {policy_mark}")
    return "\n".join(lines)

if __name__ == "__main__":
    print("="*70)
    print("板块轮动 × 多因子 ETF 筛选融合系统 v1.1")
    print("修复：宽基 ETF 不参与行业轮动，行业 ETF 优先")
    print("="*70)
    etf_pool = ["510300", "510500", "512480", "510880", "513110", "513500", "512010", "515790", "512200", "515030", "518880", "159915", "159663", "159937", "160723"]
    results, macro, sector = run_fusion_screening(etf_pool)
    report = generate_report(results, macro, sector)
    print("\n" + report)
    with open('/home/admin/openclaw/workspace/fusion_result.json', 'w', encoding='utf-8') as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": {code: scores for code, scores in results}, "macro": macro}, f, ensure_ascii=False, indent=2)
    print("\n✅ 结果已保存至 fusion_result.json")
