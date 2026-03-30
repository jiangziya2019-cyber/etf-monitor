---
name: tushare-pro
description: 统一的 Tushare Pro 金融数据技能 - 整合 ETF/指数/期货/美股/宏观数据，提供实时行情 + 历史数据 + 资金流向全方位服务
---

# Tushare Pro 统一技能 v1.0

**创建时间**: 2026-03-30  
**整合自**: tushare + tushare-finance-data + tushare_data.py + tushare_realtime_data.py  
**Token**: 25,100 积分 (完全数据接口)

---

## 📊 技能概述

本技能是**统一的 Tushare Pro 数据接口**，整合了所有金融数据获取功能。

**核心能力**:
- ✅ ETF 基础信息/实时行情/份额规模
- ✅ 指数实时日线/分钟数据/技术指标
- ✅ 全球主要指数实时监控（美股/港股/期货）
- ✅ 行业/概念资金流向
- ✅ 宏观经济数据（GDP/CPI/PMI）
- ✅ 财经新闻快讯
- ✅ 自动重试 + 降级机制
- ✅ 数据缓存（3 分钟）

---

## 🎯 触发词

当用户提到以下关键词时使用此技能：
- "tushare"、"财经数据"、"金融数据"
- "ETF 数据"、"指数数据"、"期货数据"
- "美股行情"、"实时行情"、"资金流向"
- "查询 XXX 股票"、"XXX 代码"
- "上午市场分析"、"盘前准备"

---

## 📁 模块结构

```
tushare-pro/
├── SKILL.md              # 技能文档
├── lib/
│   ├── __init__.py       # 初始化
│   ├── base.py           # 通用接口（重试/降级/缓存）
│   ├── realtime.py       # 实时行情（ETF/指数/期货）
│   ├── etf.py            # ETF 专题
│   ├── index.py          # 指数专题
│   ├── global.py         # 全球市场
│   ├── moneyflow.py      # 资金流向
│   └── macro.py          # 宏观经济
└── scripts/
    ├── example_usage.py  # 使用示例
    └── test_all.py       # 测试脚本
```

---

## 🔧 核心配置

### Token 管理
```python
TUSHARE_TOKEN = "7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75"
# 25,100 积分 - 完全数据接口
```

### 重试机制
```python
# 所有接口自动重试 3 次，间隔 2 秒
for retry in range(3):
    data = get_tushare_data(api_name, **params)
    if data:
        break
    time.sleep(2)
```

### 降级策略
```
Tushare Pro (主数据源)
  ↓ 失败
akshare (备用数据源)
  ↓ 失败
缓存数据 (3 分钟缓存)
  ↓ 失败
明确告知老板"数据获取失败"
```

---

## 📋 接口清单

### ETF 相关

| 接口 | 函数 | 文档 | 用途 |
|------|------|------|------|
| etf_basic | get_etf_basic() | doc_385 | ETF 基础信息 |
| rt_etf_k | get_etf_realtime_daily() | doc_400 | ETF 实时日线 |
| rt_min | get_etf_realtime_minute() | doc_416 | ETF 实时分钟 |
| etf_share_size | get_etf_share_size() | doc_408 | ETF 份额规模 |
| fund_daily | get_fund_daily() | - | ETF 日线历史 |

### 指数相关

| 接口 | 函数 | 文档 | 用途 |
|------|------|------|------|
| rt_idx_k | get_index_realtime_daily() | doc_403 | 指数实时日线 |
| rt_idx_min | get_index_realtime_minute() | doc_420 | 指数实时分钟 |
| idx_techfactor | get_index_techfactor() | doc_358 | 指数技术指标 |
| index_dailybasic | get_index_valuation() | doc_385 | 指数估值 |

### 全球市场

| 接口 | 函数 | 文档 | 用途 |
|------|------|------|------|
| us_daily | get_us_daily() | doc_254 | 美股日线 |
| index_global | get_global_index() | doc_211 | 全球指数 |
| hk_daily | get_hk_daily() | doc_224 | 港股日线 |
| rt_fut_min | get_futures_realtime() | doc_340 | 期货实时分钟 |

### 资金流向

| 接口 | 函数 | 文档 | 用途 |
|------|------|------|------|
| moneyflow_ind_dc | get_industry_moneyflow() | doc_344 | 行业资金流 |
| moneyflow | get_stock_moneyflow() | doc_154 | 个股资金流 |

### 宏观经济

| 接口 | 函数 | 文档 | 用途 |
|------|------|------|------|
| cn_cpi | get_cpi() | doc_228 | CPI 数据 |
| cn_pmi | get_pmi() | doc_325 | PMI 数据 |
| cn_gdp | get_gdp() | doc_227 | GDP 数据 |
| news | get_news() | doc_143 | 财经新闻 |

---

## 💡 使用示例

### 示例 1: 获取 ETF 实时行情
```python
from tushare_pro.lib import realtime

# 获取沪深 300ETF 实时日线
data = realtime.get_etf_realtime_daily(['510300.SH'])
print(data)
```

### 示例 2: 获取美股数据
```python
from tushare_pro.lib import global_market

# 获取道琼斯指数
data = global_market.get_us_daily(['DJI', 'SPX', 'IXIC'])
print(data)
```

### 示例 3: 获取行业资金流
```python
from tushare_pro.lib import moneyflow

# 获取行业资金流向
data = moneyflow.get_industry_moneyflow(trade_date='20260330')
print(data)
```

### 示例 4: 上午市场分析
```python
from tushare_pro import morning_analysis

# 执行完整分析
report = morning_analysis.generate_report()
print(report)
```

---

## 🔄 相关技能/工作流

以下技能和工作流都使用本技能获取数据：

### 技能
- morning-analysis (上午市场分析)
- finance-data (财经数据查询)
- etf-fusion-screening (ETF 融合筛选)
- china-stock-analysis (A 股价值分析)

### 工作流
- 8:30 盘前准备
- 10:30 操作建议
- **14:00 上午市场分析** ⭐
- 14:45 盘中数据
- 16:00 盘后总结
- 21:00 晚间总结
- ETF 智能触发器 (15 分钟)

### 脚本
- enhanced_morning_analysis.py
- etf_smart_monitor_v2.py
- tushare_realtime_data.py (已整合)

---

## 📊 数据源优先级

```
1. Tushare Pro (主数据源) ← 本技能
   ↓ 失败时自动降级
2. akshare (备用数据源)
   ↓ 失败时自动降级
3. 缓存数据 (3 分钟)
   ↓ 失败时
4. 明确告知老板"数据获取失败"
```

---

## ⚠️ 注意事项

1. **数据时效性**
   - 美股数据：T+1（隔夜收盘）
   - 期货数据：仅在交易时间有实时数据
   - 行业资金流：每日盘后更新
   - ETF 行情：实时秒级

2. **交易时间**
   - A 股：9:30-11:30, 13:00-15:00
   - 期货：9:00-11:30, 13:30-15:00 (部分有夜盘)
   - 美股：北京时间 21:30-次日 4:00

3. **周末/节假日**
   - 周末无交易数据
   - 自动读取缓存或明确告知

---

## 📝 版本历史

- **v1.0** (2026-03-30): 统一整合版
  - 整合 tushare + tushare-finance-data
  - 统一 Token 管理
  - 统一重试/降级机制
  - 模块化设计

---

## 🔗 相关文档

- [Tushare Pro 官方文档](https://tushare.pro/document/2)
- [ETF 实时分钟接口](https://tushare.pro/document/2?doc_id=416)
- [申万实时行情接口](https://tushare.pro/document/2?doc_id=417)
- [行业资金流接口](https://tushare.pro/document/2?doc_id=344)

---

**投资有风险，数据仅供参考**
