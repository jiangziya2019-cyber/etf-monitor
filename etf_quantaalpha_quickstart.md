# ETF-QuantaAlpha 快速使用指南

## 一分钟上手

### 1. 基础运行

```bash
cd /home/admin/openclaw/workspace

# 运行智能筛选（2 轮迭代，输出 Top 15）
python3 etf_quanta_main.py --iterations 2 --top-n 15
```

**输出示例**:
```
======================================================================
ETF-QuantaAlpha 智能筛选系统
======================================================================
[数据] 加载 1917 只 ETF
[市场状态] sideways

进化迭代 #1
  Top 5 轨迹:
    1. 短期动量效应：奖励=0.0624, IC=0.080, ARR=13.4%
    2. 中期趋势延续：奖励=0.0623, IC=0.068, ARR=14.7%
    ...

观察池推荐 (Top 15)
  510300: 沪深 300ETF
    选中 3 次 | 规则：短期动量效应，中期趋势延续，低估值修复
  ...

✅ 筛选完成！
   - 观察池 ETF: 15 只
   - 使用规则：15 条
   - 市场状态：sideways
```

---

### 2. 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--iterations` | 3 | 进化迭代次数（建议 2-5） |
| `--top-n` | 15 | 输出 ETF 数量（建议 10-20） |
| `--output` | quanta_screening_result.json | 输出文件名 |

**示例**:
```bash
# 快速测试（1 轮迭代）
python3 etf_quanta_main.py --iterations 1 --top-n 10

# 深度挖掘（5 轮迭代）
python3 etf_quanta_main.py --iterations 5 --top-n 20 --output weekly_screening.json
```

---

### 3. 结果解读

**输出文件** (`quanta_screening_result.json`):
```json
{
  "timestamp": "2026-03-27T11:38:08.937713",
  "market_regime": "sideways",
  "iterations": 2,
  "total_rules": 15,
  "selected_etfs": [
    {
      "code": "510300",
      "name": "沪深 300ETF",
      "selected_by": 3,
      "rules": ["短期动量效应", "中期趋势延续", "低估值修复"],
      "price": 4.125,
      "change_pct": 0.85
    },
    ...
  ]
}
```

**关键字段**:
- `selected_by`: 被几条规则选中（越高越可靠）
- `rules`: 具体规则名称
- `market_regime`: 当前市场状态（bull/bear/sideways）

---

## 6 大筛选方向

### 1. 动量轮动 (Momentum)
- **短期动量效应**: 20 日收益率为正且加速
- **中期趋势延续**: 60 日趋势 +20 日动量配合

**适用**: 牛市、震荡市

---

### 2. 估值回归 (Value)
- **低估值修复**: PE/PB分位<30%
- **低估值 + 正动量**: 低估值且动量转正

**适用**: 熊市、震荡市

---

### 3. 资金流向 (Flow)
- **主力进场**: 资金净流入 + 高换手
- **量价齐升**: 价格上涨 + 成交量放大

**适用**: 牛市

---

### 4. 波动率目标 (Volatility)
- **低波动稳健**: 波动率<1.5%
- **波动率收缩突破**: 极低波动后可能突破

**适用**: 震荡市、熊市

---

### 5. 行业景气 (Sector)
- **行业景气轮动**: 行业加速上涨

**适用**: 牛市、震荡市

---

### 6. 跨境套利 (Arbitrage)
- **折价套利机会**: QDII 折价>2%

**适用**: 震荡市

---

## 进化机制

### 变异 (Mutation)
**触发**: 规则表现差（IC<0.05 或 回撤>12%）

**操作**:
- 放宽过滤阈值（如 PE 分位 30%→36%）
- 增加波动率过滤
- 调整排序逻辑

**示例**:
```
原始规则：低估值修复 (PE 分位<30%)
变异后：低估值修复_v2 (PE 分位<36%)
```

---

### 交叉 (Crossover)
**触发**: 两个规则表现都好

**操作**: 融合优势
```
父代 1: 动量规则（高收益）
父代 2: 估值规则（低回撤）
子代：动量 + 估值融合（高收益 + 低回撤）
```

---

## 与现有体系集成

### 场景 1: 观察池筛选

**每周一运行**:
```bash
# 生成当周观察池
python3 etf_quanta_main.py --iterations 3 --top-n 20 --output weekly_pool.json
```

**结果应用**:
- 更新观察池（15-20 只）
- 替换连续 2 周未入选品种
- 人工审核确认

---

### 场景 2: 止盈/止损智能分析

**触发时调用**:
```python
# 伪代码
if trigger_take_profit(etf):
    # 调用 QuantaAlpha 评估行业前景
    sector_score = quanta.get_sector_score(etf.sector)
    
    if sector_score > 4.0:
        return "🟡 部分止盈（行业景气好，建议保留部分）"
    else:
        return "✅ 建议执行（行业景气一般）"
```

---

### 场景 3: 轮动信号挖掘

**每月运行**:
```bash
# 全市场扫描
python3 etf_quanta_main.py --iterations 5 --top-n 50 --output monthly_scan.json
```

**分析**:
- 对比上月观察池变化
- 识别新入选行业
- 输出轮动建议

---

## 常见问题

### Q1: 为什么有些 ETF 没有名称？
**A**: 当前使用模拟数据，真实数据对接后会自动填充。

---

### Q2: 迭代次数设置多少合适？
**A**: 
- 快速测试：1-2 次
- 日常使用：3 次
- 深度挖掘：5 次（耗时较长）

---

### Q3: 选中的 ETF 数量太少/太多？
**A**: 调整 `--top-n` 参数，或修改规则阈值：
- 数量少 → 放宽阈值（如 PE 分位 30%→40%）
- 数量多 → 增加过滤条件

---

### Q4: 如何评估规则有效性？
**A**: 查看输出中的 IC/ARR/MDD 指标：
- IC > 0.06: 良好
- ARR > 15%: 优秀
- |MDD| < 10%: 稳健

---

### Q5: 数据延迟怎么办？
**A**: 当前使用缓存数据，真实数据对接后：
- akshare: 15 分钟延迟
- Tushare: 实时（需付费）
- 建议：盘后运行筛选，次日参考

---

## 下一步

### 立即可做
1. ✅ 运行测试：`python3 etf_quanta_main.py --iterations 2`
2. ✅ 查看结果：`cat quanta_screening_result.json`
3. ✅ 理解 6 大方向规则逻辑

### 等待数据对接
- ⏳ 真实 ETF 估值数据（PE/PB 分位）
- ⏳ 资金流数据
- ⏳ 历史回测验证

### 长期优化
- 每周进化迭代
- 每月规则评估
- 根据市场变化调整

---

## 技术支持

**文件位置**:
- 核心代码：`/home/admin/openclaw/workspace/etf_quanta*.py`
- 方案设计：`etf_quantaalpha_plan.md`
- 实施报告：`etf_quantaalpha_implementation_report.md`

**测试命令**:
```bash
cd /home/admin/openclaw/workspace
python3 etf_quanta_framework.py  # 数据结构测试
python3 etf_quanta_init.py       # 初始化测试
python3 etf_quanta_eval.py       # 评估测试
python3 etf_quanta_main.py       # 完整运行
```

---

**版本**: v0.1  
**更新**: 2026-03-27  
**状态**: 阶段 1 完成，数据对接中
