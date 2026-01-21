#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试只使用语义相似度的筛选和展示逻辑
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"


async def test_similarity_only_mode():
    """测试只用语义相似度模式"""
    print("\n" + "="*80)
    print("测试语义相似度筛选模式")
    print("="*80)
    print("\n修改内容:")
    print("1. ❌ 移除多维度相关度计算")
    print("2. ✅ 只使用语义相似度（text-embedding-3-small）")
    print("3. ✅ 筛选依据：similarity >= 0.62")
    print("4. ✅ 展示分数：similarity")
    print("5. ✅ 移除字段：composite_score, relevance_dimensions, relationship_tier\n")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BASE_URL}/discover",
            json={
                "concept": "神经网络",
                "max_concepts": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            nodes = result['data']['nodes']
            
            print(f"✅ 测试成功，生成{len(nodes)}个节点\n")
            
            # 检查数据结构
            print("="*80)
            print("数据结构检查")
            print("="*80)
            
            sample_node = [n for n in nodes if n.get('depth', 0) > 0][0] if len(nodes) > 1 else None
            
            if sample_node:
                print(f"\n示例节点：{sample_node['label']}\n")
                print("✅ 包含字段:")
                for key in sorted(sample_node.keys()):
                    value = sample_node[key]
                    if isinstance(value, (int, float)):
                        print(f"   - {key}: {value}")
                    elif isinstance(value, str) and len(value) < 50:
                        print(f"   - {key}: {value}")
                    else:
                        print(f"   - {key}: <数据已省略>")
                
                # 检查是否移除了增强字段
                removed_fields = ["composite_score", "relevance_dimensions", "relationship_tier"]
                print("\n❌ 已移除字段（确认）:")
                for field in removed_fields:
                    status = "⚠️ 仍存在" if field in sample_node else "✅ 已移除"
                    print(f"   - {field}: {status}")
            
            # 展示排序结果
            print("\n" + "="*80)
            print("节点排序（按语义相似度）")
            print("="*80)
            
            sorted_nodes = sorted(
                [n for n in nodes if n.get('depth', 0) > 0],
                key=lambda x: x.get('similarity', 0),
                reverse=True
            )
            
            print("\n排名 | 概念名称 | 语义相似度 | 可信度 | 学科 | 数据来源")
            print("-" * 95)
            
            for i, node in enumerate(sorted_nodes, 1):
                name = node.get('label', 'N/A')
                sim = node.get('similarity', 0)
                cred = node.get('credibility', 0)
                disc = node.get('discipline', 'N/A')
                source = node.get('source', 'N/A')
                
                # 相似度着色
                if sim >= 0.70:
                    indicator = "🟢"
                elif sim >= 0.62:
                    indicator = "🟡"
                else:
                    indicator = "🔴"
                
                print(f"{i:2d}   | {name:18s} | {indicator} {sim:.3f}      | {cred:.3f}   | {disc:12s} | {source}")
            
            # 统计分析
            print("\n" + "="*80)
            print("统计分析")
            print("="*80)
            
            similarities = [n.get('similarity', 0) for n in sorted_nodes]
            
            print(f"\n相似度分布:")
            print(f"  最高: {max(similarities):.3f}")
            print(f"  最低: {min(similarities):.3f}")
            print(f"  平均: {sum(similarities)/len(similarities):.3f}")
            print(f"  范围: {max(similarities) - min(similarities):.3f}")
            
            above_threshold = [s for s in similarities if s >= 0.62]
            below_threshold = [s for s in similarities if s < 0.62]
            
            print(f"\n阈值筛选（0.62）:")
            print(f"  高于阈值: {len(above_threshold)}个")
            print(f"  低于阈值: {len(below_threshold)}个")
            
            if below_threshold:
                print(f"  ⚠️ 注意：有{len(below_threshold)}个节点低于阈值但仍被保留（因MIN_NODES=3要求）")
            
            # 对比说明
            print("\n" + "="*80)
            print("与多维度模式对比")
            print("="*80)
            print("\n【当前模式】只用语义相似度:")
            print("  ✅ 优点: 计算快速，逻辑一致，无额外LLM调用")
            print("  ❌ 缺点: 可能错过跨学科原理相似的概念")
            print("  📊 筛选依据 = 展示分数 = similarity")
            
            print("\n【之前模式】多维度综合得分:")
            print("  ✅ 优点: 更好识别跨学科关联，考虑原理一致性")
            print("  ❌ 缺点: 计算慢（每概念额外1次LLM调用），复杂度高")
            print("  ⚠️ 问题: 筛选用similarity，展示用composite_score（不一致！）")
                
        else:
            print(f"❌ 测试失败: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_similarity_only_mode())
