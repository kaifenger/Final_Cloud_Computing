#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的相关度计算模块
实现多维度相关度评估
"""

import asyncio
from typing import Dict, Tuple
from openai import AsyncOpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 学科距离矩阵（0-1，越大表示距离越远）
DISCIPLINE_DISTANCE = {
    # 数学相关
    ("数学", "物理学"): 0.3,
    ("数学", "计算机科学"): 0.4,
    ("数学", "统计学"): 0.2,
    ("数学", "经济学"): 0.6,
    ("数学", "生物学"): 0.7,
    ("数学", "社会学"): 0.9,
    
    # 物理学相关
    ("物理学", "计算机科学"): 0.5,
    ("物理学", "生物学"): 0.7,
    ("物理学", "工程学"): 0.4,
    ("物理学", "社会学"): 0.9,
    
    # 计算机科学相关
    ("计算机科学", "生物学"): 0.6,
    ("计算机科学", "经济学"): 0.5,
    ("计算机科学", "社会学"): 0.7,
    ("计算机科学", "工程学"): 0.3,
    
    # 生物学相关
    ("生物学", "社会学"): 0.6,
    ("生物学", "医学"): 0.3,
    ("生物学", "心理学"): 0.5,
    
    # 其他
    ("经济学", "社会学"): 0.4,
    ("心理学", "社会学"): 0.4,
}


def compute_cross_discipline_strength(disc1: str, disc2: str) -> float:
    """
    计算跨学科强度
    
    Args:
        disc1: 学科1
        disc2: 学科2
        
    Returns:
        跨学科强度 [0, 1]，越大表示跨度越大
    """
    # 同学科返回低分（我们要的是跨学科）
    if disc1 == disc2:
        return 0.2
    
    # 标准化学科名称（去除"学"后缀）
    def normalize(disc: str) -> str:
        return disc.replace("学", "").strip()
    
    d1 = normalize(disc1)
    d2 = normalize(disc2)
    
    # 查找距离（双向查找）
    pair = tuple(sorted([d1, d2]))
    distance = DISCIPLINE_DISTANCE.get(pair, None)
    
    if distance is None:
        # 尝试原始名称
        pair = tuple(sorted([disc1, disc2]))
        distance = DISCIPLINE_DISTANCE.get(pair, 0.5)  # 默认中等距离
    
    return distance


async def evaluate_principle_alignment(
    concept1: str,
    concept2: str,
    cross_principle: str,
    llm_client: AsyncOpenAI
) -> float:
    """
    使用LLM评估原理一致性
    
    Args:
        concept1: 概念1
        concept2: 概念2
        cross_principle: 跨学科原理描述
        llm_client: LLM客户端
        
    Returns:
        原理一致性分数 [0, 1]
    """
    prompt = f"""你是学术原理评估专家。请评估两个概念的底层原理一致性。

概念1: {concept1}
概念2: {concept2}
跨学科原理: {cross_principle}

评分标准（0-10分）：
- 9-10分: 数学形式完全一致（如熵在信息论和热力学，公式完全相同）
- 7-8分:  物理机制相同（如神经网络和Hopfield网络，都基于能量最小化）
- 5-6分:  方法论相似（如遗传算法和进化论，都是变异-选择机制）
- 3-4分:  类比关系（如社交网络和神经网络，都是网络结构）
- 1-2分:  仅表面关联（如命名相似但原理不同）
- 0分:    无关联

仅输出0-10的整数分数："""
    
    try:
        response = await asyncio.wait_for(
            llm_client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-3-flash-preview"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=5,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=15.0
        )
        
        score_str = response.choices[0].message.content.strip()
        score = int(''.join(filter(str.isdigit, score_str)) or "5")  # 提取数字
        score = max(0, min(10, score))  # 限制范围
        
        print(f"[INFO] 原理一致性评估: {concept1} <-> {concept2} = {score}/10")
        
        return score / 10.0
    
    except asyncio.TimeoutError:
        print(f"[WARNING] 原理评估超时，返回默认值0.5")
        return 0.5
    except Exception as e:
        print(f"[WARNING] 原理评估失败: {e}，返回默认值0.5")
        return 0.5


def compute_novelty_score(concept1: str, concept2: str) -> float:
    """
    计算新颖度（基于常见性的倒数）
    
    简化版本：基于概念对的预设常见度
    完整版本：查询学术文献共现频率
    
    Args:
        concept1: 概念1
        concept2: 概念2
        
    Returns:
        新颖度分数 [0, 1]，越大表示越新颖
    """
    # 常见概念对（常见度分数）
    COMMON_PAIRS = {
        ("神经网络", "深度学习"): 0.95,
        ("神经网络", "反向传播"): 0.90,
        ("神经网络", "卷积神经网络"): 0.92,
        ("神经网络", "感知器"): 0.75,
        ("神经网络", "机器学习"): 0.88,
        ("神经网络", "Hopfield网络"): 0.60,
        ("神经网络", "玻尔兹曼机"): 0.50,
        ("神经网络", "突触可塑性"): 0.40,
        ("神经网络", "量子计算"): 0.15,
        ("神经网络", "社会网络分析"): 0.25,
        ("神经网络", "细胞自动机"): 0.30,
    }
    
    # 标准化并查找
    pair = tuple(sorted([concept1, concept2]))
    commonness = COMMON_PAIRS.get(pair, 0.5)  # 默认中等常见度
    
    # 新颖度 = 1 - 常见度
    novelty = 1 - commonness
    
    return novelty


async def compute_multi_dimensional_relevance(
    concept1: str,
    concept2: str,
    discipline1: str,
    discipline2: str,
    cross_principle: str,
    semantic_similarity: float,
    llm_client: AsyncOpenAI
) -> Dict[str, float]:
    """
    计算多维度相关度
    
    Args:
        concept1: 概念1
        concept2: 概念2
        discipline1: 学科1
        discipline2: 学科2
        cross_principle: 跨学科原理
        semantic_similarity: 语义相似度（已计算）
        llm_client: LLM客户端
        
    Returns:
        包含所有维度分数的字典
    """
    
    # 维度1: 语义相似度（已有）
    semantic = semantic_similarity
    
    # 维度2: 跨学科强度
    cross_score = compute_cross_discipline_strength(discipline1, discipline2)
    
    # 维度3: 原理一致性（需要LLM）
    principle_score = await evaluate_principle_alignment(
        concept1, concept2, cross_principle, llm_client
    )
    
    # 维度4: 新颖度
    novelty = compute_novelty_score(concept1, concept2)
    
    # 综合得分（可调整权重）
    weights = {
        "semantic": 0.3,
        "cross": 0.3,
        "principle": 0.3,
        "novelty": 0.1
    }
    
    composite = (
        weights["semantic"] * semantic +
        weights["cross"] * cross_score +
        weights["principle"] * principle_score +
        weights["novelty"] * novelty
    )
    
    return {
        "semantic_similarity": round(semantic, 3),
        "cross_discipline_score": round(cross_score, 3),
        "principle_alignment": round(principle_score, 3),
        "novelty_score": round(novelty, 3),
        "composite_score": round(composite, 3),
        "dimensions": {
            "semantic": round(semantic, 3),
            "cross_discipline": round(cross_score, 3),
            "principle": round(principle_score, 3),
            "novelty": round(novelty, 3)
        }
    }


def classify_relationship_tier(
    composite_score: float,
    cross_score: float,
    principle_score: float
) -> Tuple[str, str]:
    """
    分类关系强度层级
    
    Args:
        composite_score: 综合得分
        cross_score: 跨学科强度
        principle_score: 原理一致性
        
    Returns:
        (层级名称, 层级描述)
    """
    # 核心关联：高原理一致性 + 低跨学科强度（同领域）
    if principle_score >= 0.8 and cross_score <= 0.4:
        return ("core", "核心关联")
    
    # 跨学科关联：高原理一致性 + 高跨学科强度
    if principle_score >= 0.6 and cross_score >= 0.5:
        return ("cross_discipline", "跨学科关联")
    
    # 边缘关联：其他
    if composite_score >= 0.5:
        return ("peripheral", "边缘关联")
    
    return ("weak", "弱关联")


# ==================== 测试代码 ====================

async def test_enhanced_relevance():
    """测试增强的相关度计算"""
    print("="*70)
    print("测试增强的相关度计算")
    print("="*70)
    
    # 模拟LLM客户端
    from openai import AsyncOpenAI
    llm_client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    )
    
    # 测试案例
    test_cases = [
        {
            "concept1": "神经网络",
            "concept2": "感知器",
            "discipline1": "计算机科学",
            "discipline2": "计算机科学",
            "cross_principle": "感知器是神经网络的基本单元，基于相同的加权求和+激活函数机制",
            "semantic_sim": 0.660
        },
        {
            "concept1": "神经网络",
            "concept2": "玻尔兹曼机",
            "discipline1": "计算机科学",
            "discipline2": "物理学",
            "cross_principle": "都基于能量最小化原理，玻尔兹曼机使用统计力学的能量函数",
            "semantic_sim": 0.581
        },
        {
            "concept1": "神经网络",
            "concept2": "群体智能",
            "discipline1": "计算机科学",
            "discipline2": "社会学",
            "cross_principle": "都涉及多个简单个体协作产生智能行为",
            "semantic_sim": 0.687
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n案例{i}: {case['concept1']} <-> {case['concept2']}")
        print(f"  学科: {case['discipline1']} → {case['discipline2']}")
        
        result = await compute_multi_dimensional_relevance(
            concept1=case["concept1"],
            concept2=case["concept2"],
            discipline1=case["discipline1"],
            discipline2=case["discipline2"],
            cross_principle=case["cross_principle"],
            semantic_similarity=case["semantic_sim"],
            llm_client=llm_client
        )
        
        print(f"\n  多维度得分:")
        print(f"    语义相似度:   {result['semantic_similarity']:.3f}")
        print(f"    跨学科强度:   {result['cross_discipline_score']:.3f}")
        print(f"    原理一致性:   {result['principle_alignment']:.3f}")
        print(f"    新颖度:       {result['novelty_score']:.3f}")
        print(f"    综合得分:     {result['composite_score']:.3f}")
        
        tier, tier_name = classify_relationship_tier(
            result["composite_score"],
            result["cross_discipline_score"],
            result["principle_alignment"]
        )
        print(f"  关系层级: {tier_name}")


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_enhanced_relevance())
