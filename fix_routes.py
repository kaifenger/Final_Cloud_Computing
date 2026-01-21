#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复routes.py文件的脚本"""

ROUTES_CONTENT = '''"""API路由定义"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import uuid
import sys
import asyncio
import os
import wikipedia
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ==================== LLM客户端 ====================
_llm_client = None

def get_llm_client():
    """获取LLM客户端单例"""
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            _llm_client = AsyncOpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )
            print("[INFO] LLM客户端已初始化")
    return _llm_client


async def translate_to_english(chinese_text: str) -> str:
    """使用LLM将中文学术术语翻译成英文"""
    client = get_llm_client()
    if not client:
        return chinese_text
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
                messages=[
                    {"role": "system", "content": "你是一个专业的学术翻译助手，擅长将中文学术术语翻译成精准的英文。"},
                    {"role": "user", "content": f"将以下中文学术术语翻译成英文（只输出英文，不要解释）：{chinese_text}"}
                ],
                temperature=0.1,
                max_tokens=50
            ),
            timeout=10.0
        )
        
        if response and response.choices:
            translation = response.choices[0].message.content.strip().strip('"\\\'""\\'\\'')
            print(f"[SUCCESS] 翻译: {chinese_text} -> {translation}")
            return translation
    except Exception as e:
        print(f"[WARNING] 翻译失败: {chinese_text}, {str(e)}")
    
    return chinese_text


async def generate_brief_summary(concept: str, wiki_definition: str = "") -> str:
    """使用LLM生成一句话简介"""
    client = get_llm_client()
    if not client:
        if wiki_definition:
            return wiki_definition[:100] + "..." if len(wiki_definition) > 100 else wiki_definition
        return f"{concept}是一个重要的跨学科概念。"
    
    try:
        prompt = f"""请为概念"{concept}"生成一句话简介（30-80字），要求：
1. 简洁精准，突出核心特征
2. 通俗易懂，适合普通读者
3. 不要使用"是指"、"是一种"等开头

{f'参考定义：{wiki_definition[:200]}' if wiki_definition else ''}

直接输出简介内容，不要任何解释或标点外的其他内容。"""

        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
                messages=[
                    {"role": "system", "content": "你是一个专业的学术概念总结助手，擅长用简洁的语言概括复杂概念。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            ),
            timeout=15.0
        )
        
        if response and response.choices:
            summary = response.choices[0].message.content.strip()
            summary = summary.strip('"\\\'""\\'\\'')
            print(f"[SUCCESS] LLM生成简介: {concept} -> {summary[:50]}...")
            return summary
    except asyncio.TimeoutError:
        print(f"[WARNING] LLM生成简介超时: {concept}")
    except Exception as e:
        print(f"[WARNING] LLM生成简介失败: {concept}, {str(e)}")
    
    if wiki_definition:
        return wiki_definition[:100] + "..." if len(wiki_definition) > 100 else wiki_definition
    return f"{concept}是一个重要的跨学科概念。"


# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 是否启用外部验证
ENABLE_EXTERNAL_VERIFICATION = os.getenv("ENABLE_EXTERNAL_VERIFICATION", "false").lower() == "true"
print(f"[INFO] 外部验证状态: {'启用' if ENABLE_EXTERNAL_VERIFICATION else '禁用'}")

try:
    from backend.database.neo4j_client import neo4j_client
    from backend.database.redis_client import redis_client
    from backend.config import settings
    from shared.schemas.concept_node import ConceptNode
    from shared.schemas.concept_edge import ConceptEdge
except ImportError:
    class MockClient:
        async def get(self, key): return None
        async def set(self, key, value, ex=None): pass
        async def query(self, query, params=None): return []
        async def create_concept_node(self, node): pass
        async def create_concept_edge(self, edge): pass
    neo4j_client = MockClient()
    redis_client = MockClient()
    
    class MockSettings:
        AGENT_API_URL = "http://localhost:5000"
        REDIS_CACHE_TTL = 3600
    settings = MockSettings()
    
    ConceptNode = dict
    ConceptEdge = dict

router = APIRouter()


async def get_wikipedia_definition(concept: str, max_length: int = 500) -> Dict[str, Any]:
    """从维基百科获取概念的权威定义"""
    if not ENABLE_EXTERNAL_VERIFICATION:
        return {"definition": "", "exists": False, "url": "", "source": "LLM"}
    
    print(f"[INFO] 正在查询Wikipedia: {concept}")
    loop = asyncio.get_event_loop()
    
    try:
        wikipedia.set_lang("zh")
        page = await loop.run_in_executor(None, wikipedia.page, concept)
        summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
        print(f"[SUCCESS] 中文Wikipedia找到: {concept}")
        return {"definition": summary, "exists": True, "url": page.url, "source": "Wikipedia"}
    except wikipedia.exceptions.DisambiguationError as e:
        if e.options:
            try:
                page = await loop.run_in_executor(None, wikipedia.page, e.options[0])
                summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
                return {"definition": summary, "exists": True, "url": page.url, "source": "Wikipedia"}
            except Exception:
                pass
    except wikipedia.exceptions.PageError:
        pass
    except Exception as e:
        print(f"[WARNING] 中文Wikipedia查询失败: {e}")
    
    try:
        wikipedia.set_lang("en")
        page = await loop.run_in_executor(None, wikipedia.page, concept)
        summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
        print(f"[SUCCESS] 英文Wikipedia找到: {concept}")
        return {"definition": summary, "exists": True, "url": page.url, "source": "Wikipedia"}
    except wikipedia.exceptions.DisambiguationError as e:
        if e.options:
            try:
                page = await loop.run_in_executor(None, wikipedia.page, e.options[0])
                summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
                return {"definition": summary, "exists": True, "url": page.url, "source": "Wikipedia"}
            except Exception:
                pass
    except wikipedia.exceptions.PageError:
        pass
    except Exception as e:
        print(f"[WARNING] 英文Wikipedia查询失败: {e}")
    
    print(f"[WARNING] Wikipedia未找到: {concept}")
    return {"definition": "", "exists": False, "url": "", "source": "LLM"}


async def search_arxiv_papers(query: str, max_results: int = 5) -> tuple[List[Dict[str, Any]], str]:
    """在Arxiv搜索相关论文"""
    if not ENABLE_EXTERNAL_VERIFICATION:
        return [], "Arxiv查询已禁用"
    
    if any('\\u4e00' <= char <= '\\u9fff' for char in query):
        print(f"[INFO] 检测到中文查询，正在翻译: {query}")
        query = await translate_to_english(query)
        print(f"[INFO] 翻译后查询: {query}")
    
    print(f"[INFO] 正在查询Arxiv论文: {query}")
    import xml.etree.ElementTree as ET
    
    arxiv_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(arxiv_url, params=params)
            if response.status_code != 200:
                error_msg = f"Arxiv API返回状态码 {response.status_code}"
                print(f"[WARNING] {error_msg}")
                return [], error_msg
            
            root = ET.fromstring(response.text)
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                link = entry.find('atom:id', ns)
                published = entry.find('atom:published', ns)
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text.strip())
                
                papers.append({
                    "title": title.text.strip() if title is not None else "",
                    "authors": authors[:3],
                    "summary": (summary.text.strip()[:200] + "...") if summary is not None and len(summary.text.strip()) > 200 else (summary.text.strip() if summary is not None else ""),
                    "link": link.text.strip() if link is not None else "",
                    "published": published.text.strip()[:10] if published is not None else ""
                })
            
            print(f"[SUCCESS] Arxiv查询成功，找到{len(papers)}篇论文")
            return papers, None
    except httpx.TimeoutException:
        error_msg = "Arxiv API请求超时"
        print(f"[ERROR] {error_msg}")
        return [], error_msg
    except httpx.HTTPError as e:
        error_msg = f"Arxiv API网络错误: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return [], error_msg
    except Exception as e:
        error_msg = f"Arxiv搜索异常: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return [], error_msg


def truncate_definition(text: str, max_length: int = 500) -> str:
    """截断定义文本"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def get_mock_discovery_result(concept: str) -> dict:
    """生成概念挖掘结果"""
    concept_disciplines = {
        "熵": [
            {"label": "熵", "discipline": "热力学", "eng_name": "entropy"},
            {"label": "信息熵", "discipline": "信息论", "eng_name": "information entropy"},
            {"label": "统计熵", "discipline": "统计力学", "eng_name": "statistical entropy"},
        ],
        "深度学习": [
            {"label": "深度学习", "discipline": "人工智能", "eng_name": "deep learning"},
            {"label": "神经网络", "discipline": "计算机科学", "eng_name": "neural network"},
            {"label": "梯度下降", "discipline": "优化理论", "eng_name": "gradient descent"},
        ],
    }
    
    default_concepts = [
        {"label": concept, "discipline": "跨学科", "eng_name": concept},
        {"label": f"{concept}的应用", "discipline": "应用领域", "eng_name": f"{concept} applications"},
        {"label": f"{concept}的理论", "discipline": "理论基础", "eng_name": f"{concept} theory"},
    ]
    
    concept_list = concept_disciplines.get(concept, default_concepts)
    
    nodes = []
    for idx, c in enumerate(concept_list):
        node_id = f"{c['label'].replace(' ', '_')}_{c['discipline'].replace(' ', '_')}_{idx}"
        
        wiki_result = await get_wikipedia_definition(c['label'], max_length=500)
        
        if not wiki_result["exists"] and c.get("eng_name"):
            wiki_result = await get_wikipedia_definition(c['eng_name'], max_length=500)
        
        if wiki_result["exists"]:
            definition = wiki_result["definition"]
            source = "Wikipedia"
            credibility = 0.95
        else:
            definition = f"关于{c['label']}的基本概念，属于{c['discipline']}领域。"
            source = "LLM"
            credibility = 0.75
        
        brief_summary = await generate_brief_summary(c['label'], definition)
        
        nodes.append({
            "id": node_id,
            "label": c['label'],
            "discipline": c['discipline'],
            "definition": truncate_definition(definition, 500),
            "brief_summary": brief_summary,
            "credibility": credibility,
            "source": source,
            "wiki_url": wiki_result.get("url", "")
        })
    
    edges = []
    if len(nodes) > 1:
        center_node = nodes[0]
        for i, node in enumerate(nodes[1:], 1):
            edge = {
                "source": center_node["id"],
                "target": node["id"],
                "relation": "related_to",
                "weight": 0.8 - (i * 0.05),
                "reasoning": f"{center_node['label']}与{node['label']}相关"
            }
            edges.append(edge)
    
    return {
        "status": "success",
        "data": {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "verified_nodes": sum(1 for n in nodes if n["source"] == "Wikipedia"),
                "avg_credibility": sum(n["credibility"] for n in nodes) / len(nodes) if nodes else 0,
                "mode": "mock_with_api"
            }
        }
    }


class DiscoverRequest(BaseModel):
    """概念挖掘请求模型"""
    concept: str = Field(..., min_length=1, max_length=100)
    disciplines: Optional[List[str]] = Field(default=None)
    depth: int = Field(default=2, ge=1, le=3)
    max_concepts: int = Field(default=30, ge=10, le=100)


class DiscoverResponse(BaseModel):
    """概念挖掘响应模型"""
    status: str
    request_id: str
    data: Dict[str, Any]


class GraphResponse(BaseModel):
    """图谱查询响应模型"""
    status: str
    data: Dict[str, Any]


class ExpandRequest(BaseModel):
    """展开请求模型"""
    node_id: str = Field(...)
    node_label: str = Field(...)
    existing_nodes: List[str] = Field(default=[])
    max_new_nodes: int = Field(default=10, ge=1, le=20)


@router.post("/discover", response_model=DiscoverResponse)
async def discover_concepts(request: DiscoverRequest):
    """概念挖掘接口"""
    cache_key = f"discover:{request.concept}"
    cached = await redis_client.get(cache_key)
    if cached:
        return DiscoverResponse(status="success", request_id=cached["request_id"], data=cached["data"])
    
    request_id = str(uuid.uuid4())
    result = await get_mock_discovery_result(request.concept)
    
    if result.get("status") == "success":
        nodes = result["data"]["nodes"]
        edges = result["data"]["edges"]
        
        try:
            for node in nodes:
                await neo4j_client.create_concept_node(node)
            for edge in edges:
                await neo4j_client.create_concept_edge(edge)
        except Exception as e:
            print(f"[WARNING] 保存失败: {e}")
        
        try:
            await redis_client.set(cache_key, {"request_id": request_id, "data": result["data"]}, ex=3600)
        except Exception as e:
            print(f"[WARNING] 缓存失败: {e}")
    
    return DiscoverResponse(status=result.get("status", "success"), request_id=request_id, data=result.get("data", {}))


@router.get("/graph/{concept_id}", response_model=GraphResponse)
async def get_graph(concept_id: str):
    """查询图谱"""
    try:
        graph_data = await neo4j_client.query_graph(concept_id)
        return GraphResponse(status="success", data=graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/arxiv/search")
async def search_arxiv(query: str = Query(...), max_results: int = Query(default=10, ge=1, le=50)):
    """搜索Arxiv论文"""
    papers, error_msg = await search_arxiv_papers(query, max_results=max_results)
    return {
        "status": "success" if error_msg is None else "partial",
        "data": {"query": query, "total": len(papers), "papers": papers, "error": error_msg}
    }


@router.post("/expand")
async def expand_node(request: ExpandRequest):
    """展开节点"""
    print(f"[INFO] 展开节点: {request.node_label}")
    
    domain_concepts = {
        "深度学习": [("神经网络", "计算机科学", "foundation"), ("反向传播", "算法", "methodology")],
        "机器学习": [("监督学习", "方法论", "sub_field"), ("深度学习", "计算机科学", "sub_field")],
    }
    
    related_concepts = domain_concepts.get(request.node_label, [
        (f"{request.node_label}理论", "理论基础", "theory"),
        (f"{request.node_label}应用", "应用领域", "application"),
    ])
    
    new_nodes = []
    new_edges = []
    
    for i, (term, discipline, relation_type) in enumerate(related_concepts):
        node_id = f"{request.node_id}_expand_{i}"
        if node_id not in request.existing_nodes:
            term_wiki = await get_wikipedia_definition(term, max_length=500)
            
            new_nodes.append({
                "id": node_id,
                "label": term,
                "discipline": discipline,
                "definition": term_wiki["definition"] if term_wiki["exists"] else f"{term}相关概念",
                "credibility": 0.90 if term_wiki["exists"] else 0.70,
                "source": "Wikipedia" if term_wiki["exists"] else "LLM",
                "wiki_url": term_wiki.get("url", "")
            })
            
            new_edges.append({
                "source": request.node_id,
                "target": node_id,
                "relation": relation_type,
                "weight": 0.80,
                "reasoning": f"{term}是{request.node_label}的{relation_type}"
            })
    
    return {"status": "success", "data": {"nodes": new_nodes, "edges": new_edges, "parent_id": request.node_id}}


@router.post("/ai/chat")
async def ai_chat(request: dict):
    """AI问答接口"""
    question = request.get("question", "")
    concept = request.get("concept", "")
    
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    client = get_llm_client()
    if not client:
        return {"status": "success", "data": {"answer": "AI服务暂时不可用", "sources": []}}
    
    try:
        system_prompt = f"""你是专业学术助手，擅长解答关于"{concept}"的问题。回答要准确简洁（150字以内）。"""
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.5,
                max_tokens=300
            ),
            timeout=20.0
        )
        
        if response and response.choices:
            answer = response.choices[0].message.content.strip()
            return {"status": "success", "data": {"answer": answer, "sources": ["LLM生成"]}}
    except Exception as e:
        print(f"[ERROR] AI问答失败: {str(e)}")
        return {"status": "error", "data": {"answer": "处理问题时出现错误", "sources": []}}
'''

if __name__ == "__main__":
    import sys
    output_file = "d:/yunjisuanfinal/backend/api/routes.py"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ROUTES_CONTENT)
        print(f"[SUCCESS] 已生成修复后的文件: {output_file}")
        
        # 验证语法
        with open(output_file, 'r', encoding='utf-8') as f:
            compile(f.read(), output_file, 'exec')
        print(f"[SUCCESS] 语法检查通过")
        
    except Exception as e:
        print(f"[ERROR] 生成文件失败: {e}")
        sys.exit(1)
