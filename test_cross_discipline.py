"""
跨学科概念挖掘测试
验证新prompt逻辑是否能发现远亲概念
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_cross_discipline_discovery():
    """测试跨学科概念挖掘"""
    test_cases = [
        {
            "concept": "神经网络",
            "expectations": [
                "生物神经元（神经科学）",
                "霍普菲尔德网络（统计物理）",
                "图论（数学）",
                "贝叶斯网络（概率论）"
            ]
        },
        {
            "concept": "熵",
            "expectations": [
                "信息熵（信息论）",
                "热力学熵（热力学）",
                "统计熵（统计力学）",
                "交叉熵损失（机器学习）"
            ]
        },
        {
            "concept": "PageRank算法",
            "expectations": [
                "马尔可夫链（概率论）",
                "随机游走（统计物理）",
                "图论（数学）",
                "特征向量中心性（网络科学）"
            ]
        },
        {
            "concept": "遗传算法",
            "expectations": [
                "达尔文进化论（生物学）",
                "自然选择（进化生物学）",
                "基因重组（遗传学）",
                "优化算法（计算机科学）"
            ]
        }
    ]
    
    print("="*70)
    print("跨学科概念挖掘测试")
    print("="*70)
    print(f"LLM模型: Gemini 2.0 Flash Thinking")
    print(f"核心目标: 发现'远亲概念' - 不同领域中原理相通的概念")
    print(f"测试数量: {len(test_cases)}个")
    print("="*70)
    
    results = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for idx, test_case in enumerate(test_cases, 1):
            concept = test_case["concept"]
            expectations = test_case["expectations"]
            
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(test_cases)}] 测试概念: {concept}")
            print(f"{'='*70}")
            print(f"预期发现的远亲概念:")
            for exp in expectations:
                print(f"  • {exp}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/discover",
                    json={"concept": concept, "max_concepts": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    nodes = data["data"]["nodes"]
                    metadata = data["data"].get("metadata", {})
                    
                    # 排除中心节点
                    related_nodes = [n for n in nodes if n.get("depth", 1) == 1]
                    
                    # 统计学科分布
                    print(f"\n[节点统计]")
                    print(f"  总节点数: {len(nodes)} (1个中心 + {len(related_nodes)}个相关)")
                    
                    disciplines = {}
                    for node in related_nodes:
                        disc = node.get("discipline", "未知")
                        disciplines[disc] = disciplines.get(disc, 0) + 1
                    
                    print(f"\n[学科分布] (覆盖{len(disciplines)}个领域)")
                    for disc, count in sorted(disciplines.items(), key=lambda x: -x[1]):
                        print(f"  {disc}: {count}个")
                    
                    # 检查跨学科质量
                    if len(disciplines) >= 3:
                        print(f"\n✅ 跨学科挖掘成功！覆盖{len(disciplines)}个不同领域")
                        cross_quality = "优秀" if len(disciplines) >= 5 else "良好"
                    else:
                        print(f"\n⚠️  学科覆盖不足，仅{len(disciplines)}个领域")
                        cross_quality = "待改进"
                    
                    # 显示远亲概念示例
                    print(f"\n[远亲概念示例] (前5个)")
                    for i, node in enumerate(related_nodes[:5], 1):
                        label = node.get("label", "")
                        disc = node.get("discipline", "未知")
                        sim = node.get("similarity", 0)
                        cred = node.get("credibility", 0)
                        
                        # 尝试显示跨学科原理（如果LLM返回了）
                        definition = node.get("definition", "")
                        brief = node.get("brief_summary", "")
                        
                        print(f"\n  {i}. {label} ({disc})")
                        print(f"     相似度: {sim:.3f} | 可信度: {cred:.3f}")
                        if brief:
                            print(f"     简介: {brief[:100]}...")
                    
                    # 分析是否找到预期的远亲概念
                    found_expectations = []
                    for exp in expectations:
                        exp_name = exp.split("（")[0]  # 提取概念名
                        for node in related_nodes:
                            if exp_name in node.get("label", ""):
                                found_expectations.append(exp)
                                break
                    
                    if found_expectations:
                        print(f"\n[预期匹配] 找到{len(found_expectations)}/{len(expectations)}个预期概念:")
                        for exp in found_expectations:
                            print(f"  ✓ {exp}")
                    
                    # 元数据
                    if metadata:
                        print(f"\n[元数据]")
                        print(f"  生成方法: {metadata.get('generation_method', 'N/A')}")
                        print(f"  平均相似度: {metadata.get('avg_similarity', 0):.3f}")
                    
                    results.append({
                        "concept": concept,
                        "node_count": len(related_nodes),
                        "discipline_count": len(disciplines),
                        "quality": cross_quality,
                        "found_expectations": len(found_expectations),
                        "total_expectations": len(expectations)
                    })
                    
                else:
                    print(f"❌ 请求失败: {response.status_code}")
                    results.append({
                        "concept": concept,
                        "error": f"HTTP {response.status_code}"
                    })
                
                await asyncio.sleep(3)  # 避免请求过快
                
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                results.append({
                    "concept": concept,
                    "error": str(e)
                })
    
    # 汇总报告
    print(f"\n{'='*70}")
    print("测试汇总报告")
    print(f"{'='*70}")
    
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    print(f"\n总测试数: {len(test_cases)}")
    print(f"成功: {len(successful)}")
    print(f"失败: {len(failed)}")
    
    if successful:
        print(f"\n[成功案例详情]")
        for r in successful:
            quality_icon = "🌟" if r["quality"] == "优秀" else "✅" if r["quality"] == "良好" else "⚠️"
            print(f"\n{quality_icon} {r['concept']}")
            print(f"  节点数: {r['node_count']}")
            print(f"  学科覆盖: {r['discipline_count']}个领域")
            print(f"  质量评价: {r['quality']}")
            print(f"  预期匹配: {r['found_expectations']}/{r['total_expectations']}")
    
    if failed:
        print(f"\n[失败案例]")
        for r in failed:
            print(f"❌ {r['concept']}: {r['error']}")
    
    # 总体评价
    if len(successful) == len(test_cases):
        avg_disciplines = sum(r["discipline_count"] for r in successful) / len(successful)
        if avg_disciplines >= 4:
            print(f"\n🎉 测试全部通过！平均学科覆盖: {avg_disciplines:.1f}个")
            print(f"   跨学科挖掘能力: 优秀")
        else:
            print(f"\n✅ 测试通过，但学科覆盖有待提升")
            print(f"   平均学科覆盖: {avg_disciplines:.1f}个（目标: ≥4个）")
    else:
        print(f"\n⚠️  部分测试失败，请检查后端服务和API配置")
    
    return results


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_cross_discipline_discovery())
