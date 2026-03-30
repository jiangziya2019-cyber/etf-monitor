#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融合系统实盘监控 + 飞书推送（带 ETF 名称）
"""

import sys, json, requests
from datetime import datetime

sys.path.insert(0, '/home/admin/openclaw/workspace')

# 飞书配置
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
BOSS_OPEN_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"

# ETF 代码 - 名称映射
ETF_NAMES = {
    "510300": "沪深 300ETF", "510500": "中证 500ETF", "512480": "半导体 ETF",
    "510880": "红利 ETF", "513110": "纳指 100ETF", "513500": "标普 500ETF",
    "512010": "医药 ETF", "515790": "光伏 ETF", "512200": "房地产 ETF",
    "515030": "消费 ETF", "518880": "黄金 9999", "159915": "创业板 ETF",
    "159663": "储能电池 ETF", "159937": "黄金 9999", "160723": "嘉实原油"
}

def get_token():
    r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    return r.json().get("tenant_access_token") if r.json().get("code") == 0 else None

def send_feishu(text):
    token = get_token()
    if not token: return False
    r = requests.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id", headers={"Authorization": f"Bearer {token}"}, json={"receive_id": BOSS_OPEN_ID, "msg_type": "text", "content": json.dumps({"text": text})}, timeout=10)
    return r.json().get("code") == 0

def generate_fusion_report():
    """生成融合系统报告（带 ETF 名称）"""
    # 读取筛选结果
    with open('/home/admin/openclaw/workspace/fusion_result.json', 'r') as f:
        data = json.load(f)
    
    macro = data.get("macro", {})
    results = data.get("results", {})
    
    # 排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]["composite"], reverse=True)
    
    report = ["📊 融合筛选报告（带名称）", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    # 宏观环境
    report.append("━━━ 宏观环境 ━━━")
    report.append(f"美林时钟：{macro.get('meilin_cycle', 'Unknown')}")
    report.append(f"CPI: {macro.get('cpi', 0):.1f}%")
    report.append(f"PMI: {macro.get('pmi', 0):.1f}")
    report.append(f"美债利差：{macro.get('treasury_spread', 0):.2f}%")
    report.append("")
    
    # 筛选结果（带名称）
    report.append("━━━ 推荐 TOP5 ━━━")
    for i, (code, scores) in enumerate(sorted_results[:5], 1):
        name = ETF_NAMES.get(code, code)
        report.append(f"{i}. {code} {name:12} 综合{scores['composite']:.2f}")
    
    report.append("")
    report.append("━━━ 因子得分 ━━━")
    for i, (code, scores) in enumerate(sorted_results[:5], 1):
        name = ETF_NAMES.get(code, code)
        report.append(f"{i}. {code} {name:12} 行业{scores['sector_factor']:.2f} 波动{scores['volatility_factor']:.2f} 动量{scores['momentum_factor']:.2f} 估值{scores['value_factor']:.2f} 宏观{scores['macro_factor']:.2f}")
    
    report.append("")
    report.append("━━━ 配置建议 ━━━")
    if macro.get('meilin_cycle') == '复苏期':
        report.append("宏观环境友好，建议积极配置")
    elif macro.get('meilin_cycle') == '过渡期':
        report.append("宏观环境中性，建议均衡配置")
    else:
        report.append("宏观环境偏空，建议防御为主")
    
    report.append("")
    report.append("⚠️ 投资有风险，决策需谨慎")
    
    return "\n".join(report)

if __name__ == "__main__":
    print("生成融合系统报告（带 ETF 名称）...")
    report = generate_fusion_report()
    print(report)
    
    print("\n发送飞书...")
    if send_feishu(report):
        print("✅ 报告已发送至飞书（带名称）")
    else:
        print("❌ 发送失败")
