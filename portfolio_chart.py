#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓收益走势图生成工具
- 读取历史持仓数据
- 生成持仓总值/收益走势图
- 标注买卖点
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 目录配置
WORKSPACE = Path('/home/admin/openclaw/workspace')
HISTORY_DIR = WORKSPACE / 'portfolio_history' / 'daily'
CHART_DIR = WORKSPACE / 'portfolio_history' / 'charts'
CHART_DIR.mkdir(parents=True, exist_ok=True)

def parse_daily_snapshot(file_path):
    """解析每日持仓快照文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取日期
    filename = os.path.basename(file_path).replace('.md', '')
    
    # 简单解析：查找汇总数据
    total_value = 0
    total_pnl = 0
    
    # 查找总市值行
    for line in content.split('\n'):
        if '**总市值**' in line:
            try:
                value_str = line.split('|')[2].strip()
                total_value = float(value_str.replace(',', '').replace('元', '').replace(' ', ''))
            except:
                pass
        if '**总盈亏**' in line or '**估算总盈亏**' in line:
            try:
                pnl_str = line.split('|')[2].strip()
                pnl_str = pnl_str.replace(',', '').replace('元', '').replace(' ', '')
                # 处理正负号
                if '+' in pnl_str:
                    pnl_str = pnl_str.replace('+', '')
                total_pnl = float(pnl_str)
            except:
                pass
    
    return {
        'date': filename,
        'total_value': total_value,
        'total_pnl': total_pnl
    }

def load_history_data(days=30):
    """加载最近 N 天的持仓数据"""
    data = []
    
    if not HISTORY_DIR.exists():
        print(f"⚠️ 历史目录不存在：{HISTORY_DIR}")
        return data
    
    # 获取所有快照文件
    files = sorted(HISTORY_DIR.glob('*.md'), reverse=True)
    
    for file in files[:days]:
        try:
            snapshot = parse_daily_snapshot(file)
            if snapshot['total_value'] > 0:
                data.append(snapshot)
        except Exception as e:
            print(f"⚠️ 解析失败 {file}: {e}")
    
    # 按日期排序
    data.sort(key=lambda x: x['date'])
    return data

def generate_portfolio_chart(data, output_file=None):
    """生成持仓走势图"""
    if len(data) < 2:
        print("⚠️ 数据不足，无法生成图表")
        return None
    
    # 准备数据
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data]
    values = [d['total_value'] for d in data]
    pnls = [d['total_pnl'] for d in data]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('持仓收益走势图', fontsize=16, fontweight='bold')
    
    # 上图：持仓总值
    ax1.plot(dates, values, 'b-', linewidth=2, marker='o', markersize=6)
    ax1.fill_between(dates, values, alpha=0.3, color='blue')
    ax1.set_ylabel('持仓总值 (元)', fontsize=12)
    ax1.set_title('持仓总值变化', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    
    # 添加数值标签
    for i, (date, value) in enumerate(zip(dates, values)):
        ax1.annotate(f'{value/1000:.1f}k', 
                    (date, value), 
                    textcoords="offset points", 
                    xytext=(0, 10), 
                    ha='center',
                    fontsize=8)
    
    # 下图：盈亏
    colors = ['red' if pnl >= 0 else 'green' for pnl in pnls]
    ax2.bar(dates, pnls, color=colors, alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_ylabel('盈亏 (元)', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.set_title('持仓盈亏变化', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    
    # 添加数值标签
    for i, (date, pnl) in enumerate(zip(dates, pnls)):
        color = 'white' if abs(pnl) > 500 else 'black'
        ax2.annotate(f'{pnl/1000:.1f}k', 
                    (date, pnl), 
                    textcoords="offset points", 
                    xytext=(0, 10 if pnl >= 0 else -15), 
                    ha='center',
                    fontsize=8,
                    color=color)
    
    plt.tight_layout()
    
    # 保存图片
    if output_file is None:
        output_file = CHART_DIR / f'portfolio_trend_{datetime.now().strftime("%Y%m%d")}.png'
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 持仓走势图已保存：{output_file}")
    return output_file

def generate_with_trades_chart(data, trades, output_file=None):
    """生成带买卖点标注的走势图"""
    if len(data) < 2:
        print("⚠️ 数据不足，无法生成图表")
        return None
    
    # 准备数据
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data]
    values = [d['total_value'] for d in data]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.suptitle('持仓走势与交易点位', fontsize=16, fontweight='bold')
    
    # 持仓总值线
    ax.plot(dates, values, 'b-', linewidth=2, marker='o', markersize=6, label='持仓总值')
    ax.fill_between(dates, values, alpha=0.3, color='blue')
    
    # 标注买卖点
    buy_dates = []
    buy_values = []
    sell_dates = []
    sell_values = []
    
    for trade in trades:
        trade_date = datetime.strptime(trade['date'], '%Y-%m-%d')
        if trade['type'] == 'buy':
            buy_dates.append(trade_date)
            # 估算当天的持仓值
            idx = min(range(len(dates)), key=lambda i: abs((dates[i] - trade_date).days))
            buy_values.append(values[idx] if idx < len(values) else values[-1])
        elif trade['type'] == 'sell':
            sell_dates.append(trade_date)
            idx = min(range(len(dates)), key=lambda i: abs((dates[i] - trade_date).days))
            sell_values.append(values[idx] if idx < len(values) else values[-1])
    
    # 绘制买卖点
    if buy_dates:
        ax.scatter(buy_dates, buy_values, color='red', marker='^', s=150, label='买入', zorder=5)
    if sell_dates:
        ax.scatter(sell_dates, sell_values, color='green', marker='v', s=150, label='卖出', zorder=5)
    
    ax.set_ylabel('持仓总值 (元)', fontsize=12)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_title('持仓总值变化与交易点位', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.legend()
    
    plt.tight_layout()
    
    # 保存图片
    if output_file is None:
        output_file = CHART_DIR / f'portfolio_with_trades_{datetime.now().strftime("%Y%m%d")}.png'
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 带交易点位的走势图已保存：{output_file}")
    return output_file

def generate_position_pie_chart(holdings, output_file=None):
    """生成持仓分布饼图"""
    if not holdings:
        print("⚠️ 无持仓数据")
        return None
    
    # 按市值排序，取前 10 大持仓
    sorted_holdings = sorted(holdings, key=lambda x: x.get('market_value', 0), reverse=True)[:10]
    
    labels = [h['name'] for h in sorted_holdings]
    sizes = [h['market_value'] for h in sorted_holdings]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('持仓分布图', fontsize=16, fontweight='bold')
    
    # 左图：饼图
    colors = plt.cm.Set3(range(len(labels)))
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('前 10 大持仓占比', fontsize=14, fontweight='bold')
    
    # 右图：条形图
    ax2.barh(labels, sizes, color=colors)
    ax2.set_xlabel('市值 (元)', fontsize=12)
    ax2.set_title('前 10 大持仓市值', fontsize=14, fontweight='bold')
    ax2.invert_yaxis()
    
    # 添加数值标签
    for i, (label, size) in enumerate(zip(labels, sizes)):
        ax2.text(size + max(sizes)*0.01, i, f'{size/1000:.1f}k', va='center', fontsize=9)
    
    plt.tight_layout()
    
    if output_file is None:
        output_file = CHART_DIR / f'position_pie_{datetime.now().strftime("%Y%m%d")}.png'
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 持仓分布图已保存：{output_file}")
    return output_file

if __name__ == "__main__":
    import sys
    
    # 加载历史数据
    print("📊 加载历史持仓数据...")
    data = load_history_data(days=30)
    print(f"✅ 加载 {len(data)} 天数据")
    
    if len(data) >= 2:
        # 生成基础走势图
        chart_file = generate_portfolio_chart(data)
        
        # 示例：生成带买卖点的图（需要交易记录）
        trades = [
            {'date': '2026-03-26', 'type': 'sell', 'name': '机器人 AI', 'amount': 12000},
            {'date': '2026-03-26', 'type': 'sell', 'name': '黄金 9999', 'amount': 5000},
            {'date': '2026-03-26', 'type': 'buy', 'name': '红利 ETF', 'amount': 8000},
        ]
        trades_chart = generate_with_trades_chart(data, trades)
        
        print(f"\n✅ 走势图已保存至：{CHART_DIR}")
    else:
        print("⚠️ 数据不足，生成持仓分布图...")
        # 从当前持仓文件读取
        holdings = []
        with open(WORKSPACE / 'portfolio_holdings.md', 'r', encoding='utf-8') as f:
            content = f.read()
            # 简单解析表格
            for line in content.split('\n'):
                if '|' in line and '品种' not in line and '---' not in line:
                    parts = line.split('|')
                    if len(parts) >= 9:
                        try:
                            name = parts[1].strip()
                            market_value_str = parts[8].strip().replace(',', '').replace('元', '')
                            market_value = float(market_value_str)
                            holdings.append({'name': name, 'market_value': market_value})
                        except:
                            pass
        
        if holdings:
            pie_chart = generate_position_pie_chart(holdings)
            print(f"\n✅ 持仓分布图已保存至：{CHART_DIR}")
        else:
            print("⚠️ 无法解析持仓数据")
        
        print("\n💡 提示：每日收盘后发送持仓数据，积累 2 天后可生成走势图")
