#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书私聊配置工具
帮助获取老板的飞书 user_id
"""

import requests
import json

API_BASE = "https://open.feishu.cn/open-apis"
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "3wh8D1UGuUN9v8B8NyqlfbmIcHgzGfdI"

def get_tenant_token():
    resp = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("tenant_access_token")
    return None

def get_user_by_phone(phone):
    """通过手机号获取用户信息"""
    token = get_tenant_token()
    if not token:
        return None
    
    resp = requests.get(
        f"{API_BASE}/contact/v3/users?user_id_type=open_id",
        headers={"Authorization": f"Bearer {token}"},
        params={"mobile": phone, "user_id_type": "open_id"},
        timeout=10
    )
    data = resp.json()
    print(f"API 响应：{json.dumps(data, indent=2, ensure_ascii=False)}")
    if data.get("code") == 0 and data.get("data"):
        user = data["data"]["user"]
        return {
            "user_id": user.get("user_id"),
            "open_id": user.get("open_id"),
            "union_id": user.get("union_id"),
            "name": user.get("name"),
            "en_name": user.get("en_name"),
            "mobile": user.get("mobile")
        }
    return None

def get_bot_info():
    """获取机器人信息"""
    token = get_tenant_token()
    if not token:
        return None
    
    resp = requests.get(
        f"{API_BASE}/auth/v3/app_access_token/info",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    print(f"Bot API 响应状态码：{resp.status_code}")
    print(f"Bot API 响应内容：{resp.text[:500]}")
    return resp.json()

if __name__ == "__main__":
    print("=" * 60)
    print("飞书私聊配置工具")
    print("=" * 60)
    
    # 测试 token
    token = get_tenant_token()
    print(f"\n1. Token 获取：{'✅ 成功' if token else '❌ 失败'}")
    if token:
        print(f"   Token: {token[:30]}...")
    
    # 获取机器人信息
    print("\n2. 机器人信息：")
    bot_info = get_bot_info()
    if bot_info:
        print(f"   {json.dumps(bot_info, indent=2, ensure_ascii=False)}")
    
    # 通过手机号获取用户 ID
    print("\n3. 获取老板的飞书用户 ID")
    print("   请输入老板的飞书绑定手机号（格式：+8613800138000 或 13800138000）")
    phone = input("   手机号：").strip()
    
    if phone:
        user_info = get_user_by_phone(phone)
        if user_info:
            print("\n✅ 找到用户！")
            print(f"   姓名：{user_info['name']}")
            print(f"   User ID: {user_info['user_id']}")
            print(f"   Open ID: {user_info['open_id']}")
            print(f"   Union ID: {user_info['union_id']}")
            print(f"\n📝 请将以下配置添加到 etf_trigger_monitor.py:")
            print(f"   FEISHU_USER_ID = \"{user_info['open_id']}\"")
            print(f"   FEISHU_RECEIVE_ID_TYPE = \"open_id\"")
        else:
            print("\n❌ 未找到用户，请检查手机号是否正确")
            print("   或者老板需要先关注/添加这个机器人")
