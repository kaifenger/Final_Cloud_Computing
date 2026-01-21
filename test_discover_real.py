"""测试/discover端点是否使用真实LLM生成"""
import asyncio
import os

os.environ["ENABLE_EXTERNAL_VERIFICATION"] = "true"

async def test_discover():
    from backend.api.routes import discover_concepts, DiscoverRequest
    
    print("=" * 80)
    print("测试 /discover 端点 - 真实LLM生成验证")
    print("=" * 80)
    
    request = DiscoverRequest(
        concept="马尔可夫原理",
        max_concepts=10
    )
    
    print(f"\n[输入]")
    print(f"  概念: {request.concept}")
    print(f"  最大概念数: {request.max_concepts}")
    
    print(f"\n[执行...]")
    result = await discover_concepts(request)
    
    print(f"\n[结果]")
    print(f"  状态: {result.status}")
    
    if result.data:
        nodes = result.data.get("nodes", [])
        edges = result.data.get("edges", [])
        metadata = result.data.get("metadata", {})
        
        print(f"\n[节点列表] ({len(nodes)}个)")
        for i, node in enumerate(nodes):
            print(f"\n  {i+1}. {node['label']}")
            print(f"     ID: {node['id']}")
            print(f"     学科: {node.get('discipline', 'N/A')}")
            print(f"     可信度: {node.get('credibility', 'N/A')}")
            print(f"     相似度: {node.get('similarity', 'N/A')}")
            print(f"     来源: {node.get('source', 'N/A')}")
            print(f"     深度: {node.get('depth', 'N/A')}")
        
        print(f"\n[元数据]")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print(f"\n[验证点]")
        
        # 检查是否使用了真实LLM
        is_real_llm = metadata.get("generation_method") == "LLM + Similarity Ranking"
        if is_real_llm:
            print("  [OK] 使用了真实LLM生成")
        else:
            print("  [FAIL] 使用了预定义概念（回退方案）")
            print(f"    生成方法: {metadata.get('generation_method', 'N/A')}")
        
        # 检查相似度是否动态计算
        similarities = [n.get('similarity') for n in nodes if n.get('depth', 0) > 0]
        if similarities:
            unique_sims = set(similarities)
            if len(unique_sims) > 1:
                print(f"  [OK] 相似度是动态计算的（{len(unique_sims)}个不同值）")
            else:
                print(f"  [FAIL] 相似度是固定的（都是{similarities[0]}）")
        
        # 检查节点名称是否模板化
        template_nodes = [n for n in nodes if n['label'].endswith('理论') or n['label'].endswith('应用') or n['label'].endswith('方法')]
        if len(template_nodes) > 0 and len(template_nodes) == len(nodes) - 1:
            print(f"  [FAIL] 节点名称是模板化的（{len(template_nodes)}个模板节点）")
        else:
            print(f"  [OK] 节点名称不是模板化的")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_discover())
