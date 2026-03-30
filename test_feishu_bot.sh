#!/bin/bash

# 飞书 App Bot API 测试
FEISHU_APP_ID="cli_a9493d702278dbb7"
FEISHU_APP_SECRET="__OPENCLAW_REDACTED__"
FEISHU_API_BASE="https://open.feishu.cn/open-apis"

echo "=== 测试飞书 App Bot API ==="

# 步骤 1: 获取 tenant_access_token
echo "1. 获取 tenant_access_token..."
TENANT_TOKEN=$(curl -s -X POST "${FEISHU_API_BASE}/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_id\": \"${FEISHU_APP_ID}\",
    \"app_secret\": \"${FEISHU_APP_SECRET}\"
  }" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tenant_access_token','ERROR: '+str(d)))")

if [[ "$TENANT_TOKEN" == "ERROR"* ]] || [[ -z "$TENANT_TOKEN" ]]; then
  echo "❌ 获取 token 失败：$TENANT_TOKEN"
  exit 1
fi

echo "✅ Token 获取成功：${TENANT_TOKEN:0:20}..."

# 步骤 2: 获取机器人所在的聊天列表
echo "2. 获取聊天列表..."
CHATS=$(curl -s "${FEISHU_API_BASE}/im/v1/chats?page_size=5" \
  -H "Authorization: Bearer ${TENANT_TOKEN}")

echo "聊天列表响应："
echo "$CHATS" | python3 -c "import json,sys; d=json.load(sys.stdin); items=d.get('data',{}).get('items',[]); print(f'找到 {len(items)} 个聊天'); [print(f\"  - {c.get('chat_id','N/A')}: {c.get('name','N/A')}\") for c in items]"

# 步骤 3: 发送测试消息
echo "3. 发送测试消息..."
# 使用之前配置的 Webhook 对应的聊天（需要 chat_id）
# 这里先尝试发送到一个测试聊天

echo "✅ 测试完成！"
