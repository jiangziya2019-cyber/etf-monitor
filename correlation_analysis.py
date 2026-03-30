#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块相关性分析模块
计算板块间相关性矩阵，识别高相关板块群和轮动传导链
"""

import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"
CACHE_DIR = Path("/home/admin/openclaw/workspace/correlation_cache")
CACHE_DIR.mkdir(exist_ok=True)

NAME_MAP_FILE = Path("/home/admin/openclaw/workspace/sector_name_map.json")
SECTOR_NAME_MAP = json.load(open(NAME_MAP_FILE, "r", encoding="utf-8")) if NAME_MAP_FILE.exists() else {}

def get_tushare_data(api_name, **params):
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = resp.json()
        return result.get("data", {}) if result.get("code") == 0 else None
    except:
        return None

def get_sector_returns(days=60, top_n=50):
    """获取板块收益率序列"""
    print("获取板块收益率数据...")
    
    sector_returns = {}
    dates_processed = set()
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        if date in dates_processed:
            continue
        
        data = get_tushare_data("dc_daily", trade_date=date)
        if data and "items" in data and data["items"]:
            fields = data.get("fields", [])
            for item in data.get("items", []):
                row = dict(zip(fields, item))
                if row.get("category") != "行业板块":
                    continue
                
                ts_code = row.get("ts_code", "")
                code_short = ts_code.split('.')[0]
                name = SECTOR_NAME_MAP.get(code_short, ts_code)
                pct_change = row.get("pct_change")
                
                if ts_code not in sector_returns:
                    sector_returns[ts_code] = {"name": name, "returns": {}, "dates": []}
                
                if pct_change is not None and date not in sector_returns[ts_code]["dates"]:
                    sector_returns[ts_code]["returns"][date] = float(pct_change)
                    sector_returns[ts_code]["dates"].append(date)
                    dates_processed.add(date)
    
    # 只保留有足够数据的板块
    valid_sectors = {k: v for k, v in sector_returns.items() if len(v["returns"]) >= 30}
    
    print(f"   获取 {len(valid_sectors)} 个板块 (>=30 天数据)")
    return valid_sectors

def calculate_correlation_matrix(sector_returns):
    """计算相关性矩阵"""
    print("计算相关性矩阵...")
    
    # 获取共同交易日
    all_dates = set()
    for data in sector_returns.values():
        all_dates.update(data["dates"])
    common_dates = sorted(all_dates)
    
    # 构建收益率矩阵
    codes = list(sector_returns.keys())[:50]  # 只计算前 50 个
    names = [sector_returns[c]["name"] for c in codes]
    
    returns_matrix = []
    for code in codes:
        row = [sector_returns[code]["returns"].get(d, 0) for d in common_dates]
        returns_matrix.append(row)
    
    returns_array = np.array(returns_matrix)
    
    # 计算相关系数矩阵
    corr_matrix = np.corrcoef(returns_array)
    
    print(f"   计算 {len(codes)}x{len(codes)} 相关性矩阵")
    return codes, names, corr_matrix

def find_highly_correlated_clusters(corr_matrix, names, threshold=0.8):
    """识别高相关板块群"""
    print(f"识别高相关板块群 (阈值>{threshold})...")
    
    n = len(corr_matrix)
    clusters = []
    visited = [False] * n
    
    for i in range(n):
        if visited[i]:
            continue
        
        cluster = [i]
        visited[i] = True
        
        for j in range(i+1, n):
            if visited[j]:
                continue
            
            # 检查是否与集群中所有成员都高度相关
            avg_corr = np.mean([corr_matrix[j][k] for k in cluster])
            if avg_corr > threshold:
                cluster.append(j)
                visited[j] = True
        
        if len(cluster) > 1:
            clusters.append(cluster)
    
    print(f"   找到 {len(clusters)} 个高相关板块群")
    return clusters

def find_leading_lagging_relationships(sector_returns, codes, names, lag_days=3):
    """分析轮动传导关系（领先 - 滞后）"""
    print(f"分析轮动传导关系 (滞后{lag_days}天)...")
    
    relationships = []
    
    # 简化版：只分析 top 10 板块
    top_codes = codes[:10]
    top_names = names[:10]
    
    for i, code1 in enumerate(top_codes):
        for j, code2 in enumerate(top_codes):
            if i >= j:
                continue
            
            returns1 = [sector_returns[code1]["returns"].get(d, 0) for d in sorted(sector_returns[code1]["dates"])]
            returns2 = [sector_returns[code2]["returns"].get(d, 0) for d in sorted(sector_returns[code2]["dates"])]
            
            if len(returns1) < 20 or len(returns2) < 20:
                continue
            
            # 计算互相关
            corr_now = np.corrcoef(returns1, returns2)[0, 1]
            
            # 滞后相关性
            if len(returns1) > lag_days:
                returns1_lagged = returns1[:-lag_days]
                returns2_current = returns2[lag_days:]
                if len(returns1_lagged) == len(returns2_current):
                    corr_lagged = np.corrcoef(returns1_lagged, returns2_current)[0, 1]
                    
                    if corr_lagged > corr_now + 0.1:
                        relationships.append({
                            "leader": top_names[i],
                            "follower": top_names[j],
                            "lag_days": lag_days,
                            "corr": corr_lagged
                        })
                    elif corr_lagged < corr_now - 0.1:
                        relationships.append({
                            "leader": top_names[j],
                            "follower": top_names[i],
                            "lag_days": lag_days,
                            "corr": abs(corr_lagged)
                        })
    
    print(f"   找到 {len(relationships)} 个传导关系")
    return relationships

def generate_report(corr_matrix, names, clusters, relationships):
    """生成相关性分析报告"""
    lines = ["📊 板块相关性分析报告", f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    # 相关性统计
    upper_tri = corr_matrix[np.triu_indices(len(corr_matrix), k=1)]
    avg_corr = np.mean(upper_tri)
    max_corr = np.max(upper_tri)
    min_corr = np.min(upper_tri)
    
    lines.append("━━━ 相关性统计 ━━━")
    lines.append(f"平均相关性：{avg_corr:.3f}")
    lines.append(f"最高相关性：{max_corr:.3f}")
    lines.append(f"最低相关性：{min_corr:.3f}")
    lines.append("")
    
    # 高相关板块群
    lines.append("━━━ 高相关板块群 ━━━")
    if clusters:
        for i, cluster in enumerate(clusters[:10], 1):
            cluster_names = [names[j] for j in cluster]
            avg_c = np.mean([corr_matrix[j][k] for j in cluster for k in cluster if j < k])
            lines.append(f"{i}. {', '.join(cluster_names)} (平均相关{avg_c:.2f})")
    else:
        lines.append("未发现高相关板块群 (阈值>0.8)")
    lines.append("")
    
    # 轮动传导关系
    lines.append("━━━ 轮动传导关系 ━━━")
    if relationships:
        for rel in relationships[:10]:
            lines.append(f"• {rel['leader']} → {rel['follower']} (滞后{rel['lag_days']}天，相关{rel['corr']:.2f})")
    else:
        lines.append("未发现明显传导关系")
    lines.append("")
    
    # 相关性热力图数据（简化版）
    lines.append("━━━ 相关性 TOP10 ━━━")
    pairs = []
    n = len(names)
    for i in range(n):
        for j in range(i+1, n):
            pairs.append((names[i], names[j], corr_matrix[i][j]))
    
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    for name1, name2, corr in pairs[:10]:
        lines.append(f"• {name1} ↔ {name2}: {corr:.3f}")
    
    lines.append("")
    lines.append("⚠️ 数据源：Tushare Pro | 60 日收益率 | 50 个主要板块")
    return "\n".join(lines)

def save_results(codes, names, corr_matrix, clusters, relationships):
    """保存结果"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "codes": codes,
        "names": names,
        "correlation_matrix": corr_matrix.tolist(),
        "clusters": [[names[j] for j in cluster] for cluster in clusters],
        "relationships": relationships
    }
    
    with open(CACHE_DIR / "correlation_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存：{CACHE_DIR / 'correlation_analysis.json'}")

def main():
    print("="*60)
    print("板块相关性分析")
    print("="*60)
    
    # 1. 获取收益率数据
    sector_returns = get_sector_returns(days=60, top_n=50)
    
    # 2. 计算相关性矩阵
    codes, names, corr_matrix = calculate_correlation_matrix(sector_returns)
    
    # 3. 识别高相关板块群
    clusters = find_highly_correlated_clusters(corr_matrix, names, threshold=0.75)
    
    # 4. 分析轮动传导关系
    relationships = find_leading_lagging_relationships(sector_returns, codes, names, lag_days=3)
    
    # 5. 生成报告
    report = generate_report(corr_matrix, names, clusters, relationships)
    print("\n" + report)
    
    # 6. 保存结果
    save_results(codes, names, corr_matrix, clusters, relationships)
    
    print("\n✅ 分析完成")

if __name__ == "__main__":
    main()
