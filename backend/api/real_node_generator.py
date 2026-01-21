#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实节点生成器 - 使用LLM和语义相似度
"""

import os
import asyncio
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ==================== LLM客户端 ====================
_llm_client = None
_embedding_client = None

def get_llm_client():
    """获取LLM客户端（用于文本生成）"""
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            _llm_client = AsyncOpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )
            print("[INFO] LLM客户端已初始化（文本生成）")
    return _llm_client


def get_embedding_client():
    """获取Embedding客户端（用于相似度计算）"""
    global _embedding_client
    if _embedding_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            _embedding_client = AsyncOpenAI(api_key=api_key)
            print("[INFO] Embedding客户端已初始化（OpenAI）")
    return _embedding_client


# ==================== LLM生成相关概念 ====================

async def generate_related_concepts(
    parent_concept: str,
    existing_concepts: List[str],
    max_count: int = 5
) -> List[Dict[str, str]]:
    """
    使用LLM生成相关概念
    
    Args:
        parent_concept: 父概念名称
        existing_concepts: 已存在的概念列表
        max_count: 最大生成数量
        
    Returns:
        [{"name": "概念名", "discipline": "学科", "relation": "关系类型"}, ...]
    """
    client = get_llm_client()
    if not client:
        print("[WARNING] LLM客户端未初始化，使用预定义概念")
        return _get_fallback_concepts(parent_concept)
    
    # 构建提示词
    existing_str = "、".join(existing_concepts) if existing_concepts else "无"
    prompt = f"""请为概念"{parent_concept}"生成{max_count}个相关的学术概念。

要求：
1. 每个概念必须是真实存在的学术概念
2. 与"{parent_concept}"有明确的学术关联
3. 不要包含已存在的概念：{existing_str}
4. 覆盖不同的关系类型：理论基础、方法论、应用领域、子领域等

输出格式（每行一个概念）：
概念名|学科|关系类型

示例：
机器学习|计算机科学|sub_field
神经网络|人工智能|foundation
监督学习|方法论|methodology

请直接输出{max_count}个概念，不要任何解释："""

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
                messages=[
                    {"role": "system", "content": "你是一个专业的学术概念生成助手，擅长识别概念间的学术关联。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            ),
            timeout=15.0
        )
        
        if response and response.choices:
            content = response.choices[0].message.content.strip()
            concepts = []
            
            for line in content.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        concepts.append({
                            "name": parts[0].strip(),
                            "discipline": parts[1].strip(),
                            "relation": parts[2].strip()
                        })
            
            if concepts:
                print(f"[SUCCESS] LLM生成了{len(concepts)}个相关概念")
                return concepts[:max_count]
    
    except asyncio.TimeoutError:
        print(f"[WARNING] LLM生成超时，使用预定义概念")
    except Exception as e:
        print(f"[WARNING] LLM生成失败: {str(e)}，使用预定义概念")
    
    return _get_fallback_concepts(parent_concept)


def _get_fallback_concepts(parent_concept: str) -> List[Dict[str, str]]:
    """预定义概念映射（作为回退方案）"""
    domain_mapping = {
        "机器学习": [
            {"name": "深度学习", "discipline": "计算机科学", "relation": "sub_field"},
            {"name": "神经网络", "discipline": "人工智能", "relation": "foundation"},
            {"name": "监督学习", "discipline": "方法论", "relation": "methodology"},
        ],
        "深度学习": [
            {"name": "卷积神经网络", "discipline": "计算机科学", "relation": "sub_field"},
            {"name": "反向传播", "discipline": "算法", "relation": "methodology"},
            {"name": "计算机视觉", "discipline": "应用领域", "relation": "application"},
        ],
    }
    
    if parent_concept in domain_mapping:
        return domain_mapping[parent_concept]
    
    # 通用回退
    return [
        {"name": f"{parent_concept}理论", "discipline": "理论基础", "relation": "theoretical_foundation"},
        {"name": f"{parent_concept}方法", "discipline": "方法论", "relation": "methodology"},
        {"name": f"{parent_concept}应用", "discipline": "应用领域", "relation": "application"},
    ]


# ==================== 语义相似度计算 ====================

async def compute_similarity(concept1: str, concept2: str) -> float:
    """
    计算两个概念的语义相似度
    
    Args:
        concept1: 概念1
        concept2: 概念2
        
    Returns:
        相似度分数 [0, 1]
    """
    client = get_embedding_client()
    if not client:
        print("[WARNING] Embedding客户端未初始化，返回默认相似度")
        return 0.75
    
    try:
        # 获取embeddings
        response = await asyncio.wait_for(
            client.embeddings.create(
                model="text-embedding-3-small",
                input=[concept1, concept2]
            ),
            timeout=10.0
        )
        
        emb1 = np.array(response.data[0].embedding)
        emb2 = np.array(response.data[1].embedding)
        
        # 计算余弦相似度
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # 归一化到 [0, 1]
        normalized = (similarity + 1) / 2
        
        print(f"[SUCCESS] 相似度计算: {concept1} <-> {concept2} = {normalized:.3f}")
        return float(normalized)
    
    except asyncio.TimeoutError:
        print(f"[WARNING] 相似度计算超时")
        return 0.75
    except Exception as e:
        print(f"[WARNING] 相似度计算失败: {str(e)}")
        return 0.75


async def compute_credibility(
    concept: str,
    parent_concept: str,
    has_wikipedia: bool = False
) -> float:
    """
    计算节点可信度
    
    公式: base_credibility * (0.7 + 0.3 * similarity)
    
    Args:
        concept: 当前概念
        parent_concept: 父概念
        has_wikipedia: 是否有Wikipedia定义
        
    Returns:
        可信度分数 [0, 1]
    """
    # 基础可信度
    base = 0.95 if has_wikipedia else 0.70
    
    # 计算语义相似度
    similarity = await compute_similarity(concept, parent_concept)
    
    # 动态可信度
    credibility = base * (0.7 + 0.3 * similarity)
    
    print(f"[INFO] 可信度: {concept} = {credibility:.3f} (base={base}, similarity={similarity:.3f})")
    
    return credibility


# ==================== 学术概念过滤 ====================

async def is_academic_concept(concept: str) -> bool:
    """
    判断是否为学术概念
    
    Args:
        concept: 概念名称
        
    Returns:
        True表示是学术概念，False表示非学术
    """
    client = get_llm_client()
    if not client:
        return True  # 默认允许
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
                messages=[
                    {
                        "role": "system",
                        "content": "你是学术概念过滤器。判断输入是否为学术概念。只回答'是'或'否'。"
                    },
                    {
                        "role": "user",
                        "content": f"'{concept}' 是学术概念吗？"
                    }
                ],
                temperature=0.1,
                max_tokens=10
            ),
            timeout=5.0
        )
        
        if response and response.choices:
            answer = response.choices[0].message.content.strip()
            is_academic = "是" in answer or "yes" in answer.lower()
            print(f"[INFO] 学术过滤: {concept} = {'学术概念' if is_academic else '非学术'}")
            return is_academic
    
    except Exception as e:
        print(f"[WARNING] 学术过滤失败: {str(e)}")
    
    return True  # 默认允许


# ==================== 测试函数 ====================

async def test_real_generator():
    """测试真实生成器"""
    print("=" * 60)
    print("测试真实节点生成器")
    print("=" * 60)
    
    # 1. 测试LLM生成概念
    print("\n[1] 测试LLM生成相关概念...")
    concepts = await generate_related_concepts("机器学习", [], max_count=3)
    for c in concepts:
        print(f"   - {c['name']} ({c['discipline']}) - {c['relation']}")
    
    # 2. 测试相似度计算
    print("\n[2] 测试相似度计算...")
    sim1 = await compute_similarity("机器学习", "深度学习")
    sim2 = await compute_similarity("机器学习", "笨蛋")
    print(f"   机器学习 <-> 深度学习: {sim1:.3f}")
    print(f"   机器学习 <-> 笨蛋: {sim2:.3f}")
    
    # 3. 测试可信度计算
    print("\n[3] 测试可信度计算...")
    cred1 = await compute_credibility("深度学习", "机器学习", has_wikipedia=True)
    cred2 = await compute_credibility("未知概念", "机器学习", has_wikipedia=False)
    print(f"   深度学习 (有Wiki): {cred1:.3f}")
    print(f"   未知概念 (无Wiki): {cred2:.3f}")
    
    # 4. 测试学术过滤
    print("\n[4] 测试学术概念过滤...")
    is_ac1 = await is_academic_concept("熵")
    is_ac2 = await is_academic_concept("笨蛋")
    print(f"   熵: {'学术' if is_ac1 else '非学术'}")
    print(f"   笨蛋: {'学术' if is_ac2 else '非学术'}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_real_generator())
