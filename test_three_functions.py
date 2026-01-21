#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三功能测试脚本
测试功能1（现有）、功能2（指定学科）、功能3（桥梁发现）
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"


async def check_backend():
    """检查后端是否在线"""
    print("检查后端服务...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ 后端服务在线\n")
                return True
            else:
                print(f"⚠️ 后端服务响应异常: {response.status_code}\n")
                return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        print(f"\n请先启动后端:")
        print(f"  py -3.11 start_backend.py")
        print(f"  或者: cd backend && py -3.11 -m uvicorn main:app --reload --port 8000\n")
        return False


async def test_function_1():
    """测试功能1：不选学科的自动跨学科挖掘"""
    print("\n" + "="*70)
    print("测试功能1：自动跨学科概念挖掘（现有功能）")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 增加到3分钟
        response = await client.post(
            f"{BASE_URL}/discover",
            json={
                "concept": "神经网络",
                "max_concepts": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 功能1测试成功")
            print(f"   状态: {result['status']}")
            print(f"   生成节点数: {len(result['data']['nodes'])}")
            print(f"   生成边数: {len(result['data']['edges'])}")
            
            print(f"\n   概念列表:")
            for node in result['data']['nodes'][:5]:
                print(f"     - {node['label']} ({node.get('discipline', 'N/A')}) - 相似度: {node.get('similarity', 'N/A')}")
        else:
            print(f"❌ 功能1测试失败: {response.status_code}")
            print(response.text)


async def test_function_2():
    """测试功能2：指定学科的概念挖掘"""
    print("\n" + "="*70)
    print("测试功能2：指定学科的概念挖掘（新功能）")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 增加到3分钟
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
            print(f"✅ 功能2测试成功")
            print(f"   状态: {result['status']}")
            print(f"   输入概念: {result['data']['metadata']['input_concept']}")
            print(f"   指定学科: {', '.join(result['data']['metadata']['disciplines'])}")
            print(f"   生成节点数: {result['data']['metadata']['total_concepts']}")
            
            print(f"\n   概念列表（按学科分组）:")
            nodes_by_discipline = {}
            for node in result['data']['nodes'][1:]:  # 跳过中心节点
                disc = node.get('discipline', '未知')
                if disc not in nodes_by_discipline:
                    nodes_by_discipline[disc] = []
                nodes_by_discipline[disc].append(node)
            
            for disc, nodes in nodes_by_discipline.items():
                print(f"\n   【{disc}】:")
                for node in nodes:
                    print(f"     - {node['label']} (相似度: {node.get('similarity', 'N/A'):.3f})")
        else:
            print(f"❌ 功能2测试失败: {response.status_code}")
            print(response.text)


async def test_function_3():
    """测试功能3：多概念桥梁发现"""
    print("\n" + "="*70)
    print("测试功能3：多概念桥梁发现（新功能）")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 增加到3分钟
        response = await client.post(
            f"{BASE_URL}/discover/bridge",
            json={
                "concepts": ["熵", "最小二乘法"],
                "max_bridges": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 功能3测试成功")
            print(f"   状态: {result['status']}")
            print(f"   输入概念: {', '.join(result['data']['metadata']['input_concepts'])}")
            print(f"   桥梁概念数: {result['data']['metadata']['total_bridges']}")
            print(f"   桥梁类型分布: {result['data']['metadata']['bridge_types']}")
            
            print(f"\n   桥梁概念列表:")
            for node in result['data']['nodes']:
                if node.get('is_bridge', False):
                    print(f"     - {node['label']} ({node.get('bridge_type', 'N/A')})")
                    print(f"       连接原理: {node.get('connection_principle', 'N/A')[:80]}...")
        else:
            print(f"❌ 功能3测试失败: {response.status_code}")
            print(response.text)


async def test_all():
    """运行所有测试"""
    print("\n" + "="*70)
    print("跨学科知识图谱三功能测试")
    print("="*70)
    
    # 先检查后端是否在线
    if not await check_backend():
        return
    
    await test_function_1()
    await asyncio.sleep(1)  # 避免请求过快
    
    await test_function_2()
    await asyncio.sleep(1)
    
    await test_function_3()
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_all())
