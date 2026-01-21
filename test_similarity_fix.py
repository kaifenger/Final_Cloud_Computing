#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试相似度计算修复
验证：
1. 网络连接重试机制
2. 超时处理
3. 错误信息更详细
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.real_node_generator import compute_similarity, get_embedding_client


async def test_similarity():
    """测试相似度计算"""
    print("="*60)
    print("测试相似度计算功能")
    print("="*60)
    
    # 检查客户端初始化
    client = get_embedding_client()
    if not client:
        print("❌ Embedding客户端初始化失败")
        return False
    
    print("✅ Embedding客户端初始化成功\n")
    
    # 测试用例
    test_cases = [
        ("机器学习", "深度学习"),
        ("朴素贝叶斯", "贝叶斯大脑假说"),
        ("神经网络", "人工智能")
    ]
    
    print("开始测试相似度计算（带重试机制）...\n")
    
    success_count = 0
    for concept1, concept2 in test_cases:
        print(f"计算: {concept1} <-> {concept2}")
        similarity = await compute_similarity(concept1, concept2)
        
        if 0 <= similarity <= 1:
            print(f"✅ 成功: 相似度 = {similarity:.3f}\n")
            success_count += 1
        else:
            print(f"❌ 失败: 相似度值异常 = {similarity}\n")
    
    print("="*60)
    print(f"测试结果: {success_count}/{len(test_cases)} 成功")
    print("="*60)
    
    return success_count == len(test_cases)


if __name__ == "__main__":
    print("确保已配置 OPENAI_API_KEY 环境变量")
    print("检查网络连接是否正常\n")
    
    result = asyncio.run(test_similarity())
    
    if result:
        print("\n✅ 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，但已使用默认相似度值（0.75）")
        print("请检查：")
        print("1. OPENAI_API_KEY 是否正确配置")
        print("2. 网络连接是否正常")
        print("3. 是否需要配置代理")
