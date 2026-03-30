#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ontology 知识图谱查询工具
支持实体查询、关系遍历、图搜索
"""

import json
import os
from typing import Dict, List, Optional, Set

ONTOLOGY_FILE = "/home/admin/openclaw/workspace/memory/ontology/graph.jsonl"
SCHEMA_FILE = "/home/admin/openclaw/workspace/memory/ontology/schema.json"

class OntologyQuery:
    def __init__(self):
        self.entities = {}
        self.relations = []
        self.schema = {}
        self.load()
    
    def load(self):
        """加载图谱数据"""
        if os.path.exists(ONTOLOGY_FILE):
            with open(ONTOLOGY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        op = json.loads(line)
                        if op['op'] == 'create':
                            entity = op['entity']
                            self.entities[entity['id']] = entity
                        elif op['op'] == 'relate':
                            self.relations.append({
                                'from': op['from'],
                                'rel': op['rel'],
                                'to': op['to']
                            })
                    except:
                        pass
        
        if os.path.exists(SCHEMA_FILE):
            with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """按类型获取实体"""
        return [e for e in self.entities.values() if e.get('type') == entity_type]
    
    def get_relations(self, from_id: str = None, rel_type: str = None, to_id: str = None) -> List[Dict]:
        """查询关系"""
        results = []
        for r in self.relations:
            if from_id and r['from'] != from_id:
                continue
            if rel_type and r['rel'] != rel_type:
                continue
            if to_id and r['to'] != to_id:
                continue
            results.append(r)
        return results
    
    def find_related(self, entity_id: str, max_depth: int = 2) -> Dict:
        """查找关联实体（BFS 遍历）"""
        result = {
            'entity': self.get_entity(entity_id),
            'relations': [],
            'related_entities': []
        }
        
        visited = set()
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            
            # 查找向外的关系
            for r in self.get_relations(from_id=current_id):
                result['relations'].append(r)
                related = self.get_entity(r['to'])
                if related:
                    result['related_entities'].append(related)
                    queue.append((r['to'], depth + 1))
            
            # 查找向内的关系
            for r in self.get_relations(to_id=current_id):
                result['relations'].append({
                    'from': r['from'],
                    'rel': f"inverse_{r['rel']}",
                    'to': r['to']
                })
                related = self.get_entity(r['from'])
                if related:
                    result['related_entities'].append(related)
                    queue.append((r['from'], depth + 1))
        
        return result
    
    def search(self, query: str) -> List[Dict]:
        """全文搜索"""
        results = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            # 搜索 ID
            if query_lower in entity.get('id', '').lower():
                results.append(entity)
                continue
            
            # 搜索类型
            if query_lower in entity.get('type', '').lower():
                results.append(entity)
                continue
            
            # 搜索属性
            props = entity.get('properties', {})
            for key, value in props.items():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(entity)
                    break
                if isinstance(value, list) and any(query_lower in str(v).lower() for v in value):
                    results.append(entity)
                    break
        
        return results
    
    def stats(self) -> Dict:
        """统计信息"""
        type_counts = {}
        for entity in self.entities.values():
            t = entity.get('type', 'Unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'types': type_counts
        }

def main():
    print("=" * 80)
    print("Ontology 知识图谱查询工具")
    print("=" * 80)
    
    oq = OntologyQuery()
    
    # 统计
    stats = oq.stats()
    print(f"\n📊 图谱统计:")
    print(f"  实体总数：{stats['total_entities']}")
    print(f"  关系总数：{stats['total_relations']}")
    print(f"  类型分布:")
    for t, c in stats['types'].items():
        print(f"    {t}: {c}")
    
    # 测试查询
    print(f"\n🔍 测试查询:")
    
    # 查询所有 Task
    tasks = oq.get_entities_by_type('Task')
    print(f"\n【任务实体】({len(tasks)}个)")
    for t in tasks:
        props = t.get('properties', {})
        print(f"  - {t['id']}: {props.get('title', 'N/A')} ({props.get('status', 'unknown')})")
    
    # 查询老板相关
    print(f"\n【老板的关联】")
    boss_relations = oq.find_related('person_boss', max_depth=1)
    for r in boss_relations['relations'][:5]:
        print(f"  {r['from']} --[{r['rel']}]--> {r['to']}")
    
    # 搜索
    print(f"\n【搜索触发器】")
    results = oq.search('触发器')
    for r in results[:3]:
        print(f"  - {r['id']} ({r['type']})")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
