#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特朗普因子监控 v2.0 - Tavily API 版
实时搜索特朗普新闻和动态，分析金融市场影响
"""

import sys, json, requests, os
from datetime import datetime, timedelta

sys.path.insert(0, '/home/admin/openclaw/workspace')

# Tavily API 配置
TAVILY_API_KEY = "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"
TAVILY_URL = "https://api.tavily.com/search"

# 影响评估规则
IMPACT_RULES = {
    '关税/贸易': {
        'keywords': ['tariff', '关税', 'trade', '贸易', 'China', '中国', 'import', 'export'],
        'impact': '📉 风险资产',
        'sectors': ['出口', '科技', '制造业'],
        'hedge': '📈 黄金/美元',
        'severity': '🟡 中等'
    },
    '美联储/利率': {
        'keywords': ['Fed', '美联储', 'interest rate', '利率', 'inflation', '通胀'],
        'impact': '📉 美元',
        'sectors': ['银行', '房地产'],
        'hedge': '📈 黄金/债券',
        'severity': '🟡 中等'
    },
    '地缘政治': {
        'keywords': ['war', '战争', 'conflict', '冲突', 'sanction', '制裁', 'Russia', '俄罗斯'],
        'impact': '📉 风险资产',
        'sectors': ['能源', '国防'],
        'hedge': '📈 黄金/日元',
        'severity': '🔴 严重'
    },
    '科技政策': {
        'keywords': ['tech', '科技', 'AI', 'semiconductor', '半导体', 'chip', '芯片'],
        'impact': '📈/📉 科技股',
        'sectors': ['科技', '半导体'],
        'hedge': '观望',
        'severity': '🟡 中等'
    },
    '能源政策': {
        'keywords': ['oil', '原油', 'energy', '能源', 'drilling', '开采', 'gas'],
        'impact': '📈/📉 油价',
        'sectors': ['能源', '航空'],
        'hedge': '观望',
        'severity': '🟢 轻微'
    }
}

def search_trump_news(query="Trump", max_results=5):
    """
    使用 Tavily 搜索特朗普新闻
    """
    print(f"\n🔍 搜索特朗普新闻：{query}...")
    
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": max_results
    }
    
    try:
        resp = requests.post(TAVILY_URL, json=payload, timeout=10)
        result = resp.json()
        
        if result.get("results"):
            print(f"✅ 获取到 {len(result['results'])} 条新闻")
            return result['results']
        else:
            print(f"⚠️ 未找到相关新闻")
            return []
            
    except Exception as e:
        print(f"❌ 搜索失败：{e}")
        return []

def analyze_news(news_item):
    """
    分析单条新闻的影响
    """
    title = news_item.get('title', '').lower()
    content = news_item.get('content', '').lower()
    text = title + ' ' + content
    
    # 识别内容类型
    content_type = None
    for ctype, rules in IMPACT_RULES.items():
        if any(kw.lower() in text for kw in rules['keywords']):
            content_type = ctype
            break
    
    if not content_type:
        return None
    
    rule = IMPACT_RULES[content_type]
    
    # 判断严重程度
    severity = rule['severity']
    if any(kw in text for kw in ['immediately', '立即', 'emergency', '紧急', 'breaking', '突发']):
        severity = '🔴 严重'
    elif any(kw in text for kw in ['consider', '考虑', 'maybe', '可能', 'plan', '计划']):
        severity = '🟡 中等'
    else:
        severity = '🟢 轻微'
    
    return {
        'content_type': content_type,
        'severity': severity,
        'market_impact': rule['impact'],
        'sectors': rule['sectors'],
        'hedge': rule['hedge'],
        'confidence': '中'
    }

def generate_alert(news, analysis):
    """
    生成特朗普因子提醒
    """
    lines = ["🔔 特朗普因子提醒", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    lines.append("━━━ 新闻内容 ━━━")
    lines.append(f"标题：{news.get('title', 'N/A')}")
    lines.append(f"来源：{news.get('url', 'N/A')}")
    lines.append(f"时间：{news.get('published_date', '实时')}")
    lines.append("")
    
    lines.append("━━━ 影响分析 ━━━")
    lines.append(f"内容类型：{analysis['content_type']}")
    lines.append(f"严重程度：{analysis['severity']}")
    lines.append(f"市场影响：{analysis['market_impact']}")
    lines.append(f"影响板块：{', '.join(analysis['sectors'])}")
    lines.append(f"对冲建议：{analysis['hedge']}")
    lines.append(f"置信度：{analysis['confidence']}")
    lines.append("")
    
    lines.append("━━━ 操作建议 ━━━")
    if analysis['severity'] == '🔴 严重':
        lines.append("⚠️ 建议：立即关注，考虑减仓风险资产")
    elif analysis['severity'] == '🟡 中等':
        lines.append("👀 建议：密切关注，准备对冲")
    else:
        lines.append("📝 建议：保持关注，暂不操作")
    
    lines.append("")
    lines.append("⚠️ 注：此提醒独立于投资系统，仅供参考")
    
    return "\n".join(lines)

def monitor_trump_factor():
    """
    主监控函数
    监控频率：每 3 小时一次（24 小时覆盖）
    考虑美国时差（美国白天 = 中国深夜）
    """
    print("="*70)
    print("特朗普因子监控 v2.0 (Tavily API)")
    print("监控频率：每 3 小时一次（24 小时）")
    print("考虑时差：美国白天 = 中国深夜")
    print("="*70)
    
    # 搜索关键词（优化：减少查询数量）
    queries = [
        "Trump tariff China trade March 2026",
        "Trump Federal Reserve interest rate",
        "Trump Ukraine Russia war latest"
    ]
    
    all_alerts = []
    
    for query in queries:
        print(f"\n搜索：{query}")
        # 每次搜索 3 条结果，节省额度
        news_list = search_trump_news(query, max_results=3)
        
        for news in news_list:
            analysis = analyze_news(news)
            if analysis:
                alert = generate_alert(news, analysis)
                all_alerts.append(alert)
                print(f"\n🔔 发现重要内容：{news.get('title', 'N/A')[:50]}...")
    
    # 保存结果
    output = {
        'timestamp': datetime.now().isoformat(),
        'queries': queries,
        'alerts_count': len(all_alerts),
        'alerts': all_alerts
    }
    
    with open('/home/admin/openclaw/workspace/trump_factor_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 数据已保存至 trump_factor_data.json")
    print(f"✅ 共发现 {len(all_alerts)} 条重要内容")
    
    return all_alerts

if __name__ == "__main__":
    alerts = monitor_trump_factor()
    
    if alerts:
        print("\n" + "="*70)
        print("特朗普因子提醒（独立于投资系统）")
        print("="*70)
        for alert in alerts:
            print(alert)
            print("-"*70)
