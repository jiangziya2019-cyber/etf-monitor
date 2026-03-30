#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场 ETF 多因子筛选 v5.0（历史数据版）
版本：v5.0 | 创建：2026-03-28 16:15

使用缓存的历史行情数据计算因子评分
"""

import sys, json, os, glob
from datetime import datetime
from typing import Dict, List
import numpy as np

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
OUTPUT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选结果_v5.json'
REPORT_FILE = '/home/admin/openclaw/workspace/全市场 ETF 筛选报告_v5.md'
TOP_N = 30

# 行业映射
INDUSTRY_KEYWORDS = {
    '宽基': ['300', '500', '50', '180', '红利', '央企', '大盘', '中小', '创业', '科创'],
    '科技': ['科技', '电子', '半导体', '芯片', '计算机', '通信', '5G', '人工智能', '光伏', '新能源', '电池'],
    '金融': ['金融', '银行', '证券', '保险', '券商'],
    '制造': ['制造', '机械', '装备', '机器人', '机床', '储能'],
    '医药': ['医药', '医疗', '生物', '创新药', '中药', '健康'],
    '周期': ['周期', '有色', '金属', '煤炭', '钢铁', '化工', '建材'],
    '消费': ['消费', '食品', '饮料', '家电', '汽车', '旅游', '农业'],
    '全球': ['纳指', '标普', '恒生', '港股', '美国', '全球', '国际', '日经'],
}

# ETF 名称映射（已知 ETF）
ETF_NAMES = {
    '510300': '沪深 300ETF', '510500': '中证 500ETF', '510880': '红利 ETF',
    '515790': '光伏 ETF', '512480': '半导体 ETF', '512880': '证券 ETF',
    '512400': '有色 ETF', '512800': '银行 ETF', '512980': '传媒 ETF',
    '159819': '人工智能 AI', '515260': '电子 ETF', '510180': '180ETF',
    '159949': '创业板 50', '513110': '纳指 ETF', '513500': '标普 500',
}

def load_etf_data() -> Dict[str, Dict]:
    """加载所有 ETF 历史数据"""
    print(f"加载 ETF 历史数据...")
    
    etf_data = {}
    json_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                code = os.path.basename(filepath).replace('.json', '')
                if code.isdigit() and len(code) == 6 and len(data) > 10:
                    etf_data[code] = data
        except:
            pass
    
    print(f"✅ 加载 {len(etf_data)} 只 ETF")
    return etf_data

def infer_industry(code: str) -> str:
    """推断行业"""
    name = ETF_NAMES.get(code, '')
    text = code + name
    
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return industry
    
    return '其他'

def calculate_factors(data: Dict) -> Dict:
    """
    基于历史数据计算因子
    
    因子:
    - 动量（20 日收益率）
    - 波动（20 日波动率）
    - 流动性（平均成交量）
    - 技术（RSI）
    """
    dates = sorted(data.keys())
    if len(dates) < 20:
        return None
    
    # 提取价格和成交量
    prices = [data[d]['close'] for d in dates]
    volumes = [data[d]['vol'] for d in dates]
    
    prices = np.array(prices[-60:])  # 最近 60 天
    volumes = np.array(volumes[-60:])
    
    # 动量（20 日收益率）
    if len(prices) >= 20:
        momentum_20 = (prices[-1] - prices[-20]) / prices[-20]
    else:
        momentum_20 = 0
    
    # 波动率（20 日）
    if len(prices) >= 20:
        returns = np.diff(prices[-20:]) / prices[-20:-1]
        volatility = np.std(returns) * np.sqrt(252)
    else:
        volatility = 0
    
    # 流动性（平均成交量）
    avg_volume = np.mean(volumes[-20:])
    
    # RSI（14 日）
    if len(prices) >= 14:
        deltas = np.diff(prices[-14:])
        gains = np.sum(deltas[deltas > 0]) / 14
        losses = np.sum(-deltas[deltas < 0]) / 14
        if losses == 0:
            rsi = 100
        else:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
    else:
        rsi = 50
    
    # 当前价格
    current_price = prices[-1]
    
    return {
        'momentum_20': momentum_20,
        'volatility': volatility,
        'avg_volume': avg_volume,
        'rsi': rsi,
        'current_price': current_price
    }

def calculate_scores(etf_data: Dict) -> Dict:
    """计算所有 ETF 的综合评分"""
    print("计算因子评分...")
    
    scores = {}
    
    for code, data in etf_data.items():
        factors = calculate_factors(data)
        if factors is None:
            continue
        
        # 标准化评分（0-1）
        momentum_score = min(max(factors['momentum_20'] + 0.2, 0), 1) * 0.3  # 动量 30%
        volatility_score = (1 - min(factors['volatility'] / 0.5, 1)) * 0.2  # 低波动 20%
        liquidity_score = min(factors['avg_volume'] / 1e7, 1) * 0.3  # 流动性 30%
        rsi_score = (1 - abs(factors['rsi'] - 50) / 50) * 0.2  # RSI 中性 20%
        
        composite = momentum_score + volatility_score + liquidity_score + rsi_score
        
        scores[code] = {
            'code': code,
            'name': ETF_NAMES.get(code, '未知'),
            'industry': infer_industry(code),
            'composite': composite,
            'momentum': momentum_score,
            'volatility': volatility_score,
            'liquidity': liquidity_score,
            'rsi': rsi_score,
            'factors': factors
        }
    
    print(f"✅ 计算 {len(scores)} 只 ETF 评分")
    return scores

def select_top(scores: Dict, top_n: int) -> List[Dict]:
    """选择 Top N"""
    sorted_etfs = sorted(scores.values(), key=lambda x: -x['composite'])
    return sorted_etfs[:top_n]

def generate_report(top_etfs: List[Dict], total: int):
    """生成报告"""
    print(f"生成报告...")
    
    # 行业分布
    industry_count = {}
    for etf in top_etfs:
        ind = etf['industry']
        industry_count[ind] = industry_count.get(ind, 0) + 1
    
    report = f"""# 📊 全市场 ETF 多因子筛选报告 v5.0

**筛选时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**策略版本**: v5.0（改进版）  
**数据源**: 历史行情数据（60 日）

---

## 一、筛选概况

- **ETF 总数**: {total} 只
- **有效数据**: {len(top_etfs)} 只
- **筛选因子**: 动量 (30%) + 波动 (20%) + 流动性 (30%) + RSI(20%)
- **Top N**: {len(top_etfs)}

---

## 二、Top {len(top_etfs)} ETF 名单

| 排名 | 代码 | 名称 | 行业 | 综合分 | 动量 | 波动 | 流动性 | RSI | 20 日收益 |
|------|------|------|------|--------|------|------|--------|-----|----------|
"""
    
    for i, etf in enumerate(top_etfs):
        f = etf['factors']
        report += f"| {i+1} | {etf['code']} | {etf['name']} | {etf['industry']} | {etf['composite']:.3f} | {etf['momentum']:.3f} | {etf['volatility']:.3f} | {etf['liquidity']:.3f} | {etf['rsi']:.3f} | {f['momentum_20']*100:+.1f}% |\n"
    
    report += f"""
---

## 三、行业分布

| 行业 | 数量 | 占比 |
|------|------|------|
"""
    
    for ind, count in sorted(industry_count.items(), key=lambda x: -x[1]):
        pct = count / len(top_etfs) * 100
        report += f"| {ind} | {count} | {pct:.1f}% |\n"
    
    report += f"""
---

## 四、分层推荐

### 第一层：防守型（低波动 + 稳定）
"""
    defensive = sorted([e for e in top_etfs if e['volatility'] > 0.6], key=lambda x: -x['composite'])[:5]
    for etf in defensive:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']}) 波动={etf['volatility']:.3f}\n"
    if not defensive:
        report += "- 暂无低波动品种\n"
    
    report += f"""
### 第二层：成长型（高动量）
"""
    growth = sorted([e for e in top_etfs if e['momentum'] > 0.6], key=lambda x: -x['momentum'])[:5]
    for etf in growth:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']}) 动量={etf['momentum']:.3f}\n"
    if not growth:
        report += "- 暂无高动量品种\n"
    
    report += f"""
### 第三层：交易型（高流动性）
"""
    trading = sorted([e for e in top_etfs if e['liquidity'] > 0.6], key=lambda x: -x['liquidity'])[:5]
    for etf in trading:
        report += f"- {etf['code']} {etf['name']} ({etf['industry']}) 流动性={etf['liquidity']:.3f}\n"
    if not trading:
        report += "- 暂无高流动性品种\n"
    
    report += f"""
---

## 五、说明

- **数据来源**: etf_data_cache（60 日历史行情）
- **因子计算**: 基于真实历史数据
- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **完整 v5.0**: 等待 Tushare 速率限制解除后更新 7 大因子

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{REPORT_FILE}")

def main():
    print("="*70)
    print("全市场 ETF 多因子筛选 v5.0（历史数据版）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 1. 加载数据
    etf_data = load_etf_data()
    
    # 2. 计算评分
    scores = calculate_scores(etf_data)
    
    # 3. 选择 Top
    top_etfs = select_top(scores, TOP_N)
    
    # 4. 打印
    print("\n" + "="*70)
    print(f"Top {TOP_N} ETF")
    print("="*70)
    print(f"{'排名':<4} {'代码':<8} {'名称':<12} {'行业':<8} {'综合':<6} {'动量':<6} {'流动性':<6} {'20 日':<8}")
    print("="*70)
    
    for i, etf in enumerate(top_etfs):
        f = etf['factors']
        print(f"{i+1:<4} {etf['code']:<8} {etf['name']:<12} {etf['industry']:<8} "
              f"{etf['composite']:.3f}  {etf['momentum']:.3f}  {etf['liquidity']:.3f}  "
              f"{f['momentum_20']*100:+6.1f}%")
    
    # 5. 保存结果
    results = {
        'screen_time': datetime.now().isoformat(),
        'total_etfs': len(etf_data),
        'valid_etfs': len(scores),
        'top_n': TOP_N,
        'top_etfs': top_etfs,
        'all_scores': scores
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存：{OUTPUT_FILE}")
    
    # 6. 生成报告
    generate_report(top_etfs, len(scores))
    
    print("\n" + "="*70)
    print("✅ 全市场筛选完成！")
    print("="*70)

if __name__ == "__main__":
    main()
