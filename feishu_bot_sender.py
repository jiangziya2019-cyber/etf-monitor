#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 App Bot 消息发送模块
使用 OpenClaw 配置的飞书凭证发送通知
"""

import json
import requests
import os
from datetime import datetime

# API 配置
API_BASE = "https://open.feishu.cn/open-apis"

# 从环境变量或配置获取凭证
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a9493d702278dbb7")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI")

# 缓存 token（2 小时有效期）
_token_cache = {"token": None, "expires_at": 0}

def get_tenant_token():
    """获取 tenant_access_token"""
    import time
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        token = data.get("tenant_access_token")
        _token_cache["token"] = token
        _token_cache["expires_at"] = time.time() + 7200  # 2 小时
        return token
    else:
        print(f"❌ 获取 token 失败：{data}")
        return None

def get_bot_chats(token):
    """获取机器人所在的聊天列表"""
    resp = requests.get(
        f"{API_BASE}/im/v1/chats?page_size=50",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("items", [])
    return []

def send_message(chat_id, msg_type, content, token):
    """发送消息到指定聊天"""
    resp = requests.post(
        f"{API_BASE}/im/v1/messages?receive_id_type=chat_id",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": chat_id,
            "msg_type": msg_type,
            "content": json.dumps(content) if isinstance(content, dict) else content
        },
        timeout=10
    )
    return resp.json()

def send_interactive_card(chat_id, card, token):
    """发送交互式卡片消息"""
    return send_message(chat_id, "interactive", card, token)

def send_text_message(chat_id, text, token):
    """发送文本消息"""
    return send_message(chat_id, "text", {"text": text}, token)

def test_connection():
    """测试飞书连接"""
    if not FEISHU_APP_SECRET:
        print("❌ FEISHU_APP_SECRET 未配置")
        return False
    
    token = get_tenant_token()
    if not token:
        print("❌ 获取 token 失败")
        return False
    
    chats = get_bot_chats(token)
    if not chats:
        print("⚠️ 机器人未加入任何群聊")
        return False
    
    print(f"✅ 飞书连接成功！机器人加入了 {len(chats)} 个群聊")
    for chat in chats[:5]:
        print(f"  - {chat.get('name', '未知')} ({chat.get('chat_id', '')})")
    return True

if __name__ == "__main__":
    print("📱 飞书 App Bot 连接测试")
    print(f"App ID: {FEISHU_APP_ID}")
    print(f"App Secret: {'*' * 8} (已配置)" if FEISHU_APP_SECRET else "❌ 未配置")
    print()
    test_connection()
