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
    
    # 构建跨学科提示词
    existing_str = "、".join(existing_concepts) if existing_concepts else "无"
    prompt = f"""你是一个跨学科知识挖掘专家。请为概念"{parent_concept}"挖掘{max_count}个跨领域的相关概念。

【核心任务】发现跨学科的"远亲概念" - 不同领域中原理相通的概念

【跨学科搜索策略】
必须从以下不同领域寻找概念（每个领域至少1个）：
1. 数学/统计学：寻找数学本质、理论基础
2. 物理学：寻找物理类比、能量/信息原理
3. 生物学/神经科学：寻找仿生学启发、演化机制
4. 计算机科学：寻找算法实现、工程应用
5. 社会学/经济学：寻找群体行为、博弈模型
6. 其他交叉学科：心理学、语言学、复杂系统等

【远亲概念判定标准】
✅ 好的远亲概念（必须满足至少一条）：
- 数学形式相同但应用领域不同（如：熵在热力学vs信息论）
- 底层原理一致（如：神经网络vs生物神经元、PageRank vs随机游走）
- 历史启发关系（如：遗传算法vs达尔文进化论）
- 结构同构（如：社交网络vs蛋白质网络）

❌ 避免的表面关联：
- 仅仅名字相似（如："网络"在计算机网络vs神经网络）
- 单纯的应用关系（如：机器学习用于医疗诊断）

【约束条件】
- 不要包含已存在的概念：{existing_str}
- 每个概念必须来自不同学科（避免扎堆）
- 必须解释跨学科关联的底层原理

【输出格式】（每行一个概念）
概念名|学科|关系类型|跨学科原理

示例：
神经网络|生物学|bio_inspired|模拟生物神经元的突触连接和激活传播机制
信息熵|物理学|mathematical_analogy|与热力学熵数学形式完全一致(H=-Σp·log(p))
PageRank算法|图论|structural_isomorphism|本质是马尔可夫链的平稳分布求解
遗传算法|进化生物学|evolutionary_mechanism|复制达尔文的变异-选择-遗传进化过程

请直接输出{max_count}个跨学科概念，不要解释："""

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-3-flash-preview"),
                messages=[
                    {"role": "system", "content": "你是跨学科知识挖掘专家，擅长发现不同领域间的深层原理关联和结构同构性。你的核心能力是识别'远亲概念' - 那些表面看起来毫不相关，但底层数学、物理或信息论原理完全一致的概念。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=20.0
        )
        
        if response and response.choices:
            content = response.choices[0].message.content.strip()
            concepts = []
            
            for line in content.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        # 新格式：概念名|学科|关系类型|跨学科原理
                        # 去除概念名前的序号（如"1. 反向传播" -> "反向传播"）
                        concept_name = parts[0].strip()
                        # 移除开头的数字+点号模式
                        import re
                        concept_name = re.sub(r'^\d+\.\s*', '', concept_name)
                        
                        concepts.append({
                            "name": concept_name,
                            "discipline": parts[1].strip(),
                            "relation": parts[2].strip(),
                            "cross_principle": parts[3].strip()
                        })
                    elif len(parts) >= 3:
                        # 兼容旧格式：概念名|学科|关系类型
                        concept_name = parts[0].strip()
                        import re
                        concept_name = re.sub(r'^\d+\.\s*', '', concept_name)
                        
                        concepts.append({
                            "name": concept_name,
                            "discipline": parts[1].strip(),
                            "relation": parts[2].strip(),
                            "cross_principle": "学科交叉概念"
                        })
            
            if concepts:
                print(f"[SUCCESS] LLM生成了{len(concepts)}个相关概念")
                
                # 启用学术概念过滤
                filtered_concepts = []
                for concept in concepts:
                    is_academic = await is_academic_concept(concept["name"])
                    if is_academic:
                        filtered_concepts.append(concept)
                    else:
                        print(f"[FILTER] 非学术概念已过滤: {concept['name']}")
                
                if filtered_concepts:
                    print(f"[SUCCESS] 学术过滤后剩余{len(filtered_concepts)}个概念")
                    return filtered_concepts[:max_count]
                else:
                    print(f"[WARNING] 学术过滤后无概念剩余，返回原始结果")
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
                model=os.getenv("LLM_MODEL", "google/gemini-3-flash-preview"),
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
                max_tokens=10,
                extra_body={"reasoning": {"enabled": True}}
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
