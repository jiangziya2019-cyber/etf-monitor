# Tushare Pro 数据源配置文档

**配置时间**: 2026-03-27 23:07  
**Tushare 积分**: 25,100 分 (完全数据接口)  
**Token**: `7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75`

---

## ✅ 已确认可用接口

### A 股数据
| 接口名 | 函数 | 用途 | 状态 |
|--------|------|------|------|
| `index_daily` | `pro.index_daily()` | A 股指数日线 | ✅ 可用 |
| `daily` | `pro.daily()` | A 股个股日线 | ✅ 可用 |
| `stock_basic` | `pro.stock_basic()` | A 股股票列表 | ✅ 可用 |
| `trade_cal` | `pro.trade_cal()` | 交易日历 | ✅ 可用 |

### ETF/基金
| 接口名 | 函数 | 用途 | 状态 |
|--------|------|------|------|
| `fund_daily` | `pro.fund_daily()` | ETF/基金日线 | ✅ 可用 |

### 港股
| 接口名 | 函数 | 用途 | 状态 |
|--------|------|------|------|
| `hk_daily` | `pro.hk_daily()` | 港股个股日线 | ✅ 可用 |

### 美股
| 接口名 | 函数 | 用途 | 状态 |
|--------|------|------|------|
| `us_daily` | `pro.us_daily()` | 美股个股日线 | ⚠️ 无数据 (可能非交易日) |

### 财务数据
| 接口名 | 函数 | 用途 | 状态 |
|--------|------|------|------|
| `income` | `pro.income()` | 利润表 | ✅ 可用 |
| `balancesheet` | `pro.balancesheet()` | 资产负债表 | ✅ 可用 |
| `cashflow` | `pro.cashflow()` | 现金流量表 | ✅ 可用 |

---

## ⚠️ 待确认接口

### 分钟线数据
| 接口名 | 状态 | 说明 |
|--------|------|------|
| `stk_min` | ❌ 接口名不对 | A 股分钟线 |
| `index_min` | ❌ 接口名不对 | 指数分钟线 |
| `fund_min` | ❌ 接口名不对 | ETF 分钟线 |
| `hk_min` | ❌ 接口名不对 | 港股分钟线 |

### 期货数据
| 接口名 | 状态 | 说明 |
|--------|------|------|
| `futures_daily` | ❌ 接口名不对 | 期货日线 |
| `fut_daily` | ⚠️ 无数据 | 期货日线 (可能合约代码不对) |
| `futures_main` | ❌ 接口名不对 | 期货主力合约 |

### 现货价格
| 接口名 | 状态 | 说明 |
|--------|------|------|
| `spot_price` | ❌ 接口名不对 | 现货价格 |
| `spot_price_quoted` | ❌ 接口名不对 | 报价现货 |

### 新闻/公告
| 接口名 | 状态 | 说明 |
|--------|------|------|
| `news` | ⚠️ 无数据 | 新闻资讯 (可能当日无新闻) |
| `disclosure_announce` | ❌ 接口名不对 | 公告数据 |
| `announcement` | ❌ 接口名不对 | 公告数据 |

---

## 📋 数据源优先级配置

### 主数据源：Tushare Pro
```python
# 日线数据优先使用 Tushare
- A 股指数日线：Tushare index_daily ✅
- A 股个股日线：Tushare daily ✅
- ETF 日线：Tushare fund_daily ✅
- 港股个股日线：Tushare hk_daily ✅
- 财务数据：Tushare income/balancesheet/cashflow ✅
```

### 备用数据源：akshare
```python
# Tushare 不可用时降级到 akshare
- 分钟线数据：akshare (待确认 Tushare 接口名)
- 商品期货：akshare futures_zh_daily_sina ✅
- 现货价格：akshare (待确认 Tushare 接口名)
- 新闻/公告：akshare (待确认 Tushare 接口名)
- 港股指数：akshare (Tushare 无数据)
```

---

## 🔧 使用示例

### 获取 A 股指数日线
```python
from tushare_data import get_index_daily

# 上证指数
df = get_index_daily('000001.SH', '20260325', '20260327')
print(df)
```

### 获取 ETF 日线
```python
from tushare_data import get_fund_daily

# 300ETF
df = get_fund_daily('510300.SH', '20260325', '20260327')
print(df)
```

### 获取港股日线
```python
from tushare_data import get_hk_daily

# 腾讯控股
df = get_hk_daily('00700.HK', '20260325', '20260327')
print(df)
```

### 获取财务数据
```python
from tushare_data import get_income, get_balance, get_cashflow

# 平安银行
income = get_income('000001.SZ')
balance = get_balance('000001.SZ')
cashflow = get_cashflow('000001.SZ')
```

---

## 📝 后续优化计划

### 1. 确认分钟线接口名
- 查阅 Tushare 文档确认正确接口名
- 测试 `min`、`stk_min`、`stock_min` 等变体

### 2. 确认期货接口名
- 查阅 Tushare 文档确认正确接口名
- 测试 `fut_daily`、`futures_daily` 等

### 3. 确认公告接口名
- 查阅 Tushare 文档确认正确接口名
- 测试 `disclosure_announce`、`announcement` 等

### 4. 建立数据缓存
- 避免重复调用
- 提高响应速度

### 5. 建立降级机制
- Tushare 失败自动切换 akshare
- 记录失败日志

---

## 📊 当前数据覆盖

**可用数据 (Tushare Pro)**:
- ✅ A 股全市场日线（指数 + 个股）
- ✅ ETF 日线
- ✅ 港股个股日线
- ✅ 财务数据（三张表）
- ✅ 交易日历

**备用数据 (akshare)**:
- ✅ 商品期货日线
- ✅ 分钟线数据
- ✅ 新闻/公告

---

**配置完成时间**: 2026-03-27 23:07  
**下次更新**: 确认分钟线/期货/公告接口名后
