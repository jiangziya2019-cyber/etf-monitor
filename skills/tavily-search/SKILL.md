# Tavily Search Skill v1.0

## 描述
AI 优化的实时新闻搜索引擎。用于获取特朗普动态、财经新闻、市场情报等实时信息。

## 触发条件
当用户提到以下关键词时使用此技能：
- "搜索新闻"、"实时新闻"、"最新新闻"
- "特朗普"、"Trump"、"特朗普新闻"
- "搜索"、"查找"、"查询"
- "市场情报"、"财经资讯"

## 核心能力

### 1. 搜索能力

| 功能 | 说明 | 状态 |
|------|------|------|
| **实时新闻搜索** | 搜索最新新闻 | ✅ 可用 |
| **AI 优化结果** | 智能排序相关度 | ✅ 可用 |
| **多源聚合** | 聚合多家媒体 | ✅ 可用 |
| **中文支持** | 支持中文搜索 | ✅ 可用 |

### 2. 数据源

| 类型 | 媒体源 | 更新频率 |
|------|--------|---------|
| **财经新闻** | 路透、彭博、财联社 | 实时 |
| **科技新闻** | TechCrunch、The Verge | 实时 |
| **综合新闻** | CNN、BBC、新华社 | 实时 |
| **社交媒体** | Twitter、Reddit | 实时 |

### 3. 免费额度

| 项目 | 额度 | 说明 |
|------|------|------|
| **每月搜索** | 1000 次 | 免费 |
| **每次结果** | 5-10 条 | 可配置 |
| **每天可用** | 约 33 次 | 平均分配 |
| **搜索深度** | basic/advanced | basic 更快 |

## 使用方法

### 快速调用
```bash
python3 /home/admin/openclaw/workspace/tavily_search.py --query "特朗普 关税"
```

### API 调用
```python
import requests

TAVILY_API_KEY = "tvly-dev-xxx"
url = "https://api.tavily.com/search"

payload = {
    "api_key": TAVILY_API_KEY,
    "query": "Trump tariff China",
    "search_depth": "basic",
    "max_results": 5
}

resp = requests.post(url, json=payload)
results = resp.json()["results"]
```

### 输出格式
```json
{
  "results": [
    {
      "title": "新闻标题",
      "url": "新闻链接",
      "content": "摘要内容",
      "published_date": "发布时间"
    }
  ]
}
```

## 搜索场景

### 场景 1: 特朗普动态监控
**查询**: "Trump Twitter X post today"
**频率**: 每 3 小时
**用途**: 特朗普因子监控

### 场景 2: 财经新闻搜索
**查询**: "Fed interest rate decision"
**频率**: 按需
**用途**: 美联储政策分析

### 场景 3: 市场情报
**查询**: "半导体 行业 最新动态"
**频率**: 按需
**用途**: 行业分析

## 相关文件

| 文件 | 功能 |
|------|------|
| `tavily_search.py` | 搜索核心模块 |
| `trump_factor_monitor_v2.py` | 特朗普监控 |
| `.env` | API Key 配置 |
| `tavily_config.json` | 配置文件 |

## 注意事项

1. **额度管理**
   - 每月 1000 次免费
   - 建议每 3 小时搜索一次
   - 避免频繁调用

2. **搜索优化**
   - 使用具体关键词
   - 添加时间限定（如"today"、"2026"）
   - 使用英文搜索更准确

3. **结果处理**
   - 验证新闻来源
   - 交叉验证重要信息
   - 注意发布时间

## 版本历史

- **v1.0** (2026-03-29): 初始版本
  - Tavily API 集成
  - 特朗普监控应用
  - 额度管理优化

## 风险提示

⚠️ 投资有风险，决策需谨慎
- 新闻内容仅供参考
- 需交叉验证重要信息
- 注意假新闻风险
