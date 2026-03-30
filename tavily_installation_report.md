# Tavily Search Skill 安装报告

**状态**: ✅ **已完成并测试通过**  
**时间**: 2026-03-27 18:10  
**版本**: v1.0

---

## 一、安装状态

### ✅ 已完成

| 项目 | 状态 | 位置 |
|------|------|------|
| **技能目录** | ✅ 已创建 | `~/.openclaw/skills/tavily-search/` |
| **SKILL.md** | ✅ 已配置 | 2.0KB |
| **API Key** | ✅ 已配置 | `tvly-dev-1OAole-...` |
| **环境变量** | ✅ 已设置 | 当前会话 + .env 文件 |
| **功能测试** | ✅ 通过 | 搜索成功返回 5 条结果 |

---

## 二、API 配置

### API Key

```
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
```

**类型**: 开发环境 (dev)  
**额度**: 免费层 1000 次/月

### 设置方式

**方式 1**: 当前会话
```bash
export TAVILY_API_KEY="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"
```

**方式 2**: 持久化到 .env
```bash
TAVILY_API_KEY=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
```

---

## 三、测试结果

### 测试查询

**Query**: "ETF 市场新闻 2026"

**结果**: ✅ 成功返回 5 条结果

### 返回数据

**AI 摘要**：
> The ETF market in 2026 is expected to grow significantly, with global assets under management surpassing 19 trillion USD. Major markets like the US and China continue to dominate...

**Top 结果**：

| # | 标题 | 来源 | 评分 |
|---|------|------|------|
| 1 | 2026 年基金公司蓄势出新，ETF 新品多点开花 | 中国基金报 | 0.93 |
| 2 | 上交所 ETF 行业发展报告（2026）发布 | 新华网 | 0.93 |
| 3 | 聚焦 ETF 市场 | 2026 年境外 ETF 做市商扩大中国内地业务版图 | Bloomberg China | 0.90 |
| 4 | 2025–2026 美國與台灣 ETF 市場洞察 | 新光證券 (PDF) | 0.88 |
| 5 | 【展望 2026 系列十一】2026 資產配置：ETF 五大關鍵 QA！ | MacroMicro | 0.87 |

---

## 四、使用示例

### 基本搜索

```python
import requests

TAVILY_API_KEY = "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"

response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": TAVILY_API_KEY,
        "query": "半导体行业最新政策 2026",
        "max_results": 5
    }
)

results = response.json()
```

### 高级搜索

```python
# 深度搜索 + 包含答案
response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": TAVILY_API_KEY,
        "query": "美联储利率决策 2026 年 3 月",
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 10,
        "days": 7  # 最近 7 天
    }
)
```

### 领域过滤

```python
# 只搜索特定域名
response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": TAVILY_API_KEY,
        "query": "新能源 ETF 分析",
        "include_domains": ["eastmoney.com", "sina.com.cn"],
        "max_results": 5
    }
)
```

---

## 五、适用场景

### ✅ 推荐使用

- **实时信息**：最新市场新闻、政策变化
- **数据验证**：核实事实、查找来源
- **研究分析**：收集多方观点、深度研究
- **链接发现**：查找相关网站、文档
- **竞争情报**：行业动态、竞品信息

### 📊 投资分析场景

| 场景 | 示例查询 |
|------|----------|
| **市场新闻** | "ETF 市场最新动态 2026" |
| **政策解读** | "半导体行业政策 2026 年" |
| **公司调研** | "贵州茅台 2025 年报分析" |
| **行业研究** | "新能源产业链发展趋势" |
| **宏观数据** | "中国 GDP 2026 Q1 预测" |
| **竞品分析** | "华夏基金 vs 易方达 ETF 规模" |

---

## 六、参数说明

### 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索查询词 |
| `api_key` | string | 必填 | API Key |
| `search_depth` | string | "basic" | basic/advanced |
| `max_results` | int | 5 | 结果数量 (1-20) |
| `include_answer` | bool | False | 包含 AI 摘要 |

### 高级参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `days` | int | 最近 N 天的内容 |
| `include_domains` | list | 只包含特定域名 |
| `exclude_domains` | list | 排除特定域名 |
| `include_images` | bool | 包含图片结果 |

---

## 七、费率说明

### 免费层 (Dev Key)

- **额度**: 1000 次搜索/月
- **速度**: 标准
- **功能**: 基础搜索

### 付费层

| 层级 | 价格 | 额度 | 功能 |
|------|------|------|------|
| **Starter** | $29/月 | 10,000 次 | 基础 + 高级搜索 |
| **Pro** | $99/月 | 100,000 次 | 全部功能 |
| **Enterprise** | 定制 | 无限 | 定制支持 |

---

## 八、与其他数据源对比

| 数据源 | 优势 | 劣势 | 用途 |
|--------|------|------|------|
| **Tavily** | AI 优化、实时、带摘要 | 有额度限制 | 网络搜索 |
| **akshare** | 免费、全市场 | 偶尔不稳定 | 行情数据 |
| **Tushare** | 稳定、权限高 | 有延迟 | 财务数据 |
| **东方财富** | 权威、实时 | 查询慢 | 补充数据 |

---

## 九、最佳实践

### 1. 查询优化

**好**：
```
"2026 年 3 月 ETF 市场规模 增长"
"半导体行业政策 中国 最新"
```

**避免**：
```
"ETF" (太宽泛)
"最新的关于 ETF 市场的一些新闻和数据分析" (太冗长)
```

### 2. 结果处理

```python
# 过滤低分结果
results = [r for r in data['results'] if r.get('score', 0) > 0.8]

# 提取关键信息
for r in results:
    title = r['title']
    url = r['url']
    content = r['content'][:200]  # 前 200 字
```

### 3. 错误处理

```python
try:
    response = requests.post(url, json=data, timeout=15)
    response.raise_for_status()
    results = response.json()
except requests.exceptions.Timeout:
    print("搜索超时")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("超出额度限制")
```

---

## 十、文件清单

```
~/.openclaw/skills/tavily-search/
└── SKILL.md          # ✅ 技能定义 (2.0KB)

/home/admin/openclaw/workspace/
├── .env              # ✅ API Key 已配置
└── tavily_installation_report.md  # ✅ 本报告
```

---

## 十一、总结

### ✅ 完成状态

- ✅ Skill 已安装
- ✅ API Key 已配置
- ✅ 功能测试通过
- ✅ 文档已完善

### 🎯 使用建议

1. **合理使用额度**: 1000 次/月，避免浪费
2. **优化查询**: 精准查询词，提高结果质量
3. **结合其他数据源**: Tavily + akshare + Tushare
4. **缓存结果**: 相同查询避免重复请求

### 🚀 下一步

- ⏳ 在实际场景中应用
- ⏳ 监控使用额度
- ⏳ 根据需求考虑升级

---

**报告人**: 金助手  
**时间**: 2026-03-27 18:10  
**状态**: ✅ Tavily Search 已就绪，可立即使用

---

*注：Tavily API Key 已配置并测试通过，可用于实时网络搜索。*
