#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能检查：测试三个功能的实现情况和相似度修改效果
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


async def check_backend_health():
    """检查后端健康状态"""
    print("\n" + "="*80)
    print("1. 后端健康检查")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                print("✅ 后端服务正常运行")
                return True
            else:
                print(f"❌ 后端响应异常: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 无法连接后端: {e}")
        return False


async def test_function1_auto_cross_discipline():
    """测试功能1：自动跨学科概念发现"""
    print("\n" + "="*80)
    print("2. 功能1：自动跨学科概念发现")
    print("="*80)
    print("提示词类型：跨学科远亲概念挖掘")
    print("筛选模式：语义相似度（已修改）\n")
    
    try:
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
                
                print(f"✅ 功能1测试成功")
                print(f"   生成节点数: {len(nodes)}")
                
                # 检查数据结构
                sample = [n for n in nodes if n.get('depth', 0) > 0][0] if len(nodes) > 1 else None
                
                if sample:
                    print(f"\n   数据结构检查:")
                    print(f"   ✅ similarity字段: {sample.get('similarity', 'N/A')}")
                    print(f"   ✅ credibility字段: {sample.get('credibility', 'N/A')}")
                    print(f"   ✅ discipline字段: {sample.get('discipline', 'N/A')}")
                    
                    # 检查是否移除了多维度字段
                    removed_fields = []
                    if 'composite_score' in sample:
                        removed_fields.append('composite_score')
                    if 'relevance_dimensions' in sample:
                        removed_fields.append('relevance_dimensions')
                    if 'relationship_tier' in sample:
                        removed_fields.append('relationship_tier')
                    
                    if removed_fields:
                        print(f"   ⚠️  仍包含多维度字段: {', '.join(removed_fields)}")
                    else:
                        print(f"   ✅ 已成功移除多维度字段")
                
                # 显示学科分布
                disciplines = {}
                for node in nodes:
                    if node.get('depth', 0) > 0:
                        d = node.get('discipline', 'Unknown')
                        disciplines[d] = disciplines.get(d, 0) + 1
                
                print(f"\n   学科分布:")
                for disc, count in sorted(disciplines.items(), key=lambda x: -x[1]):
                    print(f"   - {disc}: {count}个")
                
                # 显示相似度分布
                similarities = [n.get('similarity', 0) for n in nodes if n.get('depth', 0) > 0]
                if similarities:
                    print(f"\n   相似度分布:")
                    print(f"   - 最高: {max(similarities):.3f}")
                    print(f"   - 最低: {min(similarities):.3f}")
                    print(f"   - 平均: {sum(similarities)/len(similarities):.3f}")
                
                return True
            else:
                print(f"❌ 功能1测试失败: {response.status_code}")
                print(f"   错误信息: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ 功能1测试异常: {e}")
        return False


async def test_function2_disciplined_discovery():
    """测试功能2：指定学科的概念挖掘"""
    print("\n" + "="*80)
    print("3. 功能2：指定学科概念挖掘")
    print("="*80)
    print("提示词类型：限定学科范围")
    print("测试学科：['生物学', '数学', '物理学']\n")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{BASE_URL}/discover/disciplined",
                json={
                    "concept": "神经网络",
                    "disciplines": ["生物学", "数学", "物理学"],
                    "max_concepts": 10
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                nodes = result['data']['nodes']
                
                print(f"✅ 功能2测试成功")
                print(f"   生成节点数: {len(nodes)}")
                
                # 按学科分组
                by_discipline = {}
                for node in nodes:
                    if node.get('depth', 0) > 0:
                        disc = node.get('discipline', 'Unknown')
                        if disc not in by_discipline:
                            by_discipline[disc] = []
                        by_discipline[disc].append(node['label'])
                
                print(f"\n   按学科分组:")
                for disc in ["生物学", "数学", "物理学"]:
                    concepts = by_discipline.get(disc, [])
                    print(f"   {disc} ({len(concepts)}个):")
                    for concept in concepts[:3]:  # 只显示前3个
                        print(f"      - {concept}")
                    if len(concepts) > 3:
                        print(f"      ... 还有{len(concepts)-3}个")
                
                # 检查是否严格遵守学科限制
                invalid_disciplines = [d for d in by_discipline.keys() 
                                      if d not in ["生物学", "数学", "物理学", "跨学科"]]
                if invalid_disciplines:
                    print(f"   ⚠️  发现非指定学科: {', '.join(invalid_disciplines)}")
                else:
                    print(f"   ✅ 严格遵守学科限制")
                
                return True
            else:
                print(f"❌ 功能2测试失败: {response.status_code}")
                print(f"   错误信息: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ 功能2测试异常: {e}")
        return False


async def test_function3_bridge_discovery():
    """测试功能3：多概念桥梁发现"""
    print("\n" + "="*80)
    print("4. 功能3：多概念桥梁发现")
    print("="*80)
    print("提示词类型：寻找连接多概念的桥梁")
    print("测试概念：['熵', '最小二乘法']\n")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{BASE_URL}/discover/bridge",
                json={
                    "concepts": ["熵", "最小二乘法"],
                    "max_bridges": 10
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                nodes = result['data']['nodes']
                
                print(f"✅ 功能3测试成功")
                print(f"   生成桥梁概念数: {len(nodes) - 2}")  # 减去两个输入概念
                
                # 统计桥梁类型
                bridge_types = {}
                for node in nodes:
                    if node.get('depth', 0) > 0:
                        btype = node.get('bridge_type', 'Unknown')
                        bridge_types[btype] = bridge_types.get(btype, 0) + 1
                
                print(f"\n   桥梁类型分布:")
                for btype, count in sorted(bridge_types.items(), key=lambda x: -x[1]):
                    print(f"   - {btype}: {count}个")
                
                # 显示示例桥梁
                print(f"\n   示例桥梁概念:")
                for node in [n for n in nodes if n.get('depth', 0) > 0][:3]:
                    print(f"   - {node['label']}")
                    print(f"     类型: {node.get('bridge_type', 'N/A')}")
                    print(f"     连接: {node.get('connected_concepts', 'N/A')}")
                    print(f"     原理: {node.get('connection_principle', 'N/A')[:50]}...")
                
                return True
            else:
                print(f"❌ 功能3测试失败: {response.status_code}")
                print(f"   错误信息: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ 功能3测试异常: {e}")
        return False


async def test_similarity_modification():
    """测试相似度修改效果"""
    print("\n" + "="*80)
    print("5. 相似度修改验证")
    print("="*80)
    print("检查点：")
    print("  1. 是否只使用similarity字段")
    print("  2. 筛选依据 = 展示分数")
    print("  3. 移除了composite_score等多维度字段\n")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{BASE_URL}/discover",
                json={
                    "concept": "深度学习",
                    "max_concepts": 5
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                nodes = result['data']['nodes']
                
                generated_nodes = [n for n in nodes if n.get('depth', 0) > 0]
                
                if not generated_nodes:
                    print("❌ 没有生成节点")
                    return False
                
                # 检查字段
                print("✅ 字段检查:")
                sample = generated_nodes[0]
                
                has_similarity = 'similarity' in sample
                has_composite = 'composite_score' in sample
                has_dimensions = 'relevance_dimensions' in sample
                has_tier = 'relationship_tier' in sample
                
                print(f"   similarity字段: {'✅ 存在' if has_similarity else '❌ 缺失'}")
                print(f"   composite_score字段: {'❌ 仍存在' if has_composite else '✅ 已移除'}")
                print(f"   relevance_dimensions字段: {'❌ 仍存在' if has_dimensions else '✅ 已移除'}")
                print(f"   relationship_tier字段: {'❌ 仍存在' if has_tier else '✅ 已移除'}")
                
                # 检查排序逻辑
                similarities = [n.get('similarity', 0) for n in generated_nodes]
                is_sorted = all(similarities[i] >= similarities[i+1] 
                              for i in range(len(similarities)-1))
                
                print(f"\n✅ 排序检查:")
                print(f"   按similarity降序: {'✅ 正确' if is_sorted else '❌ 错误'}")
                print(f"   相似度序列: {[f'{s:.3f}' for s in similarities]}")
                
                # 检查阈值筛选
                above_threshold = sum(1 for s in similarities if s >= 0.62)
                print(f"\n✅ 阈值筛选:")
                print(f"   高于0.62阈值: {above_threshold}/{len(similarities)}个")
                
                success = (has_similarity and not has_composite and 
                          not has_dimensions and not has_tier and is_sorted)
                
                if success:
                    print("\n✅ 相似度修改验证通过！")
                else:
                    print("\n⚠️  相似度修改存在问题")
                
                return success
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("ConceptGraph 完整功能检查")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 等待后端启动
    print("\n⏳ 等待后端启动...")
    await asyncio.sleep(10)
    
    results = {}
    
    # 1. 健康检查
    results['health'] = await check_backend_health()
    
    if not results['health']:
        print("\n❌ 后端服务未运行，无法继续测试")
        return
    
    # 2-4. 测试三个功能
    results['function1'] = await test_function1_auto_cross_discipline()
    results['function2'] = await test_function2_disciplined_discovery()
    results['function3'] = await test_function3_bridge_discovery()
    
    # 5. 验证相似度修改
    results['similarity'] = await test_similarity_modification()
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)\n")
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:20s}: {status}")
    
    print("\n" + "="*80)
    print("详细说明")
    print("="*80)
    
    print("\n功能1（自动跨学科）:")
    print("  - Prompt: 跨学科远亲概念挖掘")
    print("  - 位置: backend/api/real_node_generator.py")
    print("  - 特点: 自动从多学科寻找原理相通的概念")
    
    print("\n功能2（指定学科）:")
    print("  - Prompt: 限定学科范围的概念挖掘")
    print("  - 位置: backend/api/multi_function_generator.py")
    print("  - 特点: 严格在指定学科内寻找概念")
    
    print("\n功能3（桥梁发现）:")
    print("  - Prompt: 多概念间桥梁概念发现")
    print("  - 位置: backend/api/multi_function_generator.py")
    print("  - 特点: 寻找能连接多个输入概念的中间概念")
    
    print("\n相似度修改:")
    print("  - 移除: 多维度相关度计算")
    print("  - 保留: 语义相似度（text-embedding-3-small）")
    print("  - 效果: 筛选依据 = 展示分数（逻辑一致）")


if __name__ == "__main__":
    asyncio.run(main())
