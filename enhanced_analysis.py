#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强分析报告 - 整合行业轮动、市场情绪、回测验证
"""

import json
import requests
from datetime import datetime
import subprocess
import sys

# 飞书配置
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
BOSS_OPEN_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"
API_BASE = "https://open.feishu.cn/open-apis"

def get_tenant_access_token():
    """获取 tenant_access_token"""
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("tenant_access_token")
    return None

def send_text_message(text):
    """发送文本消息"""
    token = get_tenant_access_token()
    if not token:
        return False
    
    url = f"{API_BASE}/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "receive_id": BOSS_OPEN_ID,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    result = response.json()
    
    return result.get("code") == 0

def run_module(module_name, module_file):
    """运行模块并捕获输出"""
    try:
        result = subprocess.run(
            [sys.executable, module_file],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/admin/openclaw/workspace"
        )
        return result.stdout
    except Exception as e:
        return f"❌ {module_name} 执行失败：{e}"

def generate_summary_report():
    """生成综合摘要报告"""
    lines = []
    lines.append("📊 增强分析报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("━━━ 新增功能 ━━━")
    lines.append("✅ 行业轮动分析 - 监测板块资金流向和轮动信号")
    lines.append("✅ 市场情绪指标 - 恐慌指数/成交量/北向资金")
    lines.append("✅ 回测框架优化 - 调仓策略回测 + 性能评估")
    lines.append("")
    lines.append("━━━ 模块文件 ━━━")
    lines.append("• sector_rotation.py - 行业轮动分析")
    lines.append("• market_sentiment.py - 市场情绪指标")
    lines.append("• backtest_framework.py - 回测框架")
    lines.append("")
    lines.append("━━━ 使用说明 ━━━")
    lines.append("1. 行业轮动：python3 sector_rotation.py")
    lines.append("2. 市场情绪：python3 market_sentiment.py")
    lines.append("3. 回测验证：python3 backtest_framework.py")
    lines.append("")
    lines.append("⚠️ 提示：详细报告见各模块输出或缓存文件")
    
    return "\n".join(lines)

def main():
    """主函数"""
    print("=" * 60)
    print("增强分析报告 - 执行中")
    print("=" * 60)
    
    # 运行三个模块
    print("\n1. 运行行业轮动分析...")
    sector_output = run_module("行业轮动", "sector_rotation.py")
    
    print("2. 运行市场情绪指标...")
    sentiment_output = run_module("市场情绪", "market_sentiment.py")
    
    print("3. 运行回测框架...")
    backtest_output = run_module("回测框架", "backtest_framework.py")
    
    # 生成摘要报告
    summary = generate_summary_report()
    
    print("\n" + summary)
    
    # 发送飞书消息
    print("\n发送飞书通知...")
    success = send_text_message(summary)
    
    if success:
        print("✅ 报告已发送至飞书")
    else:
        print("❌ 发送失败")
    
    # 保存完整报告
    full_report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "sector_output": sector_output,
        "sentiment_output": sentiment_output,
        "backtest_output": backtest_output
    }
    
    with open("/home/admin/openclaw/workspace/enhanced_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 增强分析报告完成")
    
    return full_report

if __name__ == "__main__":
    main()
