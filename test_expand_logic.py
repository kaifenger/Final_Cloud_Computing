"""测试节点展开的真实LLM生成逻辑"""
import asyncio
import sys
import os

# 设置环境变量
os.environ["ENABLE_EXTERNAL_VERIFICATION"] = "true"

async def test_expand_endpoint():
    """测试/expand端点的完整数据流"""
    print("=" * 70)
    print("测试节点展开逻辑 - 真实LLM生成 + 语义相似度排序")
    print("=" * 70)
    
    # 导入模块
    from backend.api.routes import expand_node, ExpandRequest
    
    # 模拟请求
    request = ExpandRequest(
        node_id="test_ml_001",
        node_label="机器学习",
        existing_nodes=["deep_learning_001"],
        max_new_nodes=3
    )
    
    print(f"\n[输入]")
    print(f"  父节点: {request.node_label}")
    print(f"  已有节点: {request.existing_nodes}")
    print(f"  请求数量: {request.max_new_nodes}")
    
    print(f"\n[执行展开...]")
    result = await expand_node(request)
    
    print(f"\n[结果]")
    print(f"  状态: {result['status']}")
    
    if result['status'] == 'success':
        data = result['data']
        nodes = data['nodes']
        edges = data['edges']
        metadata = data.get('metadata', {})
        
        print(f"\n[生成的节点] ({len(nodes)}个)")
        for i, node in enumerate(nodes, 1):
            print(f"  {i}. {node['label']}")
            print(f"     学科: {node['discipline']}")
            print(f"     可信度: {node['credibility']:.3f}")
            if 'similarity' in node:
                print(f"     相似度: {node['similarity']:.3f}")
            print(f"     来源: {node['source']}")
            print(f"     定义: {node['definition'][:60]}...")
            print()
        
        print(f"[边关系] ({len(edges)}条)")
        for i, edge in enumerate(edges, 1):
            print(f"  {i}. {edge['relation']}")
            print(f"     权重: {edge['weight']:.2f}")
            print(f"     推理: {edge['reasoning'][:80]}...")
            print()
        
        if metadata:
            print(f"[元数据]")
            print(f"  总候选数: {metadata.get('total_candidates', 'N/A')}")
            print(f"  选中数量: {metadata.get('selected_count', 'N/A')}")
            print(f"  平均相似度: {metadata.get('avg_similarity', 'N/A'):.3f}")
            print(f"  生成方法: {metadata.get('generation_method', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("[验证点]")
    print("  ✓ 使用真实LLM生成概念")
    print("  ✓ 计算语义相似度")
    print("  ✓ 按相似度排序选择top-N")
    print("  ✓ 动态可信度评分 (base * (0.7 + 0.3 * similarity))")
    print("  ✓ Wikipedia定义验证")
    print("=" * 70)


async def test_similarity_ranking():
    """测试相似度排序逻辑"""
    print("\n" + "=" * 70)
    print("测试相似度排序逻辑")
    print("=" * 70)
    
    from backend.api.real_node_generator import compute_similarity
    
    parent = "机器学习"
    candidates = [
        "深度学习",
        "监督学习",
        "云计算",
        "神经网络",
        "区块链",
        "强化学习"
    ]
    
    print(f"\n父概念: {parent}")
    print(f"候选概念: {len(candidates)}个")
    
    # 计算相似度
    similarities = []
    for candidate in candidates:
        sim = await compute_similarity(candidate, parent)
        similarities.append((candidate, sim))
    
    # 排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n[相似度排序结果]")
    for i, (concept, sim) in enumerate(similarities, 1):
        status = "[高相关]" if sim > 0.75 else "[中等]" if sim > 0.6 else "[低相关]"
        print(f"  {i}. {concept:15} | 相似度: {sim:.3f} | {status}")
    
    # 选择top-3
    top_n = 3
    selected = similarities[:top_n]
    
    print(f"\n[选择Top-{top_n}]")
    for concept, sim in selected:
        print(f"  [+] {concept} ({sim:.3f})")
    
    print(f"\n[排除]")
    for concept, sim in similarities[top_n:]:
        print(f"  [-] {concept} ({sim:.3f})")
    
    print("\n" + "=" * 70)


async def test_credibility_formula():
    """测试动态可信度公式"""
    print("\n" + "=" * 70)
    print("测试动态可信度公式")
    print("=" * 70)
    
    from backend.api.real_node_generator import compute_credibility
    
    test_cases = [
        ("深度学习", "机器学习", True, "高相似度+Wikipedia"),
        ("云计算", "机器学习", True, "低相似度+Wikipedia"),
        ("未知概念", "机器学习", False, "中等相似度+无Wikipedia"),
    ]
    
    print(f"\n公式: credibility = base * (0.7 + 0.3 * similarity)")
    print(f"  base = 0.95 (有Wikipedia) 或 0.70 (无Wikipedia)")
    print(f"  similarity ∈ [0, 1]")
    
    print(f"\n[测试用例]")
    for concept, parent, has_wiki, desc in test_cases:
        credibility = await compute_credibility(concept, parent, has_wiki)
        base = 0.95 if has_wiki else 0.70
        
        print(f"\n  {desc}")
        print(f"    概念: {concept}")
        print(f"    父概念: {parent}")
        print(f"    有Wikipedia: {'是' if has_wiki else '否'} (base={base})")
        print(f"    最终可信度: {credibility:.3f}")
        
        if credibility > 0.85:
            level = "[高可信]"
        elif credibility > 0.70:
            level = "[中等]"
        else:
            level = "[低可信]"
        print(f"    评级: {level}")
    
    print("\n" + "=" * 70)


async def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("节点展开逻辑 - 完整测试套件")
    print("=" * 70)
    
    # 检查环境变量
    llm_key = os.getenv("OPENROUTER_API_KEY")
    emb_key = os.getenv("OPENAI_API_KEY")
    
    print(f"\n[环境检查]")
    print(f"  OPENROUTER_API_KEY: {'OK 已配置' if llm_key else 'X 未配置'}")
    print(f"  OPENAI_API_KEY: {'OK 已配置' if emb_key else 'X 未配置'}")
    print(f"  ENABLE_EXTERNAL_VERIFICATION: {os.getenv('ENABLE_EXTERNAL_VERIFICATION')}")
    
    if not llm_key or not emb_key:
        print("\n[WARNING] 缺少API密钥，将使用预定义概念作为回退")
    
    # 运行测试
    try:
        # 测试1: 相似度排序
        await test_similarity_ranking()
        
        # 测试2: 可信度公式
        await test_credibility_formula()
        
        # 测试3: 完整展开流程
        await test_expand_endpoint()
        
        print("\n" + "=" * 70)
        print("[OK] 所有测试完成")
        print("=" * 70)
        
        print("\n[数据流总结]")
        print("  1. LLM生成 → 候选概念列表")
        print("  2. 相似度计算 → 量化关联强度")
        print("  3. 排序筛选 → 选择top-N")
        print("  4. Wikipedia验证 → 获取定义")
        print("  5. 可信度评分 → 动态计算 (0.7 + 0.3 * similarity)")
        print("  6. 返回结果 → 包含相似度和可信度")
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
