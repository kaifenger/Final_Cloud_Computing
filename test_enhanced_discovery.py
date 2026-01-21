#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多维度相关度集成
对比改进前后的排序效果
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"


async def test_enhanced_discover():
    """测试集成多维度相关度后的discover接口"""
    print("\n" + "="*70)
    print("测试多维度相关度集成")
    print("="*70)
    
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
            
            print(f"\n✅ 测试成功，生成{len(nodes)}个节点\n")
            
            # 按综合得分排序展示
            sorted_nodes = sorted(
                [n for n in nodes if n.get('depth', 0) > 0],
                key=lambda x: x.get('composite_score', x.get('similarity', 0)),
                reverse=True
            )
            
            print("排名 | 概念名称 | 综合得分 | 语义相似度 | 关系层级 | 学科")
            print("-" * 90)
            
            for i, node in enumerate(sorted_nodes, 1):
                name = node.get('label', 'N/A')
                composite = node.get('composite_score', 'N/A')
                similarity = node.get('similarity', 'N/A')
                tier = node.get('relationship_tier', 'N/A')
                discipline = node.get('discipline', 'N/A')
                
                print(f"{i:2d}   | {name:15s} | {composite:8} | {similarity:10} | {tier:12s} | {discipline}")
            
            # 分析多维度信息
            has_enhanced = any('relevance_dimensions' in n for n in sorted_nodes)
            
            if has_enhanced:
                print("\n" + "="*70)
                print("多维度详细分析（前5名）")
                print("="*70)
                
                for i, node in enumerate(sorted_nodes[:5], 1):
                    dims = node.get('relevance_dimensions', {})
                    if dims:
                        print(f"\n{i}. {node['label']} ({node.get('relationship_tier', 'N/A')})")
                        print(f"   语义相似度:   {dims.get('semantic', 'N/A')}")
                        print(f"   跨学科强度:   {dims.get('cross_discipline', 'N/A')}")
                        print(f"   原理一致性:   {dims.get('principle', 'N/A')}")
                        print(f"   新颖度:       {dims.get('novelty', 'N/A')}")
                        print(f"   → 综合得分:   {node.get('composite_score', 'N/A')}")
            else:
                print("\n⚠️  未检测到多维度相关度数据，可能未启用增强模式")
                
        else:
            print(f"❌ 测试失败: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_enhanced_discover())
