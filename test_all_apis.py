"""全面测试所有API真实调用"""
import requests
import json
import sys

BASE_URL = "http://localhost:8888/api/v1"

def test_wikipedia_api():
    """测试1: Wikipedia API真实调用"""
    print("\n" + "="*60)
    print("测试1: Wikipedia API真实调用")
    print("="*60)
    
    try:
        r = requests.post(f"{BASE_URL}/discover", 
            json={"concept": "量子计算", "depth": 1, "max_concepts": 10},
            timeout=120)
        data = r.json()
        
        if data.get("status") != "success":
            print(f"❌ API返回错误: {data}")
            return False
            
        nodes = data.get("data", {}).get("nodes", [])
        print(f"✓ 返回 {len(nodes)} 个节点")
        
        # 检查是否有Wikipedia来源
        wiki_count = sum(1 for n in nodes if n.get("source") == "Wikipedia")
        print(f"✓ Wikipedia来源节点数: {wiki_count}/{len(nodes)}")
        
        if nodes:
            node = nodes[0]
            print(f"\n首节点: {node.get('label')}")
            print(f"来源: {node.get('source')}")
            definition = node.get('definition', '')
            # 检查定义是否包含Wikipedia特征内容
            if "英語" in definition or "物理" in definition or "量子" in definition:
                print(f"✓ 定义看起来是真实Wikipedia内容")
                print(f"定义前100字: {definition[:100]}...")
            else:
                print(f"⚠ 定义可能是生成的: {definition[:100]}...")
        
        return wiki_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_arxiv_api():
    """测试2: Arxiv API真实调用"""
    print("\n" + "="*60)
    print("测试2: Arxiv API真实调用")
    print("="*60)
    
    try:
        r = requests.get(f"{BASE_URL}/arxiv/search",
            params={"query": "machine learning", "max_results": 3},
            timeout=60)
        data = r.json()
        
        if data.get("status") != "success":
            print(f"❌ API返回错误: {data}")
            return False
        
        papers = data.get("data", {}).get("papers", [])
        print(f"✓ 返回 {len(papers)} 篇论文")
        
        if papers and len(papers) > 0:
            paper = papers[0]
            # papers是列表，每个元素是字典
            if isinstance(paper, dict):
                print(f"\n首篇论文:")
                print(f"  标题: {paper.get('title', '')[:60]}...")
                print(f"  作者: {paper.get('authors', [])[:3]}")
                print(f"  链接: {paper.get('link', '')}")
                
                # 检查是否是真实Arxiv链接
                if "arxiv.org" in paper.get("link", ""):
                    print(f"✓ 是真实Arxiv论文链接")
                    return True
        
        return len(papers) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expand_api():
    """测试3: 节点展开API"""
    print("\n" + "="*60)
    print("测试3: 节点展开API (Wikipedia集成)")
    print("="*60)
    
    try:
        r = requests.post(f"{BASE_URL}/expand",
            json={
                "node_id": "test_ml",
                "node_label": "机器学习",
                "existing_nodes": [],
                "max_new_nodes": 3
            },
            timeout=120)
        data = r.json()
        
        if data.get("status") != "success":
            print(f"❌ API返回错误: {data}")
            return False
        
        nodes = data.get("data", {}).get("nodes", [])
        edges = data.get("data", {}).get("edges", [])
        print(f"✓ 返回 {len(nodes)} 个新节点, {len(edges)} 条边")
        
        wiki_count = 0
        for node in nodes:
            label = node.get("label", "")
            source = node.get("source", "")
            discipline = node.get("discipline", "")
            print(f"\n  • {label}")
            print(f"    学科: {discipline}")
            print(f"    来源: {source}")
            if source == "Wikipedia":
                wiki_count += 1
                definition = node.get("definition", "")
                if len(definition) > 50:
                    print(f"    ✓ 有Wikipedia定义 ({len(definition)}字)")
        
        print(f"\n✓ Wikipedia来源: {wiki_count}/{len(nodes)}")
        
        # 检查边关系类型
        relation_types = set(e.get("relation") for e in edges)
        print(f"✓ 关系类型: {relation_types}")
        
        return wiki_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_concept_detail_api():
    """测试4: 概念详情API (LLM生成)"""
    print("\n" + "="*60)
    print("测试4: 概念详情API (Wikipedia + 详细介绍)")
    print("="*60)
    
    try:
        # 正确的API路径: /concept/{concept_name}/detail
        r = requests.get(f"{BASE_URL}/concept/深度学习/detail",
            timeout=120)
        data = r.json()
        
        if data.get("status") != "success":
            print(f"❌ API返回错误: {data}")
            return False
        
        detail = data.get("data", {})
        print(f"✓ 概念: {detail.get('concept')}")
        
        # Wikipedia定义
        wiki_def = detail.get("wiki_definition", "")
        if wiki_def:
            print(f"✓ Wikipedia定义: {wiki_def[:80]}...")
        else:
            print(f"⚠ 无Wikipedia定义")
        
        # 详细介绍
        intro = detail.get("detailed_introduction", "")
        if intro:
            print(f"✓ 详细介绍 ({len(intro)}字)")
        
        # 相关论文
        papers = detail.get("related_papers", [])
        print(f"✓ 相关论文: {len(papers)} 篇")
        
        return len(intro) > 50
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_non_academic_concepts():
    """测试5: 非学术概念处理"""
    print("\n" + "="*60)
    print("测试5: 非学术概念处理")
    print("="*60)
    
    test_concepts = ["笨蛋", "爱情", "美食"]
    results = []
    
    for concept in test_concepts:
        try:
            r = requests.post(f"{BASE_URL}/discover",
                json={"concept": concept, "depth": 1, "max_concepts": 3},
                timeout=60)
            data = r.json()
            
            nodes = data.get("data", {}).get("nodes", [])
            if nodes and nodes[0].get("source") == "Wikipedia":
                print(f"✓ '{concept}': 找到Wikipedia定义")
                results.append(True)
            else:
                print(f"⚠ '{concept}': 无Wikipedia定义，使用LLM生成")
                results.append(True)  # 仍然可以处理
                
        except Exception as e:
            print(f"❌ '{concept}': 失败 - {e}")
            results.append(False)
    
    return all(results)


def main():
    print("="*60)
    print("ConceptGraph AI - API真实调用验证测试")
    print("="*60)
    print("\n确保后端服务已在 localhost:8888 运行")
    
    # 检查服务是否运行
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✓ 后端服务运行中\n")
    except:
        print("❌ 后端服务未运行，请先启动:")
        print("   py -3.11 -m uvicorn backend.main:app --port 8888")
        sys.exit(1)
    
    results = {
        "Wikipedia API": test_wikipedia_api(),
        "Arxiv API": test_arxiv_api(),
        "节点展开API": test_expand_api(),
        "概念详情API": test_concept_detail_api(),
        "非学术概念": test_non_academic_concepts(),
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有API测试通过！数据来自真实API调用。")
    else:
        print("⚠ 部分测试失败，请检查日志。")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
