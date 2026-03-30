#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare Pro 基础模块 - 通用接口 + 重试机制 + 降级策略
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path

# Tushare 配置
TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
TUSHARE_URL = "http://api.tushare.pro"

# 缓存配置
CACHE_DIR = Path("/tmp/tushare_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 180  # 3 分钟缓存

def get_tushare_data(api_name, max_retries=3, retry_delay=2, use_cache=True, **params):
    """
    通用 Tushare 接口调用（带重试机制 + 缓存）
    
    Args:
        api_name: 接口名称
        max_retries: 最大重试次数 (默认 3 次)
        retry_delay: 重试间隔秒数 (默认 2 秒)
        use_cache: 是否使用缓存 (默认 True)
        **params: 接口参数
    
    Returns:
        dict: 接口返回数据，失败返回 None
    """
    # 检查缓存
    if use_cache:
        cache_key = f"{api_name}_{json.dumps(params, sort_keys=True)}"
        cache_file = CACHE_DIR / f"{hash(cache_key)}.json"
        
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text())
                cache_time = cache_data.get('_cache_time', 0)
                if (datetime.now().timestamp() - cache_time) < CACHE_TTL:
                    print(f"  💾 使用缓存数据：{api_name}")
                    return cache_data.get('data', {})
            except:
                pass
    
    # 构建请求
    payload = {"api_name": api_name, "token": TUSHARE_TOKEN, "params": params}
    
    # 重试机制
    for retry in range(max_retries):
        try:
            resp = requests.post(TUSHARE_URL, json=payload, timeout=10)
            result = resp.json()
            
            if result.get("code") == 0:
                data = result.get("data", {})
                
                # 保存缓存
                if use_cache and data:
                    cache_data = {
                        'data': data,
                        '_cache_time': datetime.now().timestamp()
                    }
                    try:
                        cache_file.write_text(json.dumps(cache_data))
                    except:
                        pass
                
                return data
            else:
                error_msg = result.get('msg', 'Unknown error')
                print(f"❌ 接口错误 (第{retry+1}次): {api_name} - {error_msg}")
                if retry < max_retries - 1:
                    print(f"   {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    
        except requests.exceptions.Timeout:
            print(f"⚠️ 网络超时 (第{retry+1}次)，{retry_delay}秒后重试...")
            time.sleep(retry_delay)
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 网络错误 (第{retry+1}次): {e}，{retry_delay}秒后重试...")
            time.sleep(retry_delay)
            
        except Exception as e:
            print(f"⚠️ 未知错误 (第{retry+1}次): {e}")
            break
    
    print(f"❌ 接口 {api_name} 获取失败（{max_retries}次重试后）")
    return None

def clear_cache():
    """清除所有缓存"""
    try:
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()
        print("✅ 缓存已清除")
    except:
        pass
