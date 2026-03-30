# 🔧 回测引擎 Bug 分析报告

**分析时间**: 2026-03-28 17:42  
**问题**: 初始资金¥1,000,000 → 最终价值¥23（-100% 亏损）

---

## 一、发现的 Bug

### Bug 1: 交易成本重复计算 ❌

**问题代码**:
```python
# 买入时
target_value = self.capital * target_weight / (1 - TRANSACTION_COST)  # 第 1 次计算成本
# ...
cost = shares * price * (1 + TRANSACTION_COST)  # 第 2 次计算成本
self.capital -= cost
```

**问题分析**:
```
假设：capital=100 万，target_weight=0.2（5 只 ETF），TRANSACTION_COST=0.001

第 1 次成本调整:
target_value = 100 万 * 0.2 / (1 - 0.001) = 200,200 元

第 2 次成本调整:
假设 price=4 元，shares = 200,200/4 = 50,050 份
cost = 50,050 * 4 * (1 + 0.001) = 200,400 元

实际扣除：200,400 元
但 target_value 已考虑成本，导致重复计算！
```

**修复**:
```python
# 方案：只在买入时计算一次成本
target_value = self.capital * target_weight  # 不预先调整
price = historical_data[code][date]['close']
shares = int(target_value / price)  # 计算份额
cost = shares * price * (1 + TRANSACTION_COST)  # 买入时计算成本
self.capital -= cost
```

---

### Bug 2: 卖出逻辑问题 ⚠️

**问题代码**:
```python
# 卖出
self.capital += shares * price * (1 - TRANSACTION_COST)
```

**问题分析**:
- 卖出时扣除交易成本是正确的
- 但如果价格数据缺失（price=1.0），会导致资金大幅缩水

**修复**:
```python
# 确保价格数据存在
if price < 0.5:  # 异常低价
    log_message(f"⚠️ {code} 价格异常：{price}，跳过卖出")
    continue
```

---

### Bug 3: 资金分配不完整 ⚠️

**问题**:
```python
target_weight = 1.0 / len(target_etfs)  # 假设 5 只 ETF，每只 20%
# 但如果 capital 在过程中变化...
```

**问题分析**:
- 先卖出 ETF → capital 增加
- 再买入 ETF → 使用更新后的 capital
- 逻辑正确，但需要确保卖出和买入使用同一时点的价格

---

## 二、修复方案

### 完整修复代码

```python
def execute_rebalance(self, date: str, target_etfs: List[str], historical_data: Dict):
    """执行调仓（修复版）"""
    
    # ========== 第 1 步：卖出 ==========
    sell_proceeds = 0  # 卖出所得
    
    for code in list(self.positions.keys()):
        if code not in target_etfs:
            shares = self.positions[code]
            price = self.get_price(code, date, historical_data)
            
            if price and price > 0.5:  # 价格有效
                proceeds = shares * price * (1 - TRANSACTION_COST)
                sell_proceeds += proceeds
                del self.positions[code]
                self.trades.append({
                    'date': date,
                    'action': 'sell',
                    'code': code,
                    'shares': shares,
                    'price': price,
                    'proceeds': proceeds
                })
    
    # 更新资金（卖出后）
    self.capital += sell_proceeds
    
    # ========== 第 2 步：买入 ==========
    if not target_etfs:
        return
    
    # 计算每只 ETF 的目标金额（使用卖出后的总资金）
    target_weight = 1.0 / len(target_etfs)
    target_value_per_etf = self.capital * target_weight
    
    for code in target_etfs:
        price = self.get_price(code, date, historical_data)
        
        if not price or price < 0.5:
            continue
        
        # 计算可买份额
        shares = int(target_value_per_etf / price)
        
        if shares > 0:
            cost = shares * price * (1 + TRANSACTION_COST)
            self.positions[code] = shares
            self.capital -= cost  # 扣除买入成本
            self.trades.append({
                'date': date,
                'action': 'buy',
                'code': code,
                'shares': shares,
                'price': price,
                'cost': cost
            })
```

---

## 三、测试验证

### 修复前
```
初始资金：¥1,000,000
最终价值：¥23
总收益：-100%
```

### 修复后（预期）
```
初始资金：¥1,000,000
最终价值：¥1,000,000 - ¥1,500,000（取决于市场表现）
总收益：0% - 50%
```

---

## 四、其他改进

### 1. 添加调试日志
```python
log_message(f"  调仓日 {date}: 卖出¥{sell_proceeds:,.0f}, 买入{len(target_etfs)}只 ETF")
log_message(f"  资金变化：¥{old_capital:,.0f} → ¥{self.capital:,.0f}")
```

### 2. 添加资金验证
```python
def validate_capital(self):
    """验证资金不为负"""
    if self.capital < 0:
        log_message(f"❌ 资金为负：¥{self.capital:,.2f}")
        self.capital = 0
```

### 3. 添加交易记录统计
```python
def print_trade_summary(self):
    """打印交易汇总"""
    total_cost = sum(t.get('cost', 0) for t in self.trades if t['action'] == 'buy')
    total_proceeds = sum(t.get('proceeds', 0) for t in self.trades if t['action'] == 'sell')
    log_message(f"交易汇总：买入¥{total_cost:,.0f}, 卖出¥{total_proceeds:,.0f}")
```

---

**修复优先级**: 🔴 高（立即修复）  
**预计修复时间**: 30 分钟  
**实盘影响**: 无（回测引擎仅用于验证）

*准备开始修复...* 🔧
