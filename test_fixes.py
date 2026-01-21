#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复：
1. LLM必须生成20个概念
2. 简介必须完整不截断
"""

import asyncio
import requests
import json

API_BASE = "http://localhost:8888/api/v1"

async def test_discover():
    """测试功能一：自动跨学科发现"""
    print("\n" + "="*60)
    print("测试功能一：自动跨学科发现")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/discover",
        json={
            "concept": "朴素贝叶斯",
            "max_concepts": 5
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        nodes = data["data"]["nodes"]
        
        print(f"\n✅ 成功返回 {len(nodes)} 个节点")
        
        # 检查中心节点
        center = nodes[0]
        print(f"\n【中心节点】{center['label']}")
        print(f"  一句话简介: {center.get('brief_summary', 'N/A')}")
        print(f"  定义长度: {len(center.get('definition', ''))}")
        print(f"  简介是否完整: {'✅' if len(center.get('brief_summary', '')) > 20 else '❌ 太短/不完整'}")
        
        # 检查相关节点
        print(f"\n【相关节点】共 {len(nodes)-1} 个:")
        for idx, node in enumerate(nodes[1:], 1):
            brief = node.get('brief_summary', 'N/A')
            print(f"{idx}. {node['label']} ({node.get('discipline', 'N/A')})")
            print(f"   相似度: {node.get('similarity', 0):.3f}")
            print(f"   简介: {brief}")
            print(f"   简介完整性: {'✅' if len(brief) > 20 else '❌ 太短'}")
            print()
        
        return True
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    print("开始测试...")
    print("确保后端已启动: python start_backend.py")
    input("按回车开始测试...")
    
    asyncio.run(test_discover())
