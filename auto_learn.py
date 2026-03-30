#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Improving Agent 自动学习脚本
从每次交互中学习和记录经验
"""

import json
import os
from datetime import datetime
from typing import Dict, List

MEMORY_BASE = "/home/admin/openclaw/workspace/memory"

def record_experience(skill_name: str, outcome: str, lessons: List[str], timestamp: str = None):
    """记录技能使用经验"""
    if not timestamp:
        timestamp = datetime.now().isoformat()
    
    experience = {
        "timestamp": timestamp,
        "skill": skill_name,
        "outcome": outcome,  # success/failure/partial
        "lessons": lessons,
        "patterns": [],
        "confidence": 0.8
    }
    
    # 追加到情景记忆
    today = datetime.now().strftime('%Y-%m-%d')
    episode_file = f"{MEMORY_BASE}/episodic/{today}-experiences.jsonl"
    
    with open(episode_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(experience, ensure_ascii=False) + '\n')
    
    print(f"✅ 记录经验：{skill_name} - {outcome}")
    return experience

def extract_pattern(experience: Dict) -> Dict:
    """从经验中提取模式"""
    skill = experience.get('skill', '')
    lessons = experience.get('lessons', [])
    
    pattern = {
        "skill": skill,
        "condition": "",
        "action": "",
        "result": experience.get('outcome', ''),
        "confidence": experience.get('confidence', 0.5),
        "created": datetime.now().isoformat()
    }
    
    # 简单模式提取（可扩展）
    if '数据' in skill and '失败' in experience.get('outcome', ''):
        pattern['condition'] = "数据获取失败"
        pattern['action'] = "切换到备份数据源"
    elif '触发器' in skill and '成功' in experience.get('outcome', ''):
        pattern['condition'] = "触发器检查"
        pattern['action'] = "五维评分 + 连续确认"
    
    return pattern

def update_semantic_memory(pattern: Dict):
    """更新语义记忆（模式/规则）"""
    pattern_file = f"{MEMORY_BASE}/semantic/learned_patterns.jsonl"
    
    with open(pattern_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(pattern, ensure_ascii=False) + '\n')
    
    print(f"✅ 更新语义记忆：{pattern.get('condition', 'unknown')}")

def learn_from_session(session_summary: str):
    """从会话总结中学习"""
    # 提取关键决策、配置变更、错误教训
    lines = session_summary.split('\n')
    
    for line in lines:
        if '决策' in line or '配置' in line or '教训' in line:
            # 记录重要信息
            note = {
                "type": "session_learning",
                "content": line,
                "timestamp": datetime.now().isoformat()
            }
            
            note_file = f"{MEMORY_BASE}/working/session_notes.jsonl"
            with open(note_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(note, ensure_ascii=False) + '\n')

def main():
    """主函数 - 手动触发学习"""
    print("=" * 80)
    print("Self-Improving Agent - 学习检查")
    print("=" * 80)
    
    # 检查配置
    config_file = "/home/admin/openclaw/workspace/self_improving_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            print(f"\n✅ 配置已加载")
            print(f"  自动触发：{config.get('auto_trigger', False)}")
            print(f"  记录成功：{config.get('learning_rules', {}).get('record_success', False)}")
            print(f"  记录失败：{config.get('learning_rules', {}).get('record_failure', False)}")
    else:
        print(f"\n❌ 配置文件不存在")
        return
    
    # 检查记忆目录
    print(f"\n📂 记忆目录:")
    for mem_type in ['semantic', 'episodic', 'working']:
        path = f"{MEMORY_BASE}/{mem_type}/"
        if os.path.exists(path):
            files = os.listdir(path)
            print(f"  {mem_type}: {len(files)} 个文件")
        else:
            print(f"  {mem_type}: ❌ 不存在")
    
    # 测试记录
    print(f"\n🧪 测试学习功能...")
    exp = record_experience(
        skill_name="智能触发器 v2.0",
        outcome="success",
        lessons=[
            "五维评分系统工作正常",
            "Tushare 数据源稳定",
            "15 分钟频率合适"
        ]
    )
    
    pattern = extract_pattern(exp)
    update_semantic_memory(pattern)
    
    print(f"\n✅ Self-Improving Agent 已激活")
    print("=" * 80)

if __name__ == "__main__":
    main()
