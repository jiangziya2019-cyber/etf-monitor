#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 资金流向模块
整合行业/概念资金流数据
"""

from .base import get_tushare_data
from datetime import datetime, timedelta

def get_industry_moneyflow(trade_date=None):
    """
    获取行业资金流向
    接口：moneyflow_ind_dc (doc_344)
    注意：每日盘后更新，上午获取前一日数据
    """
    print(f"\n获取行业资金流向...")
    
    if trade_date is None:
        # 获取前一日数据
        trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    data = get_tushare_data("moneyflow_ind_dc", trade_date=trade_date, content_type='行业')
    
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        result = []
        for item in data["items"]:
            row = dict(zip(fields, item))
            result.append({
                'name': row.get("industry_name", ""),
                'net_in': row.get("net_in", 0),
                'net_in_rate': row.get("net_in_rate", 0),
                'change_pct': row.get("change_pct", 0)
            })
        
        # 排序
        result.sort(key=lambda x: x['net_in'], reverse=True)
        
        print(f"  ✅ 流入 TOP3: {[d['name'] for d in result[:3]]}")
        print(f"  ❌ 流出 TOP3: {[d['name'] for d in result[-3:]]}")
        return result
    else:
        print(f"  ❌ 行业资金流数据获取失败")
        return []

def get_concept_moneyflow(trade_date=None):
    """
    获取概念板块资金流向
    接口：moneyflow_ind_dc (doc_344)
    """
    print(f"\n获取概念板块资金流向...")
    
    if trade_date is None:
        trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    data = get_tushare_data("moneyflow_ind_dc", trade_date=trade_date, content_type='概念')
    
    if data and "items" in data and data["items"]:
        fields = data.get("fields", [])
        target_concepts = ['人工智能', '芯片', '半导体', '光伏', '储能', '新能源车', 
                          '数字经济', '军工', '医药', '消费']
        
        result = {}
        for item in data["items"][:50]:
            row = dict(zip(fields, item))
            name = row.get("name", "")
            
            for target in target_concepts:
                if target in name:
                    result[name] = {
                        'pct_change': row.get("pct_change", 0),
                        'net_amount': row.get("net_amount", 0) / 100000000,
                        'rank': row.get("rank", 0)
                    }
                    signal = "🔥" if row.get("net_amount", 0) > 50000000 else ("✅" if row.get("net_amount", 0) > 0 else "❌")
                    print(f"  {signal} {name}: {row.get('pct_change', 0):+.2f}% 净流入¥{result[name]['net_amount']:.2f}亿")
                    break
        return result
    else:
        print(f"  ❌ 概念板块资金流数据获取失败")
        return {}
