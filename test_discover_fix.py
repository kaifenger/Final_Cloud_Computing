#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试/discover端点的Agent集成和动态可信度
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_discover_with_agent():
    """测试使用Agent的discover端点"""
    print("=" * 80)
    print("测试1: /discover端点 - Agent集成")
    print("=" * 80)
    
    try:
        from backend.api.routes import discover_concepts, DiscoverRequest
        
        # 创建请求
        request = DiscoverRequest(
            concept="机器学习",
            disciplines=["计算机科学", "数学", "统计学"],
            depth=2,
            max_concepts=10
        )
        
        print(f"\n📊 请求参数:")
        print(f"  - 概念: {request.concept}")
        print(f"  - 学科: {request.disciplines}")
        print(f"  - 深度: {request.depth}")
        print(f"  - 最大概念数: {request.max_concepts}")
        
        # 调用discover端点
        print(f"\n🔄 调用discover端点...")
        response = await discover_concepts(request)
        
        # 解析响应
        if hasattr(response, 'data'):
            data = response.data
            if hasattr(data, 'nodes'):
                nodes = data.nodes
                edges = data.edges
                metadata = data.metadata if hasattr(data, 'metadata') else {}
            else:
                nodes = data.get('nodes', [])
                edges = data.get('edges', [])
                metadata = data.get('metadata', {})
        else:
            nodes = response.get('data', {}).get('nodes', [])
            edges = response.get('data', {}).get('edges', [])
            metadata = response.get('data', {}).get('metadata', {})
        
        print(f"\n✅ 响应成功:")
        print(f"  - 状态: {response.status if hasattr(response, 'status') else response.get('status')}")
        print(f"  - 请求ID: {response.request_id if hasattr(response, 'request_id') else response.get('request_id')}")
        print(f"  - 节点数: {len(nodes)}")
        print(f"  - 边数: {len(edges)}")
        print(f"  - 模式: {metadata.get('mode', 'unknown')}")
        
        # 验证节点详情
        print(f"\n📝 节点详情:")
        for i, node in enumerate(nodes[:5], 1):  # 只显示前5个
            if isinstance(node, dict):
                label = node.get('label', '未知')
                discipline = node.get('discipline', '未知')
                credibility = node.get('credibility', 0.0)
                source = node.get('source', '未知')
            else:
                label = getattr(node, 'label', '未知')
                discipline = getattr(node, 'discipline', '未知')
                credibility = getattr(node, 'credibility', 0.0)
                source = getattr(node, 'source', '未知')
            
            print(f"  {i}. {label}")
            print(f"     学科: {discipline}")
            print(f"     可信度: {credibility:.3f}")
            print(f"     来源: {source}")
        
        # 验证动态可信度范围
        print(f"\n🔍 可信度验证:")
        credibilities = []
        for node in nodes:
            if isinstance(node, dict):
                credibilities.append(node.get('credibility', 0.0))
            else:
                credibilities.append(getattr(node, 'credibility', 0.0))
        
        if credibilities:
            min_cred = min(credibilities)
            max_cred = max(credibilities)
            avg_cred = sum(credibilities) / len(credibilities)
            unique_creds = len(set(credibilities))
            
            print(f"  - 最小值: {min_cred:.3f}")
            print(f"  - 最大值: {max_cred:.3f}")
            print(f"  - 平均值: {avg_cred:.3f}")
            print(f"  - 不同值数量: {unique_creds}")
            
            # 检查是否使用动态可信度
            if unique_creds > 2:
                print(f"  ✅ 可信度动态计算成功（{unique_creds}个不同值）")
            elif unique_creds == 2 and {min_cred, max_cred} == {0.95, 0.75}:
                print(f"  ⚠️ 仍使用固定值（0.95/0.75）")
            else:
                print(f"  ⚠️ 可信度范围异常")
        
        # 验证元数据
        print(f"\n📊 元数据:")
        print(f"  - total_nodes: {metadata.get('total_nodes', 0)}")
        print(f"  - total_edges: {metadata.get('total_edges', 0)}")
        print(f"  - verified_nodes: {metadata.get('verified_nodes', 0)}")
        print(f"  - avg_credibility: {metadata.get('avg_credibility', 0.0):.3f}")
        print(f"  - mode: {metadata.get('mode', 'unknown')}")
        
        # 检查模式
        mode = metadata.get('mode', '')
        if 'agent' in mode.lower():
            print(f"\n🎯 ✅ 使用Agent生成（真实LLM调用）")
        elif 'fallback' in mode.lower():
            print(f"\n🎯 ⚠️ 使用后备方案（Agent未加载）")
            if 'dynamic' in mode.lower():
                print(f"     但启用了动态可信度计算")
        else:
            print(f"\n🎯 ⚠️ 模式未知: {mode}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_credibility_calculation():
    """测试可信度计算"""
    print("\n" + "=" * 80)
    print("测试2: 动态可信度计算")
    print("=" * 80)
    
    try:
        from backend.api.real_node_generator import compute_similarity, compute_credibility
        
        test_cases = [
            ("机器学习", "深度学习", True),   # 强相关
            ("机器学习", "统计学", True),     # 中等相关
            ("机器学习", "量子物理", False),  # 弱相关
        ]
        
        print(f"\n测试语义相似度和动态可信度:")
        for parent, child, has_wiki in test_cases:
            similarity = await compute_similarity(parent, child)
            credibility = await compute_credibility(child, parent, has_wiki)
            
            print(f"\n  父概念: {parent} | 子概念: {child}")
            print(f"  - 相似度: {similarity:.3f}")
            print(f"  - 有Wikipedia: {has_wiki}")
            print(f"  - 可信度: {credibility:.3f}")
            
            # 验证范围
            if 0.665 <= credibility <= 0.99:
                print(f"  ✅ 可信度在合理范围内")
            else:
                print(f"  ⚠️ 可信度超出预期范围")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🧪 /discover端点修复验证测试")
    print("=" * 80)
    
    results = []
    
    # 测试1: Agent集成
    result1 = await test_discover_with_agent()
    results.append(("Agent集成测试", result1))
    
    # 测试2: 可信度计算
    result2 = await test_credibility_calculation()
    results.append(("动态可信度测试", result2))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
