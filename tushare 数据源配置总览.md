# Tushare Pro 金融数据源配置总览

**配置完成时间**: 2026-03-27 23:51  
**Token**: `7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75`  
**积分**: 25,100 分（完全数据接口，¥60,000+/年）

---

## 📋 配置完成清单

### ✅ 已完成的任务

| 任务 | 状态 | 文件路径 |
|------|------|---------|
| **Tushare Skill 创建** | ✅ 完成 | `/home/admin/openclaw/workspace/skills/tushare-finance-data/SKILL.md` |
| **晚间报告格式规范** | ✅ 完成 | `/home/admin/openclaw/workspace/晚间报告格式规范.md` |
| **数据获取模块更新** | ✅ 完成 | `/home/admin/openclaw/workspace/tushare_data.py` |
| **MEMORY.md 更新** | ✅ 完成 | `/home/admin/openclaw/workspace/MEMORY.md` |
| **完全接口配置文档** | ✅ 完成 | `/home/admin/openclaw/workspace/tushare 完全接口配置.md` |

---

## 🎯 数据源配置（所有金融数据）

### 主数据源：Tushare Pro
```
Token: 7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75
积分：25,100 分
权限：完全数据接口（¥60,000+/年）
```

### 数据源优先级
```
Tushare Pro (主数据源)
  ↓ (失败时降级)
akshare (备用数据源)
  ↓ (失败时降级)
缓存数据 (3 分钟缓存)
```

### 应用范围
**所有金融数据获取事项均使用 Tushare Pro 作为主数据源**：
- ✅ 晚间总结报告
- ✅ 盘前准备报告
- ✅ 盘中监控
- ✅ 持仓分析
- ✅ 板块分析
- ✅ ETF 分析
- ✅ 期货监控
- ✅ 国际指数监控

---

## 📊 已配置接口清单

### A 股市场
| 接口 | 函数 | 状态 |
|------|------|------|
| `index_daily` | `pro.index_daily()` | ✅ 完全可用 |
| `daily` | `ts.pro_bar()` | ✅ 完全可用 |
| `stock_min` | `ts.pro_bar(freq='1min')` | ✅ 241 条/日 |

### 港股市场
| 接口 | 函数 | 状态 |
|------|------|------|
| `hk_daily` | `pro.hk_daily()` | ✅ 完全可用 |
| `rt_hk_k` | `pro.rt_hk_k()` | ✅ 完全可用 |

### 国际市场
| 接口 | 函数 | 状态 |
|------|------|------|
| `index_global` | `pro.index_global()` | ✅ 完全可用 |

**支持的指数代码**:
```
HSI        - 恒生指数 ✅
N225       - 日经 225 ✅
DJI        - 道琼斯
SPX        - 标普 500
IXIC       - 纳斯达克
FTSE       - 富时 100
GDAXI      - 德国 DAX
```

### 商品期货
| 接口 | 函数 | 状态 |
|------|------|------|
| `fut_daily` | `pro.fut_daily()` | ✅ 完全可用 |

**期货代码**:
```
AU.SHF     - 沪金主力 ✅
SC.INE     - SC 原油 ✅
AUL.SHF    - 沪金主连 ✅
```

### ETF/基金
| 接口 | 函数 | 状态 |
|------|------|------|
| `fund_daily` | `ts.pro_bar(asset='FD')` | ✅ 完全可用 |
| `fund_min` | `ts.pro_bar(asset='FD', freq='1min')` | ✅ 241 条/日 |

### 板块数据
| 接口 | 函数 | 状态 |
|------|------|------|
| `dc_daily` | `pro.dc_daily()` | ✅ 496 个板块 |

### 财务数据
| 接口 | 函数 | 状态 |
|------|------|------|
| `income` | `pro.income()` | ✅ 完全可用 |
| `balancesheet` | `pro.balancesheet()` | ✅ 完全可用 |
| `cashflow` | `pro.cashflow()` | ✅ 完全可用 |

---

## 🛠️ 技术实现

### 数据获取模块
**文件**: `/home/admin/openclaw/workspace/tushare_data.py`

**核心函数**:
```python
# A 股
get_stock_daily(ts_code, start_date, end_date, adj=None)
get_stock_min(ts_code, trade_date, freq='1min')
get_index_daily(ts_code, start_date, end_date)
get_index_min(ts_code, trade_date, freq='1min')

# ETF
get_fund_daily(ts_code, start_date, end_date)
get_fund_min(ts_code, trade_date, freq='1min')

# 港股
get_hk_daily_pro(ts_code, start_date, end_date)

# 期货
get_futures_daily_pro(ts_code, start_date, end_date)

# 国际指数
get_index_global(ts_code, start_date, end_date)

# 板块
get_dc_daily(trade_date)
```

### Skill 文档
**文件**: `/home/admin/openclaw/workspace/skills/tushare-finance-data/SKILL.md`

**内容**:
- 技能描述
- 核心能力
- 接口调用代码
- 使用场景
- 错误处理
- 测试验证

### 晚间报告格式规范
**文件**: `/home/admin/openclaw/workspace/晚间报告格式规范.md`

**内容**:
- 报告结构（10 个部分）
- 数据获取规范
- 质量检查清单
- 数据源优先级

---

## 📝 使用示例

### 获取晚间报告数据
```python
import tushare as ts

ts.set_token("7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75")
pro = ts.pro_api()

# A 股指数
sh_index = pro.index_daily(ts_code='000001.SH', start_date='20260327', end_date='20260327')

# 恒生指数
hsi = pro.index_global(ts_code='HSI', start_date='20260327', end_date='20260327')

# 商品期货
au = pro.fut_daily(ts_code='AU.SHF', start_date='20260327', end_date='20260327')

# 板块涨跌
sectors = pro.dc_daily(trade_date='20260327')

# ETF
etf = ts.pro_bar(ts_code='510300.SH', asset='FD', start_date='20260327', end_date='20260327')
```

### 从 tushare_data 模块获取
```python
from tushare_data import (
    get_index_daily,
    get_index_global,
    get_futures_daily_pro,
    get_fund_daily,
    get_dc_daily
)

# 获取上证指数
sh = get_index_daily('000001.SH', '20260327', '20260327')

# 获取恒生指数
hsi = get_index_global('HSI', '20260327', '20260327')

# 获取沪金主力
au = get_futures_daily_pro('AU.SHF', '20260327', '20260327')
```

---

## 🎯 质量保证

### 数据验证要求
1. ✅ 收盘点位：必须有具体数值
2. ✅ 涨跌额：必须有具体数值（点/元）
3. ✅ 涨跌幅：必须有百分比数值
4. ✅ 板块名称：必须完整列出前 10 名
5. ✅ 持仓数据：必须包含所有持仓 ETF

### 质量检查清单
发送晚间报告前必须检查：
- [ ] A 股数据包含收盘点位 + 涨跌额 + 涨跌幅
- [ ] 港股包含恒生指数收盘点位 + 涨跌幅
- [ ] 期货包含收盘价 + 结算价 + 涨跌幅
- [ ] 板块涨跌前十完整列出（10 个名称 + 涨跌幅）
- [ ] 持仓明细包含所有 ETF
- [ ] 持仓分析包含盈利/亏损分析
- [ ] 操作建议明确
- [ ] 数据源说明完整（100% Tushare Pro）

---

## 📚 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **Tushare Skill** | `skills/tushare-finance-data/SKILL.md` | 数据获取技能文档 |
| **晚间报告格式** | `晚间报告格式规范.md` | 报告格式规范 |
| **数据获取模块** | `tushare_data.py` | Python 数据获取代码 |
| **完全接口配置** | `tushare 完全接口配置.md` | 接口购买记录 |
| **MEMORY.md** | `MEMORY.md` | 长期记忆配置 |

---

## 🔄 维护计划

### 定期检查
- [ ] 每周检查 Tushare 积分余额
- [ ] 每月验证所有接口可用性
- [ ] 每季度更新接口文档

### 升级信号
- ⚠️ 积分不足 6000 分
- ⚠️ 接口权限变更
- ⚠️ Token 过期或失效

---

**配置完成时间**: 2026-03-27 23:51  
**维护者**: 金助手  
**下次检查**: 2026-04-03
