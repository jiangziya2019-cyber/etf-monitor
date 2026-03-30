#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全更新持仓数据
流程：备份现有数据 → 写入新数据 → 验证 → 创建新备份
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HOLDINGS_FILE = "/home/admin/openclaw/workspace/holdings_current.json"
BACKUP_DIR = "/home/admin/openclaw/workspace/holdings_backup"

def safe_update_holdings(new_data):
    """
    安全更新持仓数据
    
    Args:
        new_data: 新的持仓数据（dict）
    
    Returns:
        bool: 是否成功
    """
    
    # 1. 备份现有数据（如果存在）
    if os.path.exists(HOLDINGS_FILE):
        print("📦 正在备份现有数据...")
        backup_holdings()
    
    # 2. 写入新数据到临时文件
    temp_file = HOLDINGS_FILE + ".tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        print("✅ 临时文件写入成功")
    except Exception as e:
        print(f"❌ 写入临时文件失败：{e}")
        return False
    
    # 3. 验证临时文件
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # 验证必要字段
        required = ['last_updated', 'total_market_value', 'etfs']
        for field in required:
            if field not in test_data:
                raise ValueError(f"缺少必要字段：{field}")
        
        # 验证 ETF 数量
        if not isinstance(test_data['etfs'], list) or len(test_data['etfs']) == 0:
            raise ValueError("ETF 列表为空或格式错误")
        
        print(f"✅ 数据验证通过：{len(test_data['etfs'])} 只 ETF")
        
    except Exception as e:
        print(f"❌ 数据验证失败：{e}")
        # 删除临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False
    
    # 4. 原子替换（先删除再重命名）
    try:
        if os.path.exists(HOLDINGS_FILE):
            os.remove(HOLDINGS_FILE)
        os.rename(temp_file, HOLDINGS_FILE)
        print("✅ 数据更新成功")
    except Exception as e:
        print(f"❌ 文件替换失败：{e}")
        return False
    
    # 5. 创建新备份
    print("📦 正在创建新备份...")
    backup_holdings()
    
    return True

def backup_holdings():
    """创建备份"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"holdings_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    shutil.copy2(HOLDINGS_FILE, backup_path)
    
    # 更新 latest 备份
    latest_backup = os.path.join(BACKUP_DIR, "holdings_latest.json")
    shutil.copy2(HOLDINGS_FILE, latest_backup)
    
    print(f"✅ 备份成功：{backup_filename}")

if __name__ == "__main__":
    # 从参数或 stdin 读取新数据
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
    else:
        # 从 stdin 读取
        new_data = json.load(sys.stdin)
    
    # 添加时间戳（如果没有）
    if 'last_updated' not in new_data:
        new_data['last_updated'] = datetime.now().astimezone().isoformat()
    
    # 执行安全更新
    success = safe_update_holdings(new_data)
    
    if success:
        print("\n✅ 持仓数据更新完成！")
        print(f"   文件：{HOLDINGS_FILE}")
        print(f"   ETF 数量：{len(new_data['etfs'])}")
        print(f"   总市值：{new_data['total_market_value']:,.2f} 元")
        print(f"   备份位置：{BACKUP_DIR}/")
    else:
        print("\n❌ 持仓数据更新失败！")
        sys.exit(1)
