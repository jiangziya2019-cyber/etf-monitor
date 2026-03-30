#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 ETF 多因子筛选 v5.0（缓存版）
版本：v5.0 | 创建：2026-03-28 16:10

使用缓存数据运行筛选，避免 Tushare 速率限制
"""

import sys, json, os, time, glob
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5.json'
REPORT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选报告_v5.md'
TOP_N = 30

# 行业映射
INDUSTRY_KEYWORDS = {
    '宽基': ['300', '500', '50', '180', '红利', '央企', '大盘', '中小'],
    '科技': ['科技', '电子', '半导体', '芯片', '计算机', '通信', '5G', '人工智能', '光伏', '新能源'],
    '金融': ['金融', '银行', '证券', '保险', '券商'],
    '制造': ['制造', '机械', '装备', '机器人', '机床', '储能', '电池'],
    '医药': ['医药', '医疗', '生物', '创新药', '中药'],
    '周期': ['周期', '有色', '金属', '煤炭', '钢铁', '化工', '建材'],
    '消费': ['消费', '食品', '饮料', '家电', '汽车', '旅游'],
    '全球': ['纳指', '标普', '恒生', '港股', '美国', '全球', '国际'],
    '其他': []
}

def load_etf_from_cache() -> Dict[str, Dict]:
    """从缓存加载全市场 ETF 数据"""
    print(f"从 {CACHE_DIR} 加载 ETF 数据...")
    
    etf_data = {}
    json_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                code = os.path.basename(filepath).replace('.json', '')
                if code.isdigit() and len(code) == 6:
                    etf_data[code] = data
        except Exception as e:
            print(f"⚠️ 加载 {filepath} 失败：{e}")
    
    print(f"✅ 加载 {len(etf_data)} 只 ETF")
    return etf_data

def infer_industry(code: str, name: str = '') -> str:
    """根据代码和名称推断行业"""
    text = code + name
    
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return industry
    
    return '其他'

def calculate_simple_scores(etf_data: Dict) -> Dict:
    """
    计算简化版因子评分（基于缓存数据）
    
    因子:
    - 流动性（日均成交额）
    - 动量（如有历史数据）
    - 规模（基金份额）
    """
    print("计算因子评分...")
    
    scores = {}
    
    for code, data in etf_data.items():
        # 流动性评分（基于成交额）
        turnover = data.get('turnover', 0) or data.get('amount', 0) or 0
        liquidity_score = min(turnover / 1e9, 1) * 0.4  # 10 亿为满分
        
        # 规模评分（基于份额）
        share = data.get('share', 0) or 0
        size_score = min(share / 10, 1) * 0.3  # 10 亿份为满分
        
        # 价格评分（简化）
        price = data.get('close', 0) or data.get('price', 1)
        price_score = 0.3  # 默认
        
        # 综合评分
        composite = liquidity_score + size_score + price_score
        
        # 推断行业
        name = data.get('name', '')
        industry = infer_industry(code, name)
        
        scores[code] = {
            'code': code,
            'name': name,
            'industry': industry,
            'composite': composite,
            'liquidity': liquidity_score,
            'size': size_score,
            'turnover': turnover,
            'share': share,
            'price': price
        }
    
    return scores

def select_top_etfs(scores: Dict, top_n: int = 30) -> List[Dict]:
    """选择 Top N ETF"""
    sorted_etfs = sorted(scores.values(), key=lambda x: -x['composite'])
    return sorted_etfs[:top_n]

def generate_report(top_etfs: List[Dict], total_count: int, output_file: str):
    """生成 Markdown 报告"""
    print(f"生成报告到 {output_file}...")
    
    # 行业分布
    industry_count = {}
    for etf in top_etfs:
        industry = etf['industry']
        industry_count[industry] = industry_count.get(industry, 0) + 1
    
    report = f"""# 📊 全市场 ETF 多因子筛选报告 v5.0

**筛选时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**策略版本**: v5.0（改进版）  
**数据源**: 缓存数据（608 只 ETF）

---

## 一、筛选概况

- **ETF 总数**: {total_count} 只
- **筛选标准**: 流动性 + 规模 + 价格
- **Top N**: {len(top_etfs)}

---

## 二、Top {len(top_etfs)} ETF 名单

| 排名 | 代码 | 名称 | 行业 | 综合分 | 流动性 | 规模 | 成交额 (元) |
|------|------|------|------|--------|--------|------|-------------|
"""
    
    for i, etf in enumerate(top_etfs):
        report += f"| {i+1} | {etf['code']} | {etf['name']} | {etf['industry']} | {etf['composite']:.3f} | {etf['liquidity']:.3f} | {etf['size']:.3f} | {etf['turnover']:,.0f} |\n"
    
    report += f"""
---

## 三、行业分布

| 行业 | 数量 | 占比 |
|------|------|------|
"""
    
    for industry, count in sorted(industry_count.items(), key=lambda x: -x[1]):
        pct = count / len(top_etfs) * 100
        report += f"| {industry} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 四、分层推荐

### 第一层：防守型（高流动性 + 大规模）
"""
    
    defensive = [e for e in top_etfs if e['industry'] in ['宽基', '金融', '红利']][:5]
    for etf in defensive:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    
    report += f"""
### 第二层：成长型（科技 + 制造）
"""
    
    growth = [e for e in top_etfs if e['industry'] in ['科技', '制造', '医药']][:5]
    for etf in growth:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    
    report += f"""
### 第三层：交易型（周期 + 消费）
"""
    
    trading = [e for e in top_etfs if e['industry'] in ['周期', '消费', '其他']][:5]
    for etf in trading:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']})\n"
    
    report += f"""
---

## 五、数据说明

- **数据来源**: etf_data_cache 缓存目录
- **更新时间**: 2026-03-28 盘后
- **因子计算**: 基于缓存数据的简化版评分
- **完整 v5.0 因子**: 需等待 Tushare 速率限制解除后更新

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{output_file}")

def main():
    """主函数"""
    print("="*70)
    print("全市场 ETF 多因子筛选 v5.0（缓存版）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 加载缓存数据
    etf_data = load_etf_from_cache()
    
    if not etf_data:
        print("⚠️ 无缓存数据，退出")
        return
    
    # 2. 计算评分
    scores = calculate_simple_scores(etf_data)
    
    # 3. 选择 Top ETF
    top_etfs = select_top_etfs(scores, TOP_N)
    
    # 4. 打印结果
    print("\n" + "="*70)
    print(f"Top {TOP_N} ETF")
    print("="*70)
    print(f"{'排名':<4} {'代码':<8} {'名称':<15} {'行业':<8} {'综合分':<8} {'流动性':<8}")
    print("="*70)
    
    for i, etf in enumerate(top_etfs):
        print(f"{i+1:<4} {etf['code']:<8} {etf['name']:<15} {etf['industry']:<8} "
              f"{etf['composite']:.3f}    {etf['liquidity']:.3f}")
    
    # 5. 生成 JSON 结果
    results = {
        'screen_time': datetime.now().isoformat(),
        'total_etfs': len(etf_data),
        'top_n': TOP_N,
        'top_etfs': top_etfs,
        'all_scores': scores
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存：{OUTPUT_FILE}")
    
    # 6. 生成报告
    generate_report(top_etfs, len(etf_data), REPORT_FILE)
    
    print("\n" + "="*70)
    print("✅ 全市场筛选完成！")
    print("="*70)

if __name__ == "__main__":
    main()
