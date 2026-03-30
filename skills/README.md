# 金融投资分析技能库

## 技能列表

### 1. ETF 融合筛选系统 v1.1
**位置**: `etf-fusion-screening/SKILL.md`

**功能**: 板块轮动 × 多因子 ETF 筛选融合系统

**触发词**:
- "ETF 筛选"、"推荐 ETF"、"筛选 ETF"
- "融合筛选"、"多因子"、"因子评分"
- "板块轮动"、"行业轮动"
- "今天买什么 ETF"

**核心能力**:
- ✅ 五因子融合模型（行业 25%+ 波动 30%+ 动量 25%+ 估值 20%+ 宏观 10%）
- ✅ 行业 ETF 优先，宽基 ETF 分开评估
- ✅ Tushare Pro 真实数据（25,100 积分）
- ✅ 回测验证（250 天真实数据 + 压力测试）

**快速调用**:
```bash
python3 /home/admin/openclaw/workspace/sector_etf_fusion.py
```

**输出文件**:
- `fusion_result.json` - 筛选结果
- `sector_etf_mapping.json` - 行业-ETF 映射

---

### 2. 四层仓位管理系统 v2.0
**位置**: `four-layer-position/SKILL.md`

**功能**: 基于融合筛选结果的四层仓位智能分配

**触发词**:
- "仓位配置"、"仓位管理"、"资金分配"
- "四层仓位"、"四层配置"
- "怎么建仓"、"如何配置 ETF"
- "防守层"、"未来层"、"获利层"、"全球层"

**四层架构**:
| 层级 | 仓位 | 定位 | 调仓 |
|------|------|------|------|
| **防守层** | 27% | 高股息 + 低波动 | 周频 |
| **未来层** | 27% | 成长型赛道 | 周频 |
| **获利层** | 20% | 高弹性交易 | 日频 |
| **全球层** | 16% | QDII/跨境 | 周频 |
| **现金层** | 10% | 流动性储备 | 灵活 |

**快速调用**:
```bash
python3 /home/admin/openclaw/workspace/four_layer_upgrade_v2.py
```

**输出文件**:
- `four_layer_positions_v2.json` - 仓位配置

---

## 使用流程

### 场景 1：ETF 筛选 + 仓位配置
```
1. 运行融合筛选 → sector_etf_fusion.py
2. 运行四层配置 → four_layer_upgrade_v2.py
3. 生成报告 → 发送飞书
```

### 场景 2：日常监控
```
1. 读取 fusion_result.json → 获取最新评分
2. 读取 four_layer_positions_v2.json → 获取配置
3. 对比变化 → 生成调仓建议
```

### 场景 3：回测验证
```
1. 运行专业回测 → professional_backtest.py
2. 查看回测结果 → backtest_v2_professional.json
3. 压力测试 → 4 种市场场景
```

---

## 数据源配置

### Tushare Pro
- **Token**: `7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75`
- **积分**: 25,100 分（完全数据接口）
- **数据模块**: `/home/admin/openclaw/workspace/tushare_data.py`

### 数据优先级
```
Tushare Pro (主数据源)
  ↓ (失败时降级)
akshare (备用数据源)
  ↓ (失败时降级)
缓存数据 (3 分钟缓存)
```

---

## 文件结构

```
/home/admin/openclaw/workspace/
├── skills/
│   ├── etf-fusion-screening/
│   │   └── SKILL.md          # ETF 融合筛选技能
│   ├── four-layer-position/
│   │   └── SKILL.md          # 四层仓位技能
│   └── README.md             # 本文件
│
├── sector_etf_fusion.py      # 融合筛选核心
├── four_layer_upgrade_v2.py  # 四层配置核心
├── professional_backtest.py  # 专业回测
│
├── fusion_result.json        # 筛选结果
├── four_layer_positions_v2.json  # 仓位配置
├── backtest_v2_professional.json # 回测结果
│
└── sector_etf_mapping.json   # 行业-ETF 映射
```

---

## 快速命令

### ETF 筛选
```bash
# 运行融合筛选
python3 /home/admin/openclaw/workspace/sector_etf_fusion.py

# 查看结果
cat /home/admin/openclaw/workspace/fusion_result.json | python3 -m json.tool
```

### 仓位配置
```bash
# 运行四层配置
python3 /home/admin/openclaw/workspace/four_layer_upgrade_v2.py

# 查看配置
cat /home/admin/openclaw/workspace/four_layer_positions_v2.json | python3 -m json.tool
```

### 回测验证
```bash
# 运行专业回测
python3 /home/admin/openclaw/workspace/professional_backtest.py

# 查看回测结果
cat /home/admin/openclaw/workspace/backtest_v2_professional.json | python3 -m json.tool
```

---

## 版本历史

- **v2.0** (2026-03-29): 四层仓位升级，融合筛选 v1.1
- **v1.1** (2026-03-29): 融合筛选修复（宽基 ETF 不参与行业轮动）
- **v1.0** (2026-03-28): 四层仓位初始版本

---

## 联系支持

- **技能文档**: 查看各技能目录下的 SKILL.md
- **问题反馈**: 检查日志文件
- **数据源**: Tushare Pro 25,100 积分完全接口

---

⚠️ **风险提示**: 所有分析仅供参考，不构成投资建议。市场有风险，投资需谨慎。
