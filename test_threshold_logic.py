"""
测试动态阈值筛选逻辑
验证不同概念下的节点数量控制在3-9个之间
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_discover_with_threshold(concept: str):
    """测试discover端点的动态阈值筛选"""
    print(f"\n{'='*60}")
    print(f"测试概念: {concept}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/discover",
            json={"concept": concept, "max_concepts": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            nodes = data["data"]["nodes"]
            edges = data["data"]["edges"]
            metadata = data["data"].get("metadata", {})
            
            # 分析节点数量
            related_nodes = [n for n in nodes if n.get("depth", 1) == 1]
            print(f"\n[节点统计]")
            print(f"  总节点数: {len(nodes)} (1个中心节点 + {len(related_nodes)}个相关节点)")
            print(f"  目标范围: 3-9个相关节点")
            print(f"  实际结果: {'✅ 符合' if 3 <= len(related_nodes) <= 9 else '❌ 不符合'}")
            
            # 分析相似度分布
            similarities = [n.get("similarity", 0) for n in related_nodes]
            if similarities:
                print(f"\n[相似度分析]")
                print(f"  最高相似度: {max(similarities):.3f}")
                print(f"  最低相似度: {min(similarities):.3f}")
                print(f"  平均相似度: {sum(similarities)/len(similarities):.3f}")
                print(f"  阈值(0.62)以上: {len([s for s in similarities if s >= 0.62])}个")
                
                # 详细列表
                print(f"\n[节点明细]")
                for i, node in enumerate(related_nodes, 1):
                    sim = node.get("similarity", 0)
                    label = node.get("label", "Unknown")
                    credibility = node.get("credibility", 0)
                    status = "✓" if sim >= 0.62 else "○"
                    print(f"  {status} {i}. {label}: 相似度={sim:.3f}, 可信度={credibility:.3f}")
            
            # 元数据
            if metadata:
                print(f"\n[元数据]")
                print(f"  生成方法: {metadata.get('generation_method', 'N/A')}")
                print(f"  平均相似度: {metadata.get('avg_similarity', 0):.3f}")
            
            return len(related_nodes), similarities
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return 0, []


async def main():
    """测试多个概念"""
    test_concepts = [
        "马尔可夫理论",    # 高相关性概念（预期8-9个）
        "深度学习",        # 常见概念（预期7-9个）
        "笨蛋",            # 低相关性概念（预期3-5个）
        "量子计算",        # 专业概念（预期6-8个）
    ]
    
    print("="*60)
    print("动态阈值筛选逻辑测试")
    print("="*60)
    print(f"阈值设置: 0.62")
    print(f"节点数量范围: 3-9个")
    print(f"测试概念数量: {len(test_concepts)}")
    
    results = []
    for concept in test_concepts:
        try:
            count, sims = await test_discover_with_threshold(concept)
            results.append((concept, count, sims))
            await asyncio.sleep(2)  # 避免请求过快
        except Exception as e:
            print(f"❌ 测试失败: {concept} - {e}")
    
    # 汇总报告
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}")
    
    passed = sum(1 for _, count, _ in results if 3 <= count <= 9)
    total = len(results)
    
    print(f"\n总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%\n")
    
    for concept, count, sims in results:
        status = "✅" if 3 <= count <= 9 else "❌"
        avg_sim = sum(sims) / len(sims) if sims else 0
        print(f"{status} {concept}: {count}个节点 (平均相似度: {avg_sim:.3f})")
    
    if passed == total:
        print(f"\n🎉 所有测试通过！动态阈值逻辑运行正常。")
    else:
        print(f"\n⚠️  部分测试失败，需要调整阈值参数。")


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(main())
