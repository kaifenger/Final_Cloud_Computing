#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能2和功能3的核心生成器
"""

import os
import asyncio
import re
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ==================== LLM客户端 ====================
_llm_client = None

def get_llm_client():
    """获取LLM客户端"""
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            _llm_client = AsyncOpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )
            print("[INFO] 多功能LLM客户端已初始化")
    return _llm_client


# ==================== 功能2：指定学科的概念挖掘 ====================

async def generate_concepts_with_disciplines(
    parent_concept: str,
    disciplines: List[str],
    max_count: int = 10
) -> List[Dict]:
    """
    功能2：生成指定学科的相关概念
    
    Args:
        parent_concept: 输入概念，如"神经网络"
        disciplines: 学科列表，如["生物学", "数学"]
        max_count: 每个学科生成的概念数
        
    Returns:
        概念列表，每个概念包含：name, discipline, relation, cross_principle
    """
    
    client = get_llm_client()
    if not client:
        print("[WARNING] LLM客户端未初始化")
        return []
    
    # 构建学科列表字符串
    discipline_list = "\n".join([f"- {d}" for d in disciplines])
    
    # 填充prompt
    prompt = f"""你是跨学科知识挖掘专家。

任务：为概念"{parent_concept}"在指定学科中生成{max_count}个相关概念。

**仅在以下学科中寻找**：
{discipline_list}

严格要求：
1. **只能从上述指定学科中选择概念**，不得跨越到其他领域
2. 如果某个学科与该概念关联性弱，可以选择该学科中的"桥梁概念"（即连接性概念）
3. 必须解释每个概念与"{parent_concept}"在该学科视角下的关联
4. 每个学科至少生成1个概念（如果可能）

输出格式（每行一个概念，不要序号）：
概念名|学科|关系类型|学科视角下的关联原理

示例（假设指定学科为"生物学"和"数学"）：
输入：神经网络
输出：
突触传递|生物学|生物灵感|神经元间信号传递机制
Hebbian学习|生物学|学习规则|同步激活的神经元连接增强
梯度下降|数学|优化算法|损失函数最小化的迭代方法
反向传播|数学|计算方法|链式法则求导数传播误差

请直接输出："""
    
    system_prompt = "你是跨学科知识挖掘专家，严格按照指定学科范围生成概念。"
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-3-flash-preview"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=20.0
        )
        
        # 解析输出
        if response and response.choices:
            content = response.choices[0].message.content.strip()
            concepts = []
            
            for line in content.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        # 去除序号
                        concept_name = re.sub(r'^\d+\.\s*', '', parts[0].strip())
                        concept_discipline = parts[1].strip()
                        
                        # 验证学科是否在指定列表中
                        if concept_discipline not in disciplines:
                            print(f"[FILTER] 学科不匹配，已过滤: {concept_name} ({concept_discipline})")
                            continue
                        
                        concepts.append({
                            "name": concept_name,
                            "discipline": concept_discipline,
                            "relation": parts[2].strip(),
                            "cross_principle": parts[3].strip()
                        })
            
            # 启用学术概念过滤
            if concepts:
                # 导入is_academic_concept函数
                try:
                    from backend.api.real_node_generator import is_academic_concept
                    
                    filtered_concepts = []
                    for concept in concepts:
                        is_academic = await is_academic_concept(concept["name"])
                        if is_academic:
                            filtered_concepts.append(concept)
                        else:
                            print(f"[FILTER] 非学术概念已过滤: {concept['name']}")
                    
                    if filtered_concepts:
                        print(f"[SUCCESS] 功能2生成了{len(filtered_concepts)}个概念（限定学科：{', '.join(disciplines)}，学术过滤后）")
                        return filtered_concepts
                    else:
                        print(f"[WARNING] 学术过滤后无概念剩余，返回原始结果")
                        return concepts
                except ImportError:
                    print(f"[WARNING] 无法导入is_academic_concept，跳过学术过滤")
                    print(f"[SUCCESS] 功能2生成了{len(concepts)}个概念（限定学科：{', '.join(disciplines)}）")
                    return concepts
            
            return concepts
    
    except asyncio.TimeoutError:
        print(f"[WARNING] 功能2生成超时")
    except Exception as e:
        print(f"[WARNING] 功能2生成失败: {str(e)}")
    
    return []


# ==================== 功能3：多概念桥梁发现 ====================

async def find_bridge_concepts(
    concepts: List[str],
    max_bridges: int = 10
) -> List[Dict]:
    """
    功能3：寻找多个概念之间的桥梁概念
    
    Args:
        concepts: 输入概念列表，如["熵", "最小二乘法"]
        max_bridges: 最大桥梁概念数
        
    Returns:
        桥梁概念列表，每个包含：
        - name: 桥梁概念名
        - bridge_type: 桥梁类型（直接/间接/原理性）
        - connected_concepts: 关联的输入概念列表
        - connection_principle: 连接原理
    """
    
    client = get_llm_client()
    if not client:
        print("[WARNING] LLM客户端未初始化")
        return []
    
    # 构建概念列表字符串
    concept_list = "\n".join([f"- {c}" for c in concepts])
    
    # 填充prompt
    prompt = f"""你是跨学科概念连接专家，擅长发现看似无关概念之间的深层联系。

任务：分析以下多个概念之间的跨学科联系，找到连接它们的"桥梁概念"。

输入概念：
{concept_list}

核心要求：
1. **寻找桥梁概念**：能够同时关联多个输入概念的中间概念
2. **跨学科路径**：优先选择能够跨越不同学科的连接
3. **原理性关联**：必须基于共同的数学原理、物理规律或方法论

桥梁概念的三个层次：
- **直接桥梁**（优先）：与所有输入概念都有明确关联
  例：熵 + 最小二乘法 → 信息论（两者都涉及不确定性度量）
  
- **间接桥梁**（次选）：通过1-2步可连接所有概念
  例：熵 + 最小二乘法 → 概率论 → 统计推断
  
- **原理性桥梁**（补充）：体现相同的数学/哲学原理
  例：熵 + 最小二乘法 → 优化理论（两者都涉及最优化）

输出格式（每行一个桥梁概念，不要序号）：
概念名|桥梁类型|关联的输入概念|连接原理

桥梁类型：直接桥梁/间接桥梁/原理性桥梁
关联的输入概念：用逗号分隔，如"熵,最小二乘法"

示例：
输入概念：["熵", "最小二乘法"]

输出：
信息论|直接桥梁|熵,最小二乘法|熵度量信息不确定性，最小二乘基于信息损失最小化
统计推断|直接桥梁|熵,最小二乘法|最大熵原理和最小二乘估计都是统计推断方法
优化理论|原理性桥梁|熵,最小二乘法|熵最大化和误差最小化都是优化问题
概率分布|间接桥梁|熵,最小二乘法|熵描述分布不确定性，最小二乘假设正态分布
贝叶斯推理|直接桥梁|熵,最小二乘法|最大熵先验+最小二乘似然=后验估计

请直接输出至少{max_bridges}个桥梁概念："""
    
    system_prompt = "你是跨学科概念连接专家，擅长发现看似无关概念之间的深层联系。"
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-3-flash-preview"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # 稍高的temperature鼓励创造性连接
                max_tokens=1000,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=30.0
        )
        
        # 解析输出
        if response and response.choices:
            content = response.choices[0].message.content.strip()
            bridges = []
            
            for line in content.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        bridge_name = re.sub(r'^\d+\.\s*', '', parts[0].strip())
                        bridge_type = parts[1].strip()
                        connected = [c.strip() for c in parts[2].split(',')]
                        principle = parts[3].strip()
                        
                        bridges.append({
                            "name": bridge_name,
                            "bridge_type": bridge_type,
                            "connected_concepts": connected,
                            "connection_principle": principle
                        })
            
            # 按桥梁类型排序：直接桥梁 > 间接桥梁 > 原理性桥梁
            priority = {"直接桥梁": 1, "间接桥梁": 2, "原理性桥梁": 3}
            bridges.sort(key=lambda x: priority.get(x["bridge_type"], 999))
            
            print(f"[SUCCESS] 功能3找到了{len(bridges)}个桥梁概念")
            return bridges[:max_bridges]
    
    except asyncio.TimeoutError:
        print(f"[WARNING] 功能3生成超时")
    except Exception as e:
        print(f"[WARNING] 功能3生成失败: {str(e)}")
    
    return []


# ==================== 测试代码 ====================

async def test_function_2():
    """测试功能2：指定学科挖掘"""
    print("\n" + "="*70)
    print("测试功能2：指定学科的概念挖掘")
    print("="*70)
    
    concepts = await generate_concepts_with_disciplines(
        parent_concept="神经网络",
        disciplines=["生物学", "数学"],
        max_count=10
    )
    
    print(f"\n生成结果（{len(concepts)}个）：")
    for concept in concepts:
        print(f"  - {concept['name']} ({concept['discipline']})")
        print(f"    关系: {concept['relation']}")
        print(f"    原理: {concept['cross_principle']}")


async def test_function_3():
    """测试功能3：多概念桥梁发现"""
    print("\n" + "="*70)
    print("测试功能3：多概念桥梁发现")
    print("="*70)
    
    bridges = await find_bridge_concepts(
        concepts=["熵", "最小二乘法"],
        max_bridges=10
    )
    
    print(f"\n桥梁概念（{len(bridges)}个）：")
    for bridge in bridges:
        print(f"  - {bridge['name']} ({bridge['bridge_type']})")
        print(f"    连接: {', '.join(bridge['connected_concepts'])}")
        print(f"    原理: {bridge['connection_principle']}")


if __name__ == "__main__":
    print(__doc__)
    
    # 测试功能2
    asyncio.run(test_function_2())
    
    # 测试功能3
    asyncio.run(test_function_3())
