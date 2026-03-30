#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Tushare 板块数据接口
"""

import requests
import json
from datetime import datetime

TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

def test_api(api_name, **params):
    """测试接口"""
    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params
    }
    
    try:
        response = requests.post(TUSHARE_URL, json=payload, timeout=10)
        result = response.json()
        
        if result.get("code") == 0:
            data = result.get("data", {})
            print(f"✅ {api_name} - 成功")
            
            # 显示字段和样本数据
            if "fields" in data:
                print(f"   字段：{data['fields'][:10]}...")
            if "items" in data and data["items"]:
                print(f"   数据量：{len(data['items'])} 条")
                print(f"   样本：{data['items'][0][:5]}...")
            
            return data
        else:
            print(f"❌ {api_name} - 失败：{result.get('msg', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ {api_name} - 异常：{e}")
        return None

def main():
    print("=" * 60)
    print("Tushare 板块数据接口测试")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y%m%d")
    last_week = (datetime.now()).strftime("%Y%m%d")
    
    # 1. 板块涨跌数据
    print("\n1. 测试 dc_daily (板块涨跌)")
    test_api("dc_daily", trade_date=today)
    
    # 2. 板块资金流向
    print("\n2. 测试 moneyflow_indcty (行业资金流)")
    test_api("moneyflow_indcty")
    
    # 3. 板块资金流向（个股）
    print("\n3. 测试 moneyflow_cnt (个股资金流)")
    test_api("moneyflow_cnt", trade_date=today)
    
    # 4. 指数估值数据
    print("\n4. 测试 index_dailybasic (指数基本面)")
    test_api("index_dailybasic", ts_code="000300.SH", trade_date=today)
    
    # 5. 申万行业指数
    print("\n5. 测试 index_classify (行业分类)")
    test_api("index_classify", level="L1", src="SW2021")
    
    # 6. 申万行业行情
    print("\n6. 测试 index_weekly (行业周度行情)")
    test_api("index_weekly", ts_code="801010.SI")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
