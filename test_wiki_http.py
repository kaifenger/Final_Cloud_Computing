"""直接测试Wikipedia HTTP API"""
import httpx
import asyncio
import urllib.parse

async def test_wikipedia_direct():
    """直接测试维基百科API"""
    
    concept = "量子计算"
    lang = "zh"
    
    base_url = f"https://{lang}.wikipedia.org/w/api.php"
    
    print(f"测试概念: {concept}")
    print(f"API URL: {base_url}")
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 第一步：opensearch
        search_params = {
            "action": "opensearch",
            "search": concept,
            "limit": "1",
            "namespace": "0",
            "format": "json"
        }
        search_url = f"{base_url}?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in search_params.items())
        print(f"\n1. OpenSearch URL: {search_url}")
        
        search_resp = await client.get(search_url)
        print(f"   状态码: {search_resp.status_code}")
        print(f"   响应: {search_resp.text[:500]}")
        
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            print(f"   解析结果: {search_data}")
            
            if len(search_data) >= 4 and search_data[1]:
                found_title = search_data[1][0]
                page_url = search_data[3][0] if search_data[3] else ""
                print(f"   找到标题: {found_title}")
                print(f"   页面URL: {page_url}")
                
                # 第二步：获取摘要
                query_params = {
                    "action": "query",
                    "titles": found_title,
                    "format": "json",
                    "prop": "extracts",
                    "exintro": "1",
                    "explaintext": "1",
                    "redirects": "1"
                }
                query_url = f"{base_url}?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in query_params.items())
                print(f"\n2. Query URL: {query_url}")
                
                query_resp = await client.get(query_url)
                print(f"   状态码: {query_resp.status_code}")
                
                if query_resp.status_code == 200:
                    data = query_resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_info in pages.items():
                        extract = page_info.get("extract", "")
                        print(f"   页面ID: {page_id}")
                        print(f"   摘要长度: {len(extract)}")
                        print(f"   摘要前200字: {extract[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_wikipedia_direct())
