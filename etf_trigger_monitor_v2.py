#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 实时触发器监控脚本 v2（优化版）
- 优先使用缓存数据（避免超时）
- 添加超时控制
- 简化飞书推送逻辑
"""

import json
import os
import signal
import sys
from datetime import datetime

# 超时控制（30 秒）
def timeout_handler(signum, frame):
    print("⏰ 脚本执行超时，退出")
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 秒超时

# ============ 配置区域 ============

GRID_MONITOR = {
    "159663": {"name": "科创芯片 ETF", "grid_5": 1.606, "grid_10": 1.522, "grid_15": 1.437},
    "517520": {"name": "新能源车 ETF", "grid_5": 2.014, "grid_10": 1.908, "grid_15": 1.802},
    "159243": {"name": "科创 50ETF", "grid_5": 1.018, "grid_10": 0.965, "grid_15": 0.911},
    "159819": {"name": "人工智能 ETF", "grid_5": 1.397, "grid_10": 1.324, "grid_15": 1.250},
    "515790": {"name": "光伏 ETF", "grid_5": 1.049, "grid_10": 0.994, "grid_15": 0.938},
    "512480": {"name": "半导体 ETF", "grid_5": 1.378, "grid_10": 1.305, "grid_15": 1.233},
    "159241": {"name": "恒生科技 ETF", "grid_5": 1.213, "grid_10": 1.149, "grid_15": 1.085},
    "159227": {"name": "碳中和 ETF", "grid_5": 1.188, "grid_10": 1.125, "grid_15": 1.063},
    "518880": {"name": "黄金 ETF", "grid_5": 8.977, "grid_10": 8.504, "grid_15": 8.032},
    "159937": {"name": "黄金 9999", "grid_5": 8.951, "grid_10": 8.480, "grid_15": 8.009},
    "512010": {"name": "医药 ETF", "grid_5": 0.334, "grid_10": 0.317, "grid_15": 0.299},
    "510500": {"name": "500ETF", "grid_5": 7.302, "grid_10": 6.917, "grid_15": 6.533},
    "510300": {"name": "300ETF", "grid_5": 4.256, "grid_10": 4.032, "grid_15": 3.808},
    "159770": {"name": "机器人 AI", "grid_5": 0.907, "grid_10": 0.860, "grid_15": 0.812},
    "159399": {"name": "现金流 ETF", "grid_5": 1.059, "grid_10": 1.004, "grid_15": 0.948},
    "159206": {"name": "卫星 ETF", "grid_5": 1.512, "grid_10": 1.433, "grid_15": 1.353},
    "159566": {"name": "储能电池", "grid_5": 2.132, "grid_10": 2.020, "grid_15": 1.907},
    "513110": {"name": "纳指 ETF", "grid_5": 1.848, "grid_10": 1.751, "grid_15": 1.653},
    "510880": {"name": "红利 ETF", "grid_5": 3.102, "grid_10": 2.939, "grid_15": 2.775},
    "513500": {"name": "标普 500ETF", "grid_5": 2.109, "grid_10": 1.998, "grid_15": 1.887},
}

TAKE_PROFIT_MONITOR = {
    "160723": {"name": "嘉实原油", "tp_20": 1.301, "tp_40": 1.518},
    "159663": {"name": "机床", "tp_20": 2.118, "tp_40": 2.471},
    "159566": {"name": "储能电池", "tp_20": 2.579, "tp_40": 3.009},
    "159206": {"name": "卫星 ETF", "tp_20": 2.051, "tp_40": 2.393},
}

STOP_LOSS_MONITOR = {
    "159937": {"name": "黄金 9999", "sl_10": 9.604, "sl_15": 9.070},
    "512480": {"name": "半导体", "sl_10": 1.415, "sl_15": 1.336},
    "513500": {"name": "标普 500", "sl_10": 2.055, "sl_15": 1.941},
    "510300": {"name": "300ETF", "sl_10": 4.133, "sl_15": 3.903},
    "510500": {"name": "500ETF", "sl_10": 7.115, "sl_15": 6.719},
    "159363": {"name": "创业板 AI", "sl_10": 0.970, "sl_15": 0.916},
}

CACHE_FILE = "/home/admin/openclaw/workspace/etf_price_cache.json"
TRIGGER_RECORD_FILE = "/home/admin/openclaw/workspace/trigger_records.json"

def load_cache():
    """加载缓存价格数据"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                timestamp = data.get("timestamp", 0)
                cache_age = (datetime.now().timestamp() - timestamp) / 60  # 分钟
                if cache_age < 30:  # 30 分钟内缓存有效
                    print(f"✅ 使用缓存数据（{cache_age:.1f} 分钟前）")
                    return data.get("prices", {})
                else:
                    print(f"⚠️ 缓存过期（{cache_age:.1f} 分钟前）")
        except Exception as e:
            print(f"⚠️ 加载缓存失败：{e}")
    return {}

def load_trigger_records():
    """加载触发记录"""
    if os.path.exists(TRIGGER_RECORD_FILE):
        try:
            with open(TRIGGER_RECORD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_trigger_records(records):
    """保存触发记录"""
    try:
        with open(TRIGGER_RECORD_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存记录失败：{e}")

def check_triggers():
    """检查所有触发条件"""
    prices = load_cache()
    if not prices:
        print("❌ 无可用价格数据，退出")
        return
    
    records = load_trigger_records()
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"ETF 触发器监控 | {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    triggered = []
    
    # 检查网格加仓
    print("\n【网格加仓监控】")
    for code, config in GRID_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config.get('name', code)
        
        for level in ['grid_5', 'grid_10', 'grid_15']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('grid', {}):
                continue
            
            trigger_price = config[level]
            if price <= trigger_price:
                level_pct = level.replace('grid_', '')
                triggered.append(f"🔔 {name}({code}) 下跌{level_pct}% @ {price:.3f} ≤ {trigger_price}")
                records.setdefault('grid', {})[trigger_key] = True
                print(f"  🔔 {name}({code}) 下跌{level_pct}% @ {price:.3f} ≤ {trigger_price}")
    
    # 检查止盈
    print("\n【止盈监控】")
    for code, config in TAKE_PROFIT_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config.get('name', code)
        
        for level in ['tp_20', 'tp_40']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('take_profit', {}):
                continue
            
            trigger_price = config[level]
            if price >= trigger_price:
                level_pct = level.replace('tp_', '')
                triggered.append(f"🎯 {name}({code}) 上涨{level_pct}% @ {price:.3f} ≥ {trigger_price}")
                records.setdefault('take_profit', {})[trigger_key] = True
                print(f"  🎯 {name}({code}) 上涨{level_pct}% @ {price:.3f} ≥ {trigger_price}")
    
    # 检查止损
    print("\n【止损监控】")
    for code, config in STOP_LOSS_MONITOR.items():
        if code not in prices:
            continue
        price_data = prices[code]
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        name = config.get('name', code)
        
        for level in ['sl_10', 'sl_15']:
            trigger_key = f"{code}_{level}_{today}"
            if trigger_key in records.get('stop_loss', {}):
                continue
            
            trigger_price = config[level]
            if price <= trigger_price:
                level_pct = level.replace('sl_', '')
                triggered.append(f"⛔ {name}({code}) 止损{level_pct}% @ {price:.3f} ≤ {trigger_price}")
                records.setdefault('stop_loss', {})[trigger_key] = True
                print(f"  ⛔ {name}({code}) 止损{level_pct}% @ {price:.3f} ≤ {trigger_price}")
    
    # 保存记录
    save_trigger_records(records)
    
    # 汇总
    print(f"\n{'='*60}")
    if triggered:
        print(f"✅ 触发 {len(triggered)} 条")
        for t in triggered:
            print(f"  {t}")
    else:
        print("✅ 无触发")
    print(f"{'='*60}\n")
    
    return triggered

if __name__ == "__main__":
    try:
        check_triggers()
    except Exception as e:
        print(f"❌ 执行错误：{e}")
    finally:
        signal.alarm(0)  # 取消超时
