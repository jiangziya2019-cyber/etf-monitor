#!/usr/bin/env python3
"""
持仓数据更新脚本
用于安全更新 holdings_current.json
"""

import json
import os
from datetime import datetime
from pathlib import Path

class HoldingsUpdater:
    def __init__(self):
        self.workspace = Path("/home/admin/openclaw/workspace")
        self.current_file = self.workspace / "holdings_current.json"
        self.backup_dir = self.workspace / "holdings_backup"
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self):
        """创建备份"""
        if self.current_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"holdings_{timestamp}.json"
            
            with open(self.current_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新最新备份
            latest_backup = self.backup_dir / "holdings_latest.json"
            with open(latest_backup, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份已创建：{backup_file.name}")
            return True
        return False
    
    def update_holdings(self, etfs_data, source="手动更新"):
        """
        更新持仓数据
        
        Args:
            etfs_data: ETF 持仓列表
            source: 数据来源说明
        """
        # 创建备份
        self.create_backup()
        
        # 计算汇总数据
        total_market_value = sum(etf.get('market_value', 0) for etf in etfs_data)
        total_profit = sum(etf.get('profit', 0) for etf in etfs_data)
        yield_rate = (total_profit / total_market_value * 100) if total_market_value > 0 else 0
        
        # 构建数据结构
        holdings_data = {
            "last_updated": datetime.now().isoformat(),
            "source": source,
            "total_market_value": round(total_market_value, 2),
            "total_profit": round(total_profit, 2),
            "yield_rate": round(yield_rate, 2),
            "etf_count": len(etfs_data),
            "etfs": etfs_data
        }
        
        # 写入文件
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(holdings_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 持仓数据已更新")
        print(f"   ETF 数量：{len(etfs_data)}")
        print(f"   总市值：¥{total_market_value:,.2f}")
        print(f"   总盈亏：{total_profit:+,.2f} 元")
        print(f"   收益率：{yield_rate:.2f}%")
        
        return holdings_data
    
    def append_daily_record(self, holdings_data):
        """添加每日记录"""
        today = datetime.now().strftime("%Y-%m-%d")
        record_file = self.workspace / "memory" / "portfolio" / f"{today}.md"
        record_file.parent.mkdir(exist_ok=True)
        
        # 生成记录内容
        content = f"""# {today} 持仓记录

## 基本信息
- **更新时间**: {holdings_data['last_updated']}
- **数据来源**: {holdings_data['source']}
- **ETF 数量**: {holdings_data['etf_count']} 只
- **总市值**: ¥{holdings_data['total_market_value']:,.2f}
- **总盈亏**: {holdings_data['total_profit']:+,.2f} 元
- **收益率**: {holdings_data['yield_rate']:.2f}%

## 持仓明细

| 代码 | 名称 | 价格 | 数量 | 市值 | 盈亏 | 盈亏% |
|------|------|------|------|------|------|-------|
"""
        
        for etf in holdings_data['etfs']:
            content += f"| {etf.get('code', '-')} | {etf.get('name', '-')} | {etf.get('price', 0):.3f} | {etf.get('shares', 0):.0f} | ¥{etf.get('market_value', 0):,.0f} | {etf.get('profit', 0):+,.0f} | {etf.get('yield', 0):+.2f}% |\n"
        
        # 写入文件
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 每日记录已保存：{record_file.name}")
    
    def parse_ocr_result(self, ocr_text):
        """
        解析 OCR 识别结果
        
        Args:
            ocr_text: OCR 识别的原始文本
        
        Returns:
            list: ETF 持仓列表
        """
        # TODO: 实现 OCR 文本解析逻辑
        # 这里需要根据实际 OCR 输出格式来解析
        pass

def main():
    """测试示例"""
    updater = HoldingsUpdater()
    
    # 示例数据
    sample_etfs = [
        {"code": "510880", "name": "红利 ETF", "price": 3.284, "shares": 3817, "market_value": 12536, "profit": 56, "yield": 0.46},
        {"code": "512480", "name": "半导体", "price": 1.567, "shares": 3276, "market_value": 5134, "profit": -349, "yield": -6.38},
    ]
    
    # 更新持仓
    holdings_data = updater.update_holdings(sample_etfs, source="测试更新")
    
    # 保存每日记录
    updater.append_daily_record(holdings_data)

if __name__ == "__main__":
    main()
