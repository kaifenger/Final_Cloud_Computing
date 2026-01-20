"""
测试维基百科API和Arxiv API功能
使用 py -3.11 test_apis.py 运行
"""

import asyncio
import sys


async def test_wikipedia_api():
    """测试维基百科API"""
    print("\n" + "="*60)
    print("测试维基百科API")
    print("="*60)
    
    try:
        import wikipedia
        
        # 测试中文维基百科
        test_concepts = ["熵", "神经网络", "量子计算", "深度学习"]
        
        for concept in test_concepts:
            print(f"\n🔍 搜索: {concept}")
            try:
                wikipedia.set_lang("zh")
                page = wikipedia.page(concept)
                summary = page.summary[:200] + "..." if len(page.summary) > 200 else page.summary
                print(f"   ✅ 找到: {page.title}")
                print(f"   📖 摘要: {summary}")
                print(f"   🔗 链接: {page.url}")
            except wikipedia.exceptions.DisambiguationError as e:
                print(f"   ⚠️ 歧义页面，选项: {e.options[:3]}")
                # 尝试第一个选项
                if e.options:
                    page = wikipedia.page(e.options[0])
                    print(f"   ✅ 选择: {page.title}")
            except wikipedia.exceptions.PageError:
                print(f"   ❌ 中文未找到，尝试英文...")
                try:
                    wikipedia.set_lang("en")
                    page = wikipedia.page(concept)
                    print(f"   ✅ 英文找到: {page.title}")
                except:
                    print(f"   ❌ 英文也未找到")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
        
        print("\n✅ 维基百科API测试完成!")
        return True
        
    except ImportError:
        print("❌ wikipedia包未安装，请运行: py -3.11 -m pip install wikipedia")
        return False


async def test_arxiv_api():
    """测试Arxiv API"""
    print("\n" + "="*60)
    print("测试Arxiv API")
    print("="*60)
    
    try:
        import httpx
        import xml.etree.ElementTree as ET
        
        # 使用HTTPS URL
        arxiv_url = "https://export.arxiv.org/api/query"
        test_queries = ["entropy", "neural network", "quantum computing", "deep learning"]
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for query in test_queries:
                print(f"\n🔍 搜索: {query}")
                
                params = {
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": 3,
                    "sortBy": "relevance",
                    "sortOrder": "descending"
                }
                
                try:
                    response = await client.get(arxiv_url, params=params)
                    
                    if response.status_code == 200:
                        # 解析XML
                        root = ET.fromstring(response.text)
                        ns = {
                            'atom': 'http://www.w3.org/2005/Atom',
                            'arxiv': 'http://arxiv.org/schemas/atom'
                        }
                        
                        entries = root.findall('atom:entry', ns)
                        print(f"   ✅ 找到 {len(entries)} 篇论文")
                        
                        for i, entry in enumerate(entries[:2], 1):
                            title = entry.find('atom:title', ns)
                            link = entry.find('atom:id', ns)
                            
                            if title is not None:
                                title_text = title.text.strip().replace('\n', ' ')[:80]
                                print(f"   📄 [{i}] {title_text}...")
                            if link is not None:
                                print(f"       🔗 {link.text.strip()}")
                    else:
                        print(f"   ❌ HTTP错误: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ 请求失败: {e}")
        
        print("\n✅ Arxiv API测试完成!")
        return True
        
    except ImportError:
        print("❌ httpx包未安装，请运行: py -3.11 -m pip install httpx")
        return False


async def test_backend_api():
    """测试后端API"""
    print("\n" + "="*60)
    print("测试后端API连接")
    print("="*60)
    
    try:
        import httpx
        
        base_url = "http://localhost:8888"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试根路径
            print("\n🔍 测试根路径...")
            try:
                response = await client.get(f"{base_url}/")
                if response.status_code == 200:
                    print(f"   ✅ 根路径: {response.json()}")
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 连接失败: {e}")
                print("   💡 请先启动后端: cd backend && py -3.11 -m uvicorn main:app --reload --port 8888")
                return False
            
            # 测试健康检查
            print("\n🔍 测试健康检查...")
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    print(f"   ✅ 健康状态: {response.json()}")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
            
            # 测试发现接口
            print("\n🔍 测试概念发现接口 (熵)...")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/discover",
                    json={"concept": "熵", "depth": 1, "max_concepts": 10},
                    timeout=120.0
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 状态: {data.get('status')}")
                    if 'data' in data and 'nodes' in data['data']:
                        nodes = data['data']['nodes']
                        print(f"   📊 发现 {len(nodes)} 个节点")
                        for node in nodes[:3]:
                            source = node.get('source', 'LLM')
                            print(f"      - {node['label']} ({node['discipline']}) [来源: {source}]")
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
                    print(f"   📝 响应: {response.text[:200]}")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
            
            # 测试Arxiv搜索接口
            print("\n🔍 测试Arxiv搜索接口...")
            try:
                response = await client.get(
                    f"{base_url}/api/v1/arxiv/search",
                    params={"query": "entropy", "max_results": 3},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 找到 {data['data']['total']} 篇论文")
                    for paper in data['data']['papers'][:2]:
                        print(f"      - {paper['title'][:60]}...")
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
            
            # 测试概念详情接口
            print("\n🔍 测试概念详情接口...")
            try:
                response = await client.get(
                    f"{base_url}/api/v1/concept/熵/detail",
                    timeout=60.0
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 获取成功")
                    print(f"      - 维基定义: {data['data']['wiki_definition'][:100] if data['data']['wiki_definition'] else '无'}...")
                    print(f"      - 相关论文: {data['data']['papers_count']} 篇")
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
        
        print("\n✅ 后端API测试完成!")
        return True
        
    except ImportError:
        print("❌ httpx包未安装")
        return False


async def main():
    print("="*60)
    print("ConceptGraph AI - API功能测试")
    print("="*60)
    
    # 测试维基百科API
    wiki_ok = await test_wikipedia_api()
    
    # 测试Arxiv API
    arxiv_ok = await test_arxiv_api()
    
    # 测试后端API
    backend_ok = await test_backend_api()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"维基百科API: {'✅ 通过' if wiki_ok else '❌ 失败'}")
    print(f"Arxiv API: {'✅ 通过' if arxiv_ok else '❌ 失败'}")
    print(f"后端API: {'✅ 通过' if backend_ok else '❌ 失败'}")
    
    if not backend_ok:
        print("\n💡 启动后端的命令:")
        print("   cd D:\\yunjisuanfinal\\backend")
        print("   py -3.11 -m uvicorn main:app --reload --port 8888")


if __name__ == "__main__":
    asyncio.run(main())
