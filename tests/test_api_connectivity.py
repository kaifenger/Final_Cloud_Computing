"""
API连通性测试 - 验证OpenRouter + Gemini 3 Pro是否可以正常调用
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_client import LLMClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def test_api_basic_call():
    """测试1: 基础API调用"""
    print("\n" + "="*60)
    print("测试1: 基础API调用 - 简单问答")
    print("="*60)
    
    try:
        # 获取API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ 未找到OPENROUTER_API_KEY环境变量")
            return False
        
        print(f"✓ API Key已配置: {api_key[:20]}...")
        
        # 创建LLM客户端
        print("✓ 创建LLMClient...")
        client = LLMClient(
            api_key=api_key,
            model="google/gemini-3-pro-preview",
            temperature=0.3,
            max_tokens=500,
            enable_reasoning=True
        )
        print(f"  模型: {client.model}")
        print(f"  Base URL: {client.base_url}")
        
        # 发送简单测试请求
        print("\n✓ 发送测试请求...")
        test_prompt = "请用一句话解释什么是熵？"
        print(f"  Prompt: {test_prompt}")
        
        response = await client.call_with_retry(test_prompt)
        
        print("\n✅ API调用成功！")
        print(f"响应内容: {response[:200]}...")
        print(f"响应长度: {len(response)} 字符")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_discovery():
    """测试2: ConceptDiscoveryAgent API调用"""
    print("\n" + "="*60)
    print("测试2: ConceptDiscoveryAgent - 概念发现")
    print("="*60)
    
    try:
        from agents import ConceptDiscoveryAgent
        from shared.constants import Discipline
        
        print("✓ 创建ConceptDiscoveryAgent...")
        agent = ConceptDiscoveryAgent()
        
        print("\n✓ 调用discover_concepts方法...")
        print("  目标概念: 熵")
        print("  学科范围: [物理, 计算机]")
        print("  深度: 1")
        print("  最大数量: 3")
        
        result = await agent.discover_concepts(
            concept="熵",
            disciplines=[Discipline.PHYSICS, Discipline.COMPUTER],
            depth=1,
            max_concepts=3
        )
        
        concepts = result.get('concepts', [])
        
        print(f"\n✅ 发现 {len(concepts)} 个相关概念！")
        for i, concept in enumerate(concepts, 1):
            print(f"\n  概念 {i}:")
            print(f"    名称: {concept.get('name', 'N/A')}")
            print(f"    学科: {concept.get('discipline', 'N/A')}")
            print(f"    关联强度: {concept.get('strength', 0):.2f}")
            print(f"    原因: {concept.get('reasoning', 'N/A')[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Agent调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_workflow():
    """测试3: 完整编排器工作流"""
    print("\n" + "="*60)
    print("测试3: AgentOrchestrator - 完整工作流")
    print("="*60)
    
    try:
        from agents import get_orchestrator
        from shared.constants import Discipline
        
        print("✓ 获取AgentOrchestrator实例...")
        orchestrator = get_orchestrator()
        
        print("\n✓ 调用discover方法...")
        print("  概念: 熵")
        print("  学科: [物理]")
        print("  深度: 1")
        print("  最大概念数: 2")
        
        result = await orchestrator.discover(
            concept="熵",
            disciplines=[Discipline.PHYSICS],
            depth=1,
            max_concepts=2
        )
        
        print(f"\n✅ 编排器工作流执行成功！")
        print(f"  状态: {result.status}")
        
        if result.data:
            graph_data = result.data
            print(f"  节点数: {len(graph_data.nodes)}")
            print(f"  边数: {len(graph_data.edges)}")
            
            if graph_data.metadata:
                meta = graph_data.metadata
                print(f"  验证通过率: {meta.verified_nodes}/{meta.total_nodes}")
                print(f"  平均可信度: {meta.avg_credibility:.2f}")
                print(f"  处理时间: {meta.processing_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 编排器调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有API测试"""
    print("\n" + "="*60)
    print("ConceptGraph AI - API连通性测试")
    print("测试OpenRouter + Gemini 3 Pro是否正常工作")
    print("="*60)
    
    results = {}
    
    # 测试1: 基础API调用
    results["基础API调用"] = await test_api_basic_call()
    
    # 测试2: Agent API调用
    results["Agent概念发现"] = await test_agent_discovery()
    
    # 测试3: 完整编排器工作流
    results["编排器工作流"] = await test_orchestrator_workflow()
    
    # 汇总结果
    print("\n" + "="*60)
    print("API测试结果汇总")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s}: {status}")
        if result:
            passed += 1
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("="*60)
        print("🎉 恭喜！所有API测试通过，系统可以正常工作！")
        print("="*60)
        return 0
    else:
        print("="*60)
        print("⚠️  部分API测试失败，请检查配置")
        print("="*60)
        print("\n常见问题排查:")
        print("1. 检查API key是否有效: echo $env:OPENROUTER_API_KEY")
        print("2. 检查网络连接是否正常")
        print("3. 检查OpenRouter余额是否充足")
        print("4. 检查模型名称是否正确: google/gemini-3-pro-preview")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
