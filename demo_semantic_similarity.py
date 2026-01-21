#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义相似度演示 - 展示embedding模型如何计算概念相似度
"""

import os
import asyncio
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载环境变量
load_dotenv()

async def compute_similarity(concept1: str, concept2: str, client) -> float:
    """计算两个概念的语义相似度"""
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=[concept1, concept2]
        )
        
        # 获取1536维向量
        emb1 = np.array(response.data[0].embedding)
        emb2 = np.array(response.data[1].embedding)
        
        # 计算余弦相似度（范围 -1 到 1）
        cosine_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # 归一化到 0-1 范围
        normalized = (cosine_sim + 1) / 2
        
        return float(normalized)
    except Exception as e:
        print(f"❌ 计算失败: {e}")
        return 0.0


async def demo_semantic_similarity():
    """演示不同类型概念对的语义相似度"""
    
    print("=" * 80)
    print("语义相似度演示 - OpenAI text-embedding-3-small")
    print("=" * 80)
    
    # 初始化客户端
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未找到 OPENAI_API_KEY")
        return
    
    client = AsyncOpenAI(api_key=api_key)
    
    # 测试案例分组
    test_cases = {
        "📚 同义词/近义词（应该非常相似）": [
            ("神经网络", "人工神经网络"),
            ("机器学习", "机器学习算法"),
            ("深度学习", "深层神经网络"),
        ],
        
        "🔗 强相关概念（同领域核心概念）": [
            ("神经网络", "反向传播"),
            ("神经网络", "感知器"),
            ("神经网络", "激活函数"),
        ],
        
        "🌉 跨学科概念（原理相通，表述不同）": [
            ("神经网络", "电路网络"),
            ("神经网络", "Hopfield网络"),
            ("反向传播", "梯度下降"),
        ],
        
        "🔄 远距离相关（间接关联）": [
            ("神经网络", "贝叶斯定理"),
            ("神经网络", "决策树"),
            ("神经网络", "遗传算法"),
        ],
        
        "❌ 弱相关/无关概念": [
            ("神经网络", "量子力学"),
            ("神经网络", "经济学"),
            ("神经网络", "文学创作"),
        ],
    }
    
    print("\n💡 **语义相似度的含义**:")
    print("   通过将概念转换为1536维向量（embedding），计算向量间的余弦相似度")
    print("   - 相似度 = cos(θ) 归一化到 [0, 1]")
    print("   - 分数越高，表示两个概念在语义空间中距离越近")
    print("   - 能捕捉语义相似，但对跨学科的原理相似性识别有限\n")
    
    all_results = []
    
    for category, pairs in test_cases.items():
        print("\n" + "=" * 80)
        print(f"{category}")
        print("=" * 80)
        
        for concept1, concept2 in pairs:
            similarity = await compute_similarity(concept1, concept2, client)
            all_results.append((concept1, concept2, similarity, category))
            
            # 根据相似度着色
            if similarity >= 0.75:
                indicator = "🟢 极高"
            elif similarity >= 0.65:
                indicator = "🟡 高"
            elif similarity >= 0.55:
                indicator = "🟠 中等"
            else:
                indicator = "🔴 低"
            
            print(f"{indicator}  {concept1:15s} ←→ {concept2:20s}  相似度: {similarity:.4f}")
            
            # 稍作延迟，避免API限流
            await asyncio.sleep(0.3)
    
    # 总结分析
    print("\n" + "=" * 80)
    print("📊 分数分布分析")
    print("=" * 80)
    
    all_scores = [r[2] for r in all_results]
    print(f"最高相似度: {max(all_scores):.4f}")
    print(f"最低相似度: {min(all_scores):.4f}")
    print(f"平均相似度: {np.mean(all_scores):.4f}")
    print(f"分数范围:   {max(all_scores) - min(all_scores):.4f}")
    
    # 找出最相似和最不相似的对
    sorted_results = sorted(all_results, key=lambda x: x[2], reverse=True)
    
    print(f"\n🏆 最相似的3组:")
    for i, (c1, c2, score, cat) in enumerate(sorted_results[:3], 1):
        print(f"   {i}. {c1} ←→ {c2}: {score:.4f} ({cat})")
    
    print(f"\n❌ 最不相似的3组:")
    for i, (c1, c2, score, cat) in enumerate(sorted_results[-3:], 1):
        print(f"   {i}. {c1} ←→ {c2}: {score:.4f} ({cat})")
    
    # 重要发现
    print("\n" + "=" * 80)
    print("🔍 关键发现")
    print("=" * 80)
    print("1. 同义词/近义词：通常 > 0.80（embedding模型擅长）")
    print("2. 同领域强相关：通常 0.65-0.80（较好识别）")
    print("3. 跨学科概念：通常 0.55-0.70（识别能力有限）⚠️")
    print("4. 远距离相关：通常 0.50-0.60（难以准确判断）")
    print("5. 无关概念：通常 < 0.55（能有效排除）")
    print("\n💡 启示：单纯用语义相似度筛选节点，可能错过原理相通但表述不同的跨学科概念")


if __name__ == "__main__":
    asyncio.run(demo_semantic_similarity())
