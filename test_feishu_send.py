#!/usr/bin/env python3
import json
import requests

# 从配置获取（硬编码，因为环境变量未设置）
APP_ID = "cli_a9493d702278dbb7"
APP_SECRET = "7dXh0bGzQl5RvK3N"  # 需要老板提供真实的 appSecret
API_BASE = "https://open.feishu.cn/open-apis"

# 1. 获取 tenant_access_token
def get_tenant_token():
    resp = requests.post(f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET})
    data = resp.json()
    return data.get("tenant_access_token")

# 2. 获取机器人所在的聊天列表
def list_chats(token):
    resp = requests.get(f"{API_BASE}/im/v1/chats?page_size=20",
        headers={"Authorization": f"Bearer {token}"})
    return resp.json()

if __name__ == "__main__":
    print("⚠️ 需要老板提供飞书 App Secret")
    print(f"当前配置的 App ID: {APP_ID}")
    print("\n获取方式：")
    print("1. 飞书开放平台 → 我的企业 → 凭证与基础信息")
    print("2. 复制 App Secret")
    print("3. 添加到环境变量或配置")
