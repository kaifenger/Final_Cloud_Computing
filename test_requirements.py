"""测试三个核心要求"""
import requests
import json

print("="*60)
print("测试核心要求")
print("="*60)

# 要求1: 节点定义使用Wikipedia API
print("\n【要求1】验证节点定义来自Wikipedia API")
print("-"*60)
r = requests.post('http://localhost:8888/api/v1/discover', 
    json={'concept': '机器学习', 'depth': 1, 'max_concepts': 10}, 
    timeout=120)
data = r.json()
nodes = data.get('data', {}).get('nodes', [])

total_nodes = len(nodes)
wiki_nodes = sum(1 for n in nodes if n.get('source') == 'Wikipedia')
llm_nodes = sum(1 for n in nodes if n.get('source') == 'LLM')

print(f"总节点数: {total_nodes}")
print(f"Wikipedia来源: {wiki_nodes} ({wiki_nodes/total_nodes*100:.1f}%)")
print(f"LLM来源: {llm_nodes} ({llm_nodes/total_nodes*100:.1f}%)")

if nodes:
    print(f"\n示例节点:")
    for i, node in enumerate(nodes[:3], 1):
        print(f"  {i}. {node.get('label')}")
        print(f"     来源: {node.get('source')}")
        print(f"     定义: {node.get('definition', '')[:100]}...")
        if node.get('wiki_url'):
            print(f"     链接: {node.get('wiki_url')}")

result1 = "✅ 通过" if wiki_nodes > llm_nodes else "❌ 失败"
print(f"\n结果: {result1} - Wikipedia定义占比 {wiki_nodes/total_nodes*100:.1f}%")

# 要求2: 相关概念展开显示大模型生成的详细介绍
print("\n【要求2】验证相关概念展开功能")
print("-"*60)
r = requests.get('http://localhost:8888/api/v1/concept/神经网络/detail', timeout=60)
detail_data = r.json().get('data', {})

has_wiki_def = bool(detail_data.get('wiki_definition'))
has_detailed_intro = bool(detail_data.get('detailed_introduction'))
intro_length = len(detail_data.get('detailed_introduction', ''))

print(f"概念名称: {detail_data.get('concept')}")
print(f"Wikipedia定义: {'有' if has_wiki_def else '无'} ({len(detail_data.get('wiki_definition', ''))} 字符)")
print(f"详细介绍: {'有' if has_detailed_intro else '无'} ({intro_length} 字符)")
print(f"相关论文数: {detail_data.get('papers_count', 0)}")

if has_detailed_intro:
    print(f"\n详细介绍内容预览 (前300字):")
    print(detail_data.get('detailed_introduction', '')[:300])
    print("...")

result2 = "✅ 通过" if has_detailed_intro and intro_length > 200 else "❌ 失败"
print(f"\n结果: {result2} - 详细介绍长度 {intro_length} 字符")

# 要求3: 验证Arxiv API检索功能
print("\n【要求3】验证Arxiv API检索功能")
print("-"*60)

test_queries = ["deep learning", "neural networks", "quantum computing"]
all_success = True

for query in test_queries:
    r = requests.get('http://localhost:8888/api/v1/arxiv/search', 
        params={'query': query, 'max_results': 3})
    arxiv_data = r.json()
    
    if arxiv_data.get('status') == 'success':
        papers = arxiv_data.get('data', {}).get('papers', [])
        print(f"✓ '{query}': 检索到 {len(papers)} 篇论文")
        if papers:
            print(f"  示例: {papers[0].get('title')[:60]}...")
    else:
        print(f"✗ '{query}': 检索失败")
        all_success = False

result3 = "✅ 通过" if all_success else "❌ 失败"
print(f"\n结果: {result3} - Arxiv API正常工作")

# 总结
print("\n" + "="*60)
print("测试总结")
print("="*60)
print(f"要求1 - Wikipedia定义: {result1}")
print(f"要求2 - 详细概念展开: {result2}")
print(f"要求3 - Arxiv API: {result3}")

all_passed = all(r == "✅ 通过" for r in [result1, result2, result3])
print(f"\n总体结果: {'🎉 全部通过' if all_passed else '⚠️ 部分失败'}")
print("="*60)
