#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单API测试 - 验证功能可用性
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("="*80)
print("API可用性测试")
print("="*80)

# 测试健康检查
print("\n1. 健康检查...")
try:
    resp = requests.get("http://localhost:8000/health", timeout=5)
    if resp.status_code == 200:
        print("   ✅ 后端服务正常运行")
    else:
        print(f"   ⚠️ 后端响应异常: {resp.status_code}")
except Exception as e:
    print(f"   ❌ 无法连接后端: {e}")
    print("\n请先启动后端:")
    print("   cd backend && py -3.11 -m uvicorn main:app --port 8000")
    exit(1)

# 测试功能1
print("\n2. 测试功能1（自动跨学科）...")
try:
    resp = requests.post(
        f"{BASE_URL}/discover",
        json={"concept": "神经网络", "max_concepts": 5},
        timeout=120
    )
    if resp.status_code == 200:
        data = resp.json()
        nodes = data['data']['nodes']
        print(f"   ✅ 功能1成功 - 生成{len(nodes)}个节点")
        
        # 检查数据结构
        if len(nodes) > 1:
            sample = nodes[1]
            has_sim = 'similarity' in sample
            no_composite = 'composite_score' not in sample
            print(f"   {'✅' if has_sim else '❌'} similarity字段存在")
            print(f"   {'✅' if no_composite else '❌'} composite_score已移除")
    else:
        print(f"   ❌ 功能1失败: {resp.status_code}")
except Exception as e:
    print(f"   ❌ 功能1异常: {e}")

# 测试功能2
print("\n3. 测试功能2（指定学科）...")
try:
    resp = requests.post(
        f"{BASE_URL}/discover/disciplined",
        json={
            "concept": "神经网络",
            "disciplines": ["生物学", "数学"],
            "max_concepts": 5
        },
        timeout=120
    )
    if resp.status_code == 200:
        data = resp.json()
        nodes = data['data']['nodes']
        print(f"   ✅ 功能2成功 - 生成{len(nodes)}个节点")
    else:
        print(f"   ❌ 功能2失败: {resp.status_code}")
except Exception as e:
    print(f"   ❌ 功能2异常: {e}")

# 测试功能3
print("\n3. 测试功能3（桥梁发现）...")
try:
    resp = requests.post(
        f"{BASE_URL}/discover/bridge",
        json={
            "concepts": ["熵", "最小二乘法"],
            "max_bridges": 5
        },
        timeout=120
    )
    if resp.status_code == 200:
        data = resp.json()
        nodes = data['data']['nodes']
        print(f"   ✅ 功能3成功 - 生成{len(nodes)}个节点")
    else:
        print(f"   ❌ 功能3失败: {resp.status_code}")
except Exception as e:
    print(f"   ❌ 功能3异常: {e}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
