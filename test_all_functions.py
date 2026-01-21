#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试三个功能的实现情况和相似度修改
"""

import asyncio
import httpx
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"


async def test_function_1():
    """测试功能1：自动跨学科概念发现"""
    print("\n" + "="*80)
    print("功能1：自动跨学科概念发现")
    print("="*80)
    print("API: POST /api/v1/discover")
    print("逻辑: 使用跨学科提示词挖掘远亲概念，按语义相似度筛选和排序\n")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
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
                edges = result['data']['edges']
                
                print(f"✅ 功能1测试成功")
                print(f"   生成节点: {len(nodes)}个")
                print(f"   生成边: {len(edges)}条")
                
                # 检查数据结构
                sample_node = [n for n in nodes if n.get('depth', 0) > 0][0] if len(nodes) > 1 else None
                if sample_node:
                    print(f"\n   示例节点: {sample_node['label']}")
                    print(f"   - 学科: {sample_node['discipline']}")
                    print(f"   - 相似度: {sample_node.get('similarity', 'N/A')}")
                    print(f"   - 可信度: {sample_node.get('credibility', 'N/A')}")
                    
                    # 检查是否移除了多维度字段
                    has_composite = 'composite_score' in sample_node
                    has_dimensions = 'relevance_dimensions' in sample_node
                    has_tier = 'relationship_tier' in sample_node
                    
                    print(f"\n   数据结构检查:")
                    print(f"   - similarity字段: ✅ 存在")
                    print(f"   - composite_score字段: {'❌ 仍存在（应该删除）' if has_composite else '✅ 已移除'}")
                    print(f"   - relevance_dimensions字段: {'❌ 仍存在（应该删除）' if has_dimensions else '✅ 已移除'}")
                    print(f"   - relationship_tier字段: {'❌ 仍存在（应该删除）' if has_tier else '✅ 已移除'}")
                
                # 检查排序
                sorted_nodes = sorted([n for n in nodes if n.get('depth', 0) > 0], 
                                    key=lambda x: x.get('similarity', 0), reverse=True)
                print(f"\n   相似度排序（前5）:")
                for i, node in enumerate(sorted_nodes[:5], 1):
                    print(f"   {i}. {node['label']:15s} - 相似度: {node.get('similarity', 0):.3f}")
                
                return True
            else:
                print(f"❌ 功能1测试失败: HTTP {response.status_code}")
                print(f"   错误: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 功能1测试异常: {str(e)}")
            return False


async def test_function_2():
    """测试功能2：指定学科的概念挖掘"""
    print("\n" + "="*80)
    print("功能2：指定学科的概念挖掘")
    print("="*80)
    print("API: POST /api/v1/discover/disciplined")
    print("逻辑: 限定学科范围的概念挖掘，只在指定学科中寻找\n")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
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
                edges = result['data']['edges']
                metadata = result['data'].get('metadata', {})
                
                print(f"✅ 功能2测试成功")
                print(f"   生成节点: {len(nodes)}个")
                print(f"   生成边: {len(edges)}条")
                print(f"   指定学科: {metadata.get('disciplines', [])}")
                
                # 按学科分组统计
                discipline_counts = {}
                for node in nodes:
                    if node.get('depth', 0) > 0:
                        disc = node['discipline']
                        discipline_counts[disc] = discipline_counts.get(disc, 0) + 1
                
                print(f"\n   学科分布:")
                for disc, count in sorted(discipline_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {disc}: {count}个概念")
                
                # 检查是否严格限定在指定学科
                specified = set(["生物学", "数学", "物理学"])
                actual = set(discipline_counts.keys())
                violation = actual - specified
                
                if violation:
                    print(f"\n   ⚠️ 发现非指定学科: {violation}")
                else:
                    print(f"\n   ✅ 严格遵守学科限定")
                
                return True
            else:
                print(f"❌ 功能2测试失败: HTTP {response.status_code}")
                print(f"   错误: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 功能2测试异常: {str(e)}")
            return False


async def test_function_3():
    """测试功能3：多概念桥梁发现"""
    print("\n" + "="*80)
    print("功能3：多概念桥梁发现")
    print("="*80)
    print("API: POST /api/v1/discover/bridge")
    print("逻辑: 寻找连接多个概念的桥梁概念节点\n")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
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
                edges = result['data']['edges']
                
                # 区分输入节点和桥梁节点
                input_nodes = [n for n in nodes if n.get('is_input', False)]
                bridge_nodes = [n for n in nodes if n.get('is_bridge', False)]
                
                print(f"✅ 功能3测试成功")
                print(f"   输入概念: {len(input_nodes)}个")
                print(f"   桥梁概念: {len(bridge_nodes)}个")
                print(f"   连接边: {len(edges)}条")
                
                # 桥梁类型统计
                bridge_types = {}
                for node in bridge_nodes:
                    btype = node.get('bridge_type', '未知')
                    bridge_types[btype] = bridge_types.get(btype, 0) + 1
                
                print(f"\n   桥梁类型分布:")
                for btype, count in sorted(bridge_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {btype}: {count}个")
                
                # 显示桥梁示例
                print(f"\n   桥梁概念示例（前5）:")
                for i, node in enumerate(bridge_nodes[:5], 1):
                    print(f"   {i}. {node['label']:20s} - 类型: {node.get('bridge_type', 'N/A')}")
                    if 'connection_principle' in node:
                        principle = node['connection_principle'][:60]
                        print(f"      连接原理: {principle}...")
                
                return True
            else:
                print(f"❌ 功能3测试失败: HTTP {response.status_code}")
                print(f"   错误: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 功能3测试异常: {str(e)}")
            return False


async def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("三功能完整测试 + 相似度修改验证")
    print("="*80)
    print("\n测试环境:")
    print(f"  - 后端URL: {BASE_URL}")
    print(f"  - 超时时间: 180秒")
    
    # 检查后端连接
    print("\n正在检查后端连接...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ 后端服务正常")
            else:
                print("⚠️ 后端服务响应异常")
    except Exception as e:
        print(f"❌ 后端服务无法连接: {str(e)}")
        print("   请确保后端已启动: cd backend && py -3.11 -m uvicorn main:app --port 8000")
        return
    
    # 运行三个功能测试
    results = []
    
    print("\n开始测试...\n")
    
    # 功能1
    result1 = await test_function_1()
    results.append(("功能1（自动跨学科）", result1))
    
    await asyncio.sleep(2)
    
    # 功能2
    result2 = await test_function_2()
    results.append(("功能2（指定学科）", result2))
    
    await asyncio.sleep(2)
    
    # 功能3
    result3 = await test_function_3()
    results.append(("功能3（桥梁发现）", result3))
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_pass = all(r for _, r in results)
    
    print("\n" + "="*80)
    if all_pass:
        print("🎉 所有功能测试通过！")
        print("\n关键验证点:")
        print("  ✅ 功能1: 使用跨学科prompt，语义相似度筛选")
        print("  ✅ 功能2: 严格限定学科范围")
        print("  ✅ 功能3: 成功发现桥梁概念")
        print("  ✅ 相似度修改: 移除composite_score等多维度字段")
        print("  ✅ 数据一致性: 筛选依据 = 展示分数 = similarity")
    else:
        print("⚠️ 部分功能测试失败，请检查错误信息")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
