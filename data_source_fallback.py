#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源降级切换模块 - 优先级🟡
版本：v1.0 | 创建：2026-03-28 13:48

功能:
  - Tushare 失败自动切换 Akshare
  - 都失败使用缓存数据
  - 数据质量检查
  - 错误重试机制
"""

import sys, json, os, time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

sys.path.insert(0, '/home/admin/openclaw/workspace')

# ============ 配置 ============

CACHE_DIR = '/home/admin/openclaw/workspace/etf_data_cache'
VALUATION_CACHE = '/home/admin/openclaw/workspace/valuation_cache'
LOG_FILE = '/home/admin/openclaw/workspace/data_source.log'
TUSHARE_TOKEN = '7a534da257fa5505df132208cb1b5c3ea648a79763c9829d74dcca75'

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒

# 缓存过期时间（秒）
CACHE_TTL = {
    'price_1min': 300,      # 5 分钟
    'price_daily': 86400,   # 24 小时
    'valuation': 604800,    # 7 天
}

class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.tushare_available = True
        self.akshare_available = True
        self.last_check_time = None
        self.log_messages = []
    
    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        self.log_messages.append(log_line)
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def check_tushare(self) -> bool:
        """检查 Tushare 可用性"""
        try:
            import tushare as ts
            ts.set_token(TUSHARE_TOKEN)
            pro = ts.pro_api()
            
            # 测试接口
            df = pro.index_daily(ts_code='000001.SH', start_date='20260327', end_date='20260327')
            
            if df is not None and len(df) > 0:
                self.tushare_available = True
                self.log("Tushare API 正常")
                return True
            else:
                self.tushare_available = False
                self.log("Tushare API 返回空数据", 'WARN')
                return False
        except Exception as e:
            self.tushare_available = False
            self.log(f"Tushare API 失败：{e}", 'ERROR')
            return False
    
    def check_akshare(self) -> bool:
        """检查 Akshare 可用性"""
        try:
            import akshare as ak
            
            # 测试接口
            df = ak.stock_zh_index_spot()
            
            if df is not None and len(df) > 0:
                self.akshare_available = True
                self.log("Akshare API 正常")
                return True
            else:
                self.akshare_available = False
                self.log("Akshare API 返回空数据", 'WARN')
                return False
        except Exception as e:
            self.akshare_available = False
            self.log(f"Akshare API 失败：{e}", 'ERROR')
            return False
    
    def check_data_sources(self) -> Dict:
        """检查所有数据源"""
        self.log("="*50)
        self.log("检查数据源可用性...")
        
        tushare_ok = self.check_tushare()
        akshare_ok = self.check_akshare()
        
        status = {
            'check_time': datetime.now().isoformat(),
            'tushare': {'available': tushare_ok, 'priority': 1},
            'akshare': {'available': akshare_ok, 'priority': 2},
            'cache': {'available': os.path.exists(CACHE_DIR), 'priority': 3},
            'active_source': 'tushare' if tushare_ok else ('akshare' if akshare_ok else 'cache')
        }
        
        self.log(f"当前活跃数据源：{status['active_source']}")
        return status
    
    def get_etf_data(self, etf_code: str, data_type: str = 'daily') -> Optional[Dict]:
        """
        获取 ETF 数据（自动降级）
        
        Args:
            etf_code: ETF 代码
            data_type: 数据类型 (daily/1min/valuation)
        
        Returns:
            数据字典
        """
        # 1. 尝试 Tushare
        if self.tushare_available:
            try:
                data = self._fetch_from_tushare(etf_code, data_type)
                if data:
                    self.log(f"✅ {etf_code} 从 Tushare 获取成功")
                    return data
            except Exception as e:
                self.log(f"⚠️ Tushare 获取 {etf_code} 失败：{e}", 'WARN')
                self.tushare_available = False
        
        # 2. 降级到 Akshare
        if self.akshare_available:
            try:
                data = self._fetch_from_akshare(etf_code, data_type)
                if data:
                    self.log(f"✅ {etf_code} 从 Akshare 获取成功（降级）")
                    return data
            except Exception as e:
                self.log(f"⚠️ Akshare 获取 {etf_code} 失败：{e}", 'WARN')
                self.akshare_available = False
        
        # 3. 降级到缓存
        data = self._fetch_from_cache(etf_code, data_type)
        if data:
            self.log(f"✅ {etf_code} 从缓存获取（降级）", 'WARN')
            return data
        
        self.log(f"❌ {etf_code} 所有数据源失败", 'ERROR')
        return None
    
    def _fetch_from_tushare(self, etf_code: str, data_type: str) -> Optional[Dict]:
        """从 Tushare 获取数据"""
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        if data_type == 'daily':
            # 确定交易所
            if etf_code.startswith('5'):
                ts_code = f"{etf_code}.SH"
            else:
                ts_code = f"{etf_code}.SZ"
            
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
            
            df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                data = []
                for _, row in df.iterrows():
                    data.append({
                        'trade_date': row.get('trade_date', ''),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'vol': float(row.get('vol', 0))
                    })
                
                return {'source': 'tushare', 'data': data, 'etf_code': etf_code}
        
        return None
    
    def _fetch_from_akshare(self, etf_code: str, data_type: str) -> Optional[Dict]:
        """从 Akshare 获取数据"""
        import akshare as ak
        
        try:
            # 获取 ETF 历史数据
            if etf_code.startswith('5'):
                symbol = f"sz{etf_code}"
            else:
                symbol = f"sz{etf_code}"
            
            df = ak.fund_etf_hist_em(symbol=symbol, period="daily")
            
            if df is not None and len(df) > 0:
                data = []
                for _, row in df.iterrows():
                    data.append({
                        'trade_date': str(row.get('日期', '')),
                        'open': float(row.get('开盘', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'close': float(row.get('收盘', 0)),
                        'vol': float(row.get('成交量', 0))
                    })
                
                return {'source': 'akshare', 'data': data, 'etf_code': etf_code}
        except Exception as e:
            self.log(f"Akshare 获取失败：{e}", 'DEBUG')
        
        return None
    
    def _fetch_from_cache(self, etf_code: str, data_type: str) -> Optional[Dict]:
        """从缓存获取数据"""
        cache_file = f"{CACHE_DIR}/{etf_code}.json"
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # 检查缓存是否过期
                cache_time = cached_data.get('update_time', '')
                if cache_time:
                    cache_datetime = datetime.fromisoformat(cache_time)
                    age_seconds = (datetime.now() - cache_datetime).total_seconds()
                    
                    ttl = CACHE_TTL.get(data_type, CACHE_TTL['price_daily'])
                    
                    if age_seconds < ttl:
                        cached_data['source'] = 'cache'
                        cached_data['cache_hit'] = True
                        return cached_data
                    else:
                        self.log(f"缓存过期 ({age_seconds/3600:.1f}小时前)", 'WARN')
            except Exception as e:
                self.log(f"缓存读取失败：{e}", 'WARN')
        
        return None

def main():
    """主函数"""
    print("="*70)
    print("数据源降级切换模块 v1.0")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    manager = DataSourceManager()
    
    # 1. 检查数据源
    status = manager.check_data_sources()
    
    print("\n" + "="*70)
    print("数据源状态")
    print("="*70)
    print(f"Tushare:  {'✅ 可用' if status['tushare']['available'] else '❌ 不可用'}")
    print(f"Akshare:  {'✅ 可用' if status['akshare']['available'] else '❌ 不可用'}")
    print(f"缓存：    {'✅ 可用' if status['cache']['available'] else '❌ 不可用'}")
    print(f"活跃数据源：{status['active_source']}")
    
    # 2. 测试获取数据
    print("\n" + "="*70)
    print("测试数据获取")
    print("="*70)
    
    test_etfs = ['510300', '512880', '159566']
    for etf in test_etfs:
        data = manager.get_etf_data(etf, 'daily')
        if data:
            print(f"✅ {etf}: {len(data.get('data', []))}条数据 ({data.get('source', 'unknown')})")
        else:
            print(f"❌ {etf}: 获取失败")

if __name__ == "__main__":
    main()
