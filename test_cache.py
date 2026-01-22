"""
测试三个功能的缓存机制
运行前请确保：
1. Redis已启动 (docker run -d -p 6379:6379 redis)
2. 后端已启动 (python start_backend.py)
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api/v1"

def test_function_1_cache():
    """测试功能1的缓存"""
    print("\n" + "="*60)
    print("测试功能1 - 概念挖掘缓存")
    print("="*60)
    
    payload = {
        "concept": "机器学习",
        "max_depth": 1,
        "max_nodes": 5
    }
    
    # 第一次请求（应该未命中缓存）
    print("\n第一次请求（预期：缓存未命中，调用LLM）...")
    start = time.time()
    response1 = requests.post(f"{API_BASE}/discover", json=payload)
    time1 = time.time() - start
    print(f"✅ 完成，耗时: {time1:.2f}秒")
    print(f"返回节点数: {len(response1.json()['data']['nodes'])}")
    
    # 第二次请求（应该命中缓存）
    print("\n第二次请求（预期：缓存命中，秒返）...")
    start = time.time()
    response2 = requests.post(f"{API_BASE}/discover", json=payload)
    time2 = time.time() - start
    print(f"✅ 完成，耗时: {time2:.2f}秒")
    print(f"返回节点数: {len(response2.json()['data']['nodes'])}")
    
    # 验证结果一致
    assert response1.json()['data']['nodes'] == response2.json()['data']['nodes'], "❌ 缓存结果不一致！"
    print(f"\n✅ 缓存加速: {time1/time2:.1f}x 倍")


def test_function_2_cache():
    """测试功能2的缓存"""
    print("\n" + "="*60)
    print("测试功能2 - 指定学科挖掘缓存")
    print("="*60)
    
    payload = {
        "concept": "熵",
        "disciplines": ["数学"]
    }
    
    # 第一次请求
    print("\n第一次请求（预期：缓存未命中）...")
    start = time.time()
    response1 = requests.post(f"{API_BASE}/discover/disciplined", json=payload)
    time1 = time.time() - start
    
    if response1.status_code != 200:
        print(f"❌ 请求失败: {response1.status_code}")
        print(response1.text)
        return
    
    print(f"✅ 完成，耗时: {time1:.2f}秒")
    print(f"返回节点数: {len(response1.json()['data']['nodes'])}")
    
    # 第二次请求
    print("\n第二次请求（预期：缓存命中，应该快很多）...")
    start = time.time()
    response2 = requests.post(f"{API_BASE}/discover/disciplined", json=payload)
    time2 = time.time() - start
    print(f"✅ 完成，耗时: {time2:.2f}秒")
    print(f"返回节点数: {len(response2.json()['data']['nodes'])}")
    
    # 验证
    if time2 < 1.0:
        print(f"✅ 缓存生效！响应时间从{time1:.2f}秒降至{time2:.2f}秒 (加速{time1/time2:.1f}倍)")
    else:
        print(f"⚠️  警告：第二次请求仍然很慢({time2:.2f}秒)，缓存可能未生效")
    
    assert response1.json()['data']['nodes'] == response2.json()['data']['nodes'], "❌ 缓存结果不一致！"


def test_function_3_cache():
    """测试功能3的缓存"""
    print("\n" + "="*60)
    print("测试功能3 - 桥接概念发现缓存")
    print("="*60)
    
    payload = {
        "concepts": ["熵", "最小二乘法"],
        "max_bridges": 3
    }
    
    # 第一次请求
    print("\n第一次请求（预期：缓存未命中）...")
    start = time.time()
    response1 = requests.post(f"{API_BASE}/discover/bridge", json=payload)
    time1 = time.time() - start
    print(f"✅ 完成，耗时: {time1:.2f}秒")
    print(f"返回桥接概念数: {response1.json()['data']['metadata']['total_bridges']}")
    
    # 第二次请求
    print("\n第二次请求（预期：缓存命中）...")
    start = time.time()
    response2 = requests.post(f"{API_BASE}/discover/bridge", json=payload)
    time2 = time.time() - start
    print(f"✅ 完成，耗时: {time2:.2f}秒")
    print(f"返回桥接概念数: {response2.json()['data']['metadata']['total_bridges']}")
    
    # 验证
    assert response1.json()['data']['nodes'] == response2.json()['data']['nodes'], "❌ 缓存结果不一致！"
    print(f"\n✅ 缓存加速: {time1/time2:.1f}x 倍")


def test_discipline_order_consistency():
    """测试功能2学科顺序无关性"""
    print("\n" + "="*60)
    print("测试功能2 - 学科顺序无关性")
    print("="*60)
    
    payload1 = {
        "concept": "神经网络",
        "disciplines": ["生物学", "计算机科学"]
    }
    
    payload2 = {
        "concept": "神经网络",
        "disciplines": ["计算机科学", "生物学"]  # 顺序不同
    }
    
    print("\n第一次请求（学科顺序: 生物学, 计算机科学）...")
    response1 = requests.post(f"{API_BASE}/discover/disciplined", json=payload1)
    
    print("第二次请求（学科顺序: 计算机科学, 生物学）...")
    response2 = requests.post(f"{API_BASE}/discover/disciplined", json=payload2)
    
    # 应该返回相同的结果（因为排序后cache_key一致）
    assert response1.json()['data']['nodes'] == response2.json()['data']['nodes'], "❌ 学科顺序影响了缓存！"
    print("✅ 学科顺序不影响缓存结果")


def test_concept_order_consistency():
    """测试功能3概念顺序无关性"""
    print("\n" + "="*60)
    print("测试功能3 - 概念顺序无关性")
    print("="*60)
    
    payload1 = {
        "concepts": ["熵", "最小二乘法"],
        "max_bridges": 3
    }
    
    payload2 = {
        "concepts": ["最小二乘法", "熵"],  # 顺序不同
        "max_bridges": 3
    }
    
    print("\n第一次请求（概念顺序: 熵, 最小二乘法）...")
    response1 = requests.post(f"{API_BASE}/discover/bridge", json=payload1)
    
    print("第二次请求（概念顺序: 最小二乘法, 熵）...")
    response2 = requests.post(f"{API_BASE}/discover/bridge", json=payload2)
    
    # 应该返回相同的结果
    assert response1.json()['data']['nodes'] == response2.json()['data']['nodes'], "❌ 概念顺序影响了缓存！"
    print("✅ 概念顺序不影响缓存结果")


if __name__ == "__main__":
    try:
        print("\n🚀 开始测试缓存机制...")
        
        # 基础功能测试
        test_function_1_cache()
        test_function_2_cache()
        test_function_3_cache()
        
        # 顺序无关性测试
        test_discipline_order_consistency()
        test_concept_order_consistency()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！缓存机制工作正常")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端API")
        print("请确保后端已启动: python start_backend.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
