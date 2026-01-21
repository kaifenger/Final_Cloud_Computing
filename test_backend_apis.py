#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试后端所有API端点"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """测试所有API端点"""
    
    print("=" * 60)
    print("后端API测试开始")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. 测试根路径
        print("\n[1] 测试根路径 GET /")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            return False
        
        # 2. 测试概念挖掘
        print("\n[2] 测试概念挖掘 POST /api/v1/discover")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/discover",
                json={"concept": "深度学习", "depth": 2, "max_concepts": 30}
            )
            print(f"   状态码: {response.status_code}")
            data = response.json()
            print(f"   节点数: {len(data['data']['nodes'])}")
            print(f"   边数: {len(data['data']['edges'])}")
            print(f"   模式: {data['data']['metadata'].get('mode', 'unknown')}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 3. 测试Arxiv搜索
        print("\n[3] 测试Arxiv搜索 GET /api/v1/arxiv/search?query=deep learning")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/arxiv/search",
                params={"query": "deep learning", "max_results": 3}
            )
            print(f"   状态码: {response.status_code}")
            data = response.json()
            print(f"   论文数: {data['data']['total']}")
            if data['data'].get('error'):
                print(f"   错误: {data['data']['error']}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 4. 测试节点展开
        print("\n[4] 测试节点展开 POST /api/v1/expand")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/expand",
                json={
                    "node_id": "test_node_1",
                    "node_label": "机器学习",
                    "existing_nodes": [],
                    "max_new_nodes": 5
                }
            )
            print(f"   状态码: {response.status_code}")
            data = response.json()
            print(f"   新增节点: {len(data['data']['nodes'])}")
            print(f"   新增边: {len(data['data']['edges'])}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 5. 测试AI问答
        print("\n[5] 测试AI问答 POST /api/v1/ai/chat")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ai/chat",
                json={
                    "question": "什么是深度学习?",
                    "concept": "深度学习",
                    "context": "深度学习是机器学习的一个分支"
                }
            )
            print(f"   状态码: {response.status_code}")
            data = response.json()
            print(f"   回答: {data['data']['answer'][:100]}...")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        # 6. 测试API文档
        print("\n[6] 测试API文档 GET /docs")
        try:
            response = await client.get(f"{BASE_URL}/docs")
            print(f"   状态码: {response.status_code}")
            print(f"   ✅ API文档可访问")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 后端API测试完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_api_endpoints())
    except KeyboardInterrupt:
        print("\n测试中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
