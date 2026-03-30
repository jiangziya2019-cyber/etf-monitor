#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓数据备份脚本
每次更新 holdings_current.json 后自动备份，防止数据丢失
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# 配置
HOLDINGS_FILE = "/home/admin/openclaw/workspace/holdings_current.json"
BACKUP_DIR = "/home/admin/openclaw/workspace/holdings_backup"
MAX_BACKUPS = 30  # 保留最近 30 个备份

def create_backup():
    """创建持仓数据备份"""
    
    # 检查源文件是否存在
    if not os.path.exists(HOLDINGS_FILE):
        print(f"❌ 错误：持仓文件不存在 {HOLDINGS_FILE}")
        return False
    
    # 创建备份目录
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"holdings_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # 读取并验证源数据
    try:
        with open(HOLDINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证必要字段
        required_fields = ['last_updated', 'total_market_value', 'etfs']
        for field in required_fields:
            if field not in data:
                print(f"❌ 错误：数据缺少必要字段 {field}")
                return False
        
        print(f"✅ 验证通过：{len(data['etfs'])} 只 ETF，总市值 {data['total_market_value']:,.2f} 元")
        
    except json.JSONDecodeError as e:
        print(f"❌ 错误：JSON 格式无效 {e}")
        return False
    
    # 复制文件到备份目录
    shutil.copy2(HOLDINGS_FILE, backup_path)
    print(f"✅ 备份成功：{backup_filename}")
    
    # 同时创建 latest 备份（总是覆盖）
    latest_backup = os.path.join(BACKUP_DIR, "holdings_latest.json")
    shutil.copy2(HOLDINGS_FILE, latest_backup)
    print(f"✅ 最新备份已更新：holdings_latest.json")
    
    # 清理旧备份（保留最近 N 个）
    cleanup_old_backups()
    
    return True

def cleanup_old_backups():
    """清理旧备份，保留最近 MAX_BACKUPS 个"""
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR) 
            if f.startswith('holdings_') and f.endswith('.json') 
            and f != 'holdings_latest.json'
        ])
        
        if len(backups) > MAX_BACKUPS:
            to_delete = backups[:-MAX_BACKUPS]
            for filename in to_delete:
                os.remove(os.path.join(BACKUP_DIR, filename))
                print(f"🗑️  已删除旧备份：{filename}")
    
    except Exception as e:
        print(f"⚠️  清理备份时出错：{e}")

def list_backups():
    """列出所有备份"""
    if not os.path.exists(BACKUP_DIR):
        print("❌ 备份目录不存在")
        return
    
    backups = sorted([
        f for f in os.listdir(BACKUP_DIR) 
        if f.startswith('holdings_') and f.endswith('.json')
    ], reverse=True)
    
    print(f"\n📦 持仓数据备份列表（共 {len(backups)} 个）\n")
    print(f"{'文件名':<35} {'大小':<10} {'创建时间'}")
    print("-" * 70)
    
    for filename in backups:
        filepath = os.path.join(BACKUP_DIR, filename)
        size = os.path.getsize(filepath)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        print(f"{filename:<35} {size:>8}B  {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def restore_backup(backup_filename=None):
    """从备份恢复"""
    if backup_filename is None:
        # 使用最新备份
        backup_filename = "holdings_latest.json"
    
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ 错误：备份文件不存在 {backup_filename}")
        return False
    
    # 恢复
    shutil.copy2(backup_path, HOLDINGS_FILE)
    print(f"✅ 恢复成功：从 {backup_filename} 恢复到 holdings_current.json")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            create_backup()
        
        elif command == "list":
            list_backups()
        
        elif command == "restore":
            backup_file = sys.argv[2] if len(sys.argv) > 2 else None
            restore_backup(backup_file)
        
        elif command == "verify":
            # 验证当前文件和最新备份
            if os.path.exists(HOLDINGS_FILE):
                with open(HOLDINGS_FILE, 'r', encoding='utf-8') as f:
                    current = json.load(f)
                print(f"✅ 当前文件：{len(current['etfs'])} 只 ETF，总市值 {current['total_market_value']:,.2f} 元")
            
            latest_backup = os.path.join(BACKUP_DIR, "holdings_latest.json")
            if os.path.exists(latest_backup):
                with open(latest_backup, 'r', encoding='utf-8') as f:
                    backup = json.load(f)
                print(f"✅ 最新备份：{len(backup['etfs'])} 只 ETF，总市值 {backup['total_market_value']:,.2f} 元")
    else:
        # 默认执行备份
        create_backup()
