#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书消息发送脚本 - 使用 App Bot API
"""

import requests
import json
import time

# 飞书配置
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"
BOSS_OPEN_ID = "ou_d59d5ba9ec93dfbe3d1c143c5526721a"

def get_tenant_access_token():
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    
    response = requests.post(url, json=payload, timeout=10)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"获取 token 失败：{result}")
        return None

def send_message(text):
    """发送文本消息"""
    token = get_tenant_access_token()
    if not token:
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "receive_id": BOSS_OPEN_ID,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    result = response.json()
    
    if result.get("code") == 0:
        print(f"消息发送成功：{result.get('data', {}).get('message_id')}")
        return True
    else:
        print(f"消息发送失败：{result}")
        return False

def send_post_message(title, content):
    """发送富文本消息（Post）"""
    token = get_tenant_access_token()
    if not token:
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 构建 Post 消息内容
    post_content = {
        "zh_cn": {
            "title": title,
            "content": content
        }
    }
    
    payload = {
        "receive_id": BOSS_OPEN_ID,
        "msg_type": "post",
        "content": json.dumps(post_content)
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    result = response.json()
    
    if result.get("code") == 0:
        print(f"消息发送成功：{result.get('data', {}).get('message_id')}")
        return True
    else:
        print(f"消息发送失败：{result}")
        return False

if __name__ == "__main__":
    # 测试消息
    test_text = "📊 盘前准备报告测试\n\n测试飞书消息发送功能"
    send_message(test_text)
