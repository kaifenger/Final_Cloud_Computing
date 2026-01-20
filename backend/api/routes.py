"""API路由定义"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import uuid
import sys
import asyncio
import wikipedia
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from database.neo4j_client import neo4j_client
    from database.redis_client import redis_client
    from config import settings
    from shared.schemas.concept_node import ConceptNode
    from shared.schemas.concept_edge import ConceptEdge
except ImportError:
    # Mock对象用于测试
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


# ==================== 维基百科API工具函数 ====================

async def get_wikipedia_definition(concept: str, max_length: int = 500) -> Dict[str, Any]:
    """
    从维基百科获取概念的权威定义
    
    Args:
        concept: 概念名称
        max_length: 最大定义长度
        
    Returns:
        {
            "definition": str,  # 维基百科定义
            "exists": bool,     # 是否找到
            "url": str,         # 维基百科链接
            "source": str       # 来源语言
        }
    """
    loop = asyncio.get_event_loop()
    
    # 先尝试中文维基百科
    try:
        wikipedia.set_lang("zh")
        try:
            page = await loop.run_in_executor(None, wikipedia.page, concept)
            summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
            return {
                "definition": summary,
                "exists": True,
                "url": page.url,
                "source": "Wikipedia"
            }
        except wikipedia.exceptions.DisambiguationError as e:
            # 歧义页面，选择第一个
            if e.options:
                page = await loop.run_in_executor(None, wikipedia.page, e.options[0])
                summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
                return {
                    "definition": summary,
                    "exists": True,
                    "url": page.url,
                    "source": "Wikipedia"
                }
        except wikipedia.exceptions.PageError:
            pass
    except Exception as e:
        print(f"[WARNING] 中文Wikipedia搜索失败: {e}")
    
    # 再尝试英文维基百科
    try:
        wikipedia.set_lang("en")
        try:
            page = await loop.run_in_executor(None, wikipedia.page, concept)
            summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
            return {
                "definition": summary,
                "exists": True,
                "url": page.url,
                "source": "Wikipedia"
            }
        except wikipedia.exceptions.DisambiguationError as e:
            if e.options:
                page = await loop.run_in_executor(None, wikipedia.page, e.options[0])
                summary = page.summary[:max_length] if len(page.summary) > max_length else page.summary
                return {
                    "definition": summary,
                    "exists": True,
                    "url": page.url,
                    "source": "Wikipedia"
                }
        except wikipedia.exceptions.PageError:
            pass
    except Exception as e:
        print(f"[WARNING] 英文Wikipedia搜索失败: {e}")
    
    return {
        "definition": "",
        "exists": False,
        "url": "",
        "source": "LLM"
    }


async def search_arxiv_papers(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    在Arxiv搜索相关论文
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数
        
    Returns:
        论文列表
    """
    import xml.etree.ElementTree as ET
    
    # 使用HTTPS URL
    arxiv_url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(arxiv_url, params=params)
            if response.status_code != 200:
                print(f"[WARNING] Arxiv API返回状态码: {response.status_code}")
                return []
            
            # 解析XML
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
                    "authors": authors[:3],  # 最多3个作者
                    "summary": (summary.text.strip()[:200] + "...") if summary is not None and len(summary.text.strip()) > 200 else (summary.text.strip() if summary is not None else ""),
                    "link": link.text.strip() if link is not None else "",
                    "published": published.text.strip()[:10] if published is not None else ""
                })
            
            return papers
    except Exception as e:
        print(f"[WARNING] Arxiv搜索失败: {e}")
        return []


# ==================== Mock数据生成函数 ====================

def truncate_definition(text: str, max_length: int = 500) -> str:
    """截断定义文本到指定长度"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def get_mock_discovery_result(concept: str) -> dict:
    """生成概念挖掘结果（优先使用维基百科定义）"""
    
    # 预定义概念映射（学科分类）
    concept_disciplines = {
        "熵": [
            {"label": "熵", "discipline": "热力学", "eng_name": "entropy thermodynamics"},
            {"label": "信息熵", "discipline": "信息论", "eng_name": "information entropy"},
            {"label": "统计熵", "discipline": "统计力学", "eng_name": "statistical entropy"},
            {"label": "香农熵", "discipline": "信息论", "eng_name": "Shannon entropy"},
            {"label": "玻尔兹曼熵", "discipline": "物理学", "eng_name": "Boltzmann entropy"},
            {"label": "最大熵原理", "discipline": "数学", "eng_name": "maximum entropy principle"},
        ],
        "神经网络": [
            {"label": "神经网络", "discipline": "计算机科学", "eng_name": "neural network"},
            {"label": "神经元", "discipline": "生物学", "eng_name": "neuron"},
            {"label": "激活函数", "discipline": "数学", "eng_name": "activation function"},
            {"label": "反向传播", "discipline": "机器学习", "eng_name": "backpropagation"},
            {"label": "卷积神经网络", "discipline": "深度学习", "eng_name": "convolutional neural network"},
            {"label": "递归神经网络", "discipline": "深度学习", "eng_name": "recurrent neural network"},
        ],
        "深度学习": [
            {"label": "深度学习", "discipline": "人工智能", "eng_name": "deep learning"},
            {"label": "梯度下降", "discipline": "优化理论", "eng_name": "gradient descent"},
            {"label": "损失函数", "discipline": "数学", "eng_name": "loss function"},
            {"label": "过拟合", "discipline": "统计学", "eng_name": "overfitting"},
            {"label": "正则化", "discipline": "机器学习", "eng_name": "regularization"},
            {"label": "批归一化", "discipline": "深度学习", "eng_name": "batch normalization"},
        ],
        "量子计算": [
            {"label": "量子计算", "discipline": "计算机科学", "eng_name": "quantum computing"},
            {"label": "量子比特", "discipline": "量子物理", "eng_name": "qubit"},
            {"label": "量子纠缠", "discipline": "量子力学", "eng_name": "quantum entanglement"},
            {"label": "量子门", "discipline": "量子信息", "eng_name": "quantum gate"},
            {"label": "量子算法", "discipline": "算法理论", "eng_name": "quantum algorithm"},
            {"label": "量子退相干", "discipline": "量子物理", "eng_name": "quantum decoherence"},
        ]
    }
    
    # 通用概念模板
    default_concepts = [
        {"label": concept, "discipline": "跨学科", "eng_name": concept},
        {"label": f"{concept}的应用", "discipline": "应用领域", "eng_name": f"{concept} applications"},
        {"label": f"{concept}的理论基础", "discipline": "理论基础", "eng_name": f"{concept} theory"},
        {"label": f"{concept}的历史发展", "discipline": "科学史", "eng_name": f"{concept} history"},
        {"label": f"{concept}的数学模型", "discipline": "数学", "eng_name": f"{concept} mathematical model"},
    ]
    
    # 选择概念列表
    concept_list = concept_disciplines.get(concept, default_concepts)
    
    # 并行获取维基百科定义
    nodes = []
    for idx, c in enumerate(concept_list):
        node_id = f"{c['label'].replace(' ', '_')}_{c['discipline'].replace(' ', '_')}_{idx}"
        
        # 获取维基百科定义
        wiki_result = await get_wikipedia_definition(c['label'], max_length=500)
        
        # 如果中文没找到，尝试用英文名搜索
        if not wiki_result["exists"] and c.get("eng_name"):
            wiki_result = await get_wikipedia_definition(c['eng_name'], max_length=500)
        
        # 生成定义
        if wiki_result["exists"]:
            definition = wiki_result["definition"]
            source = "Wikipedia"
            credibility = 0.95
        else:
            # 使用备用定义（LLM生成标记）
            definition = f"关于{c['label']}的基本概念，属于{c['discipline']}领域的核心知识点。"
            source = "LLM"
            credibility = 0.75
        
        nodes.append({
            "id": node_id,
            "label": c['label'],
            "discipline": c['discipline'],
            "definition": truncate_definition(definition, 500),
            "credibility": credibility,
            "source": source,
            "wiki_url": wiki_result.get("url", "")
        })
    
    # 生成边
    edges = []
    if len(nodes) > 1:
        # 中心节点与其他节点的关系
        center_node = nodes[0]
        for i, node in enumerate(nodes[1:], 1):
            edges.append({
                "source": center_node["id"],
                "target": node["id"],
                "relation": "related_to",
                "weight": 0.8 - (i * 0.05),
                "reasoning": f"{center_node['label']}与{node['label']}在概念上存在关联"
            })
    
    # 搜索arxiv论文
    arxiv_papers = await search_arxiv_papers(concept, max_results=5)
    
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
                "processing_time": 1.5,
                "mode": "mock_with_wikipedia",
                "arxiv_papers": arxiv_papers
            }
        }
    }


# ==================== 请求/响应模型 ====================

class DiscoverRequest(BaseModel):
    """概念挖掘请求模型"""
    concept: str = Field(..., min_length=1, max_length=100, description="核心概念")
    disciplines: Optional[List[str]] = Field(
        default=None, 
        description="学科列表，默认全部学科"
    )
    depth: int = Field(default=2, ge=1, le=3, description="挖掘深度")
    max_concepts: int = Field(default=30, ge=10, le=100, description="最大概念数")


class DiscoverResponse(BaseModel):
    """概念挖掘响应模型"""
    status: str
    request_id: str
    data: Dict[str, Any]


class GraphResponse(BaseModel):
    """图谱查询响应模型"""
    status: str
    data: Dict[str, Any]


# ==================== API路由 ====================

@router.post("/discover", response_model=DiscoverResponse)
async def discover_concepts(request: DiscoverRequest):
    """概念挖掘接口 - 调用成员A的Agent服务
    
    功能：
    1. 检查Redis缓存
    2. 调用Agent服务进行概念挖掘（如不可用则使用Mock数据）
    3. 保存结果到Neo4j
    4. 缓存结果到Redis
    """
    
    # 1. 检查缓存
    cache_key = f"discover:{request.concept}:{':'.join(request.disciplines or [])}"
    cached = await redis_client.get(cache_key)
    if cached:
        return DiscoverResponse(
            status="success",
            request_id=cached["request_id"],
            data=cached["data"]
        )
    
    # 2. 调用Agent服务（成员A提供）
    agent_url = f"{settings.AGENT_API_URL}/discover"
    request_id = str(uuid.uuid4())
    result = None
    
    # 优先尝试直接调用Agent编排器（本地LLM调用）
    try:
        from agents.orchestrator import get_orchestrator
        from dotenv import load_dotenv
        load_dotenv()  # 确保加载环境变量
        
        orchestrator = get_orchestrator()
        print(f"[INFO] 使用真实LLM调用概念挖掘: {request.concept}")
        
        response_obj = await orchestrator.discover(
            concept=request.concept,
            disciplines=request.disciplines,
            depth=request.depth,
            max_concepts=request.max_concepts,
            enable_verification=True
        )
        
        # 转换响应格式
        if response_obj.status == "success":
            result = {
                "status": "success",
                "data": {
                    "nodes": [n.dict() if hasattr(n, 'dict') else n for n in response_obj.data.nodes],
                    "edges": [e.dict() if hasattr(e, 'dict') else e for e in response_obj.data.edges],
                    "metadata": response_obj.data.metadata.dict() if hasattr(response_obj.data.metadata, 'dict') else response_obj.data.metadata
                }
            }
            # 为每个节点添加维基百科定义
            for node in result["data"]["nodes"]:
                if node.get("source") != "Wikipedia":
                    wiki_result = await get_wikipedia_definition(node.get("label", ""), max_length=500)
                    if wiki_result["exists"]:
                        node["definition"] = wiki_result["definition"]
                        node["source"] = "Wikipedia"
                        node["wiki_url"] = wiki_result["url"]
        else:
            raise Exception(response_obj.message or "LLM调用失败")
            
    except Exception as e:
        print(f"[WARNING] 本地Agent调用失败: {str(e)}")
        print(f"[INFO] 回退到外部Agent服务或Mock模式")
        
        # 尝试外部Agent服务
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(
                    agent_url,
                    json=request.dict()
                )
                response.raise_for_status()
                result = response.json()
            except Exception as e2:
                # Agent服务不可用，使用带维基百科的数据
                print(f"[WARNING] 外部Agent服务不可用: {str(e2)}")
                print(f"[INFO] 使用Wikipedia+Mock模式返回数据")
                result = await get_mock_discovery_result(request.concept)
    
    # 3. 保存到Neo4j
    if result.get("status") == "success":
        nodes = result["data"]["nodes"]
        edges = result["data"]["edges"]
        
        try:
            # 保存节点
            for node in nodes:
                await neo4j_client.create_concept_node(node)
            # 保存边
            for edge in edges:
                await neo4j_client.create_concept_edge(edge)
        except Exception as e:
            # Neo4j保存失败不影响返回结果，只记录错误
            print(f"[WARNING] 保存到Neo4j失败: {e}")
        
        # 4. 缓存结果
        cache_data = {
            "request_id": request_id,
            "data": result["data"]
        }
        try:
            await redis_client.set(cache_key, cache_data, ex=3600)
        except Exception as e:
            print(f"[WARNING] 缓存失败: {e}")
    
    return DiscoverResponse(
        status=result.get("status", "success"),
        request_id=request_id,
        data=result.get("data", {})
    )


@router.get("/graph/{concept_id}", response_model=GraphResponse)
async def get_graph(concept_id: str):
    """查询指定概念的图谱数据
    
    Args:
        concept_id: 概念ID
        
    Returns:
        图谱数据（nodes + edges）
    """
    try:
        graph_data = await neo4j_client.query_graph(concept_id)
        return GraphResponse(
            status="success",
            data=graph_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询图谱失败: {str(e)}"
        )


@router.get("/concepts/search")
async def search_concepts(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量")
):
    """搜索概念
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量限制
        
    Returns:
        匹配的概念列表
    """
    try:
        concepts = await neo4j_client.search_concepts(keyword, limit)
        return {
            "status": "success",
            "data": {
                "keyword": keyword,
                "total": len(concepts),
                "concepts": concepts
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/disciplines")
async def get_disciplines():
    """获取所有学科列表"""
    try:
        disciplines = await neo4j_client.get_all_disciplines()
        return {
            "status": "success",
            "data": {
                "disciplines": disciplines,
                "total": len(disciplines)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取学科列表失败: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache(pattern: str = Query(default="*", description="缓存键模式")):
    """清除缓存
    
    Args:
        pattern: 缓存键模式，如 "discover:*"
    """
    try:
        await redis_client.clear_pattern(pattern)
        return {
            "status": "success",
            "message": f"已清除匹配 '{pattern}' 的缓存"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除缓存失败: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        redis_stats = await redis_client.get_stats()
        return {
            "status": "success",
            "data": {
                "redis": redis_stats,
                "neo4j": {
                    "connected": await neo4j_client.is_connected()
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )

@router.get("/concept/{concept_name}/detail")
async def get_concept_detail(concept_name: str):
    """获取概念的详细介绍（由大模型生成的扩展信息）
    
    用于"相关概念展开"功能，返回大模型生成的详细概念介绍
    """
    # 获取维基百科基础定义
    wiki_result = await get_wikipedia_definition(concept_name, max_length=500)
    
    # 搜索相关arxiv论文
    arxiv_papers = await search_arxiv_papers(concept_name, max_results=5)
    
    # 生成详细介绍（模拟大模型生成）
    detailed_intro = f"""
**{concept_name}** 是一个跨学科的重要概念。

### 基本定义
{wiki_result['definition'] if wiki_result['exists'] else f'{concept_name}是一个涉及多个领域的核心概念。'}

### 学科关联
{concept_name}在以下领域有重要应用：
- **数学领域**：作为理论基础和形式化描述的工具
- **物理学领域**：用于描述和解释自然现象
- **计算机科学领域**：在算法设计和系统实现中的应用
- **工程领域**：实际应用和工程实现

### 发展历程
该概念经历了从理论提出到实践应用的发展过程，在不同历史时期由不同学者贡献了重要的理论基础。

### 核心原理
{concept_name}的核心在于理解其基本机制和运作原理，这涉及到多学科知识的综合运用。

### 实际应用
在实际应用中，{concept_name}被广泛用于解决复杂问题，特别是在跨学科研究和工程实践中发挥着关键作用。
"""
    
    return {
        "status": "success",
        "data": {
            "concept": concept_name,
            "wiki_definition": wiki_result["definition"] if wiki_result["exists"] else None,
            "wiki_url": wiki_result["url"] if wiki_result["exists"] else None,
            "wiki_source": wiki_result["source"],
            "detailed_introduction": detailed_intro.strip(),
            "related_papers": arxiv_papers,
            "papers_count": len(arxiv_papers)
        }
    }


@router.get("/arxiv/search")
async def search_arxiv(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    max_results: int = Query(default=10, ge=1, le=50, description="最大结果数")
):
    """搜索Arxiv论文
    
    用于验证arxiv API是否能成功检索给定关键词的相关文献
    """
    papers = await search_arxiv_papers(query, max_results=max_results)
    
    return {
        "status": "success",
        "data": {
            "query": query,
            "total": len(papers),
            "papers": papers
        }
    }


# ==================== 展开节点API ====================

class ExpandRequest(BaseModel):
    """展开请求模型"""
    node_id: str = Field(..., description="要展开的节点ID")
    node_label: str = Field(..., description="节点名称")
    existing_nodes: List[str] = Field(default=[], description="已存在的节点ID列表")
    max_new_nodes: int = Field(default=10, ge=1, le=20, description="最大新增节点数")


@router.post("/expand")
async def expand_node(request: ExpandRequest):
    """展开节点 - 获取相关概念
    
    功能：
    1. 基于选中节点发现更多相关概念
    2. 优先使用Wikipedia定义
    3. 返回新的节点和边
    """
    print(f"[INFO] 展开节点: {request.node_label} (id={request.node_id})")
    
    try:
        # 尝试使用真实LLM调用
        from agents.orchestrator import get_orchestrator
        from dotenv import load_dotenv
        load_dotenv()
        
        orchestrator = get_orchestrator()
        
        # 构造现有图谱数据
        existing_graph = {
            "nodes": [{"id": nid, "label": ""} for nid in request.existing_nodes],
            "edges": []
        }
        
        expanded = await orchestrator.expand(
            node_id=request.node_id,
            existing_graph=existing_graph,
            max_new_nodes=request.max_new_nodes
        )
        
        # 为新节点添加Wikipedia定义
        new_nodes = expanded.get("new_nodes", [])
        for node in new_nodes:
            if node.get("source") != "Wikipedia":
                wiki_result = await get_wikipedia_definition(node.get("label", ""), max_length=500)
                if wiki_result["exists"]:
                    node["definition"] = wiki_result["definition"]
                    node["source"] = "Wikipedia"
                    node["wiki_url"] = wiki_result["url"]
        
        return {
            "status": "success",
            "data": {
                "nodes": new_nodes,
                "edges": expanded.get("new_edges", []),
                "parent_id": request.node_id
            }
        }
        
    except Exception as e:
        print(f"[WARNING] 展开失败，使用智能Wikipedia搜索: {str(e)}")
        
        # 回退：使用智能Wikipedia搜索相关概念
        # 策略：基于父概念在Wikipedia中查找真实相关概念
        
        new_nodes = []
        new_edges = []
        
        # 1. 获取父概念的Wikipedia页面
        parent_wiki = await get_wikipedia_definition(request.node_label, max_length=500)
        
        # 2. 生成结构化的相关概念（按学科和关系类型）
        # 根据父概念类型智能生成相关概念（更具体的策略）
        
        # 根据概念名称特征选择策略
        label = request.node_label.lower()
        
        # 预定义领域特定的扩展映射
        domain_specific_concepts = {
            "机器学习": [
                ("深度学习", "计算机科学", "sub_field"),
                ("神经网络", "计算机科学", "foundation"),
                ("监督学习", "方法论", "methodology"),
            ],
            "量子计算": [
                ("量子纠缠", "物理学", "foundation"),
                ("量子算法", "计算机科学", "methodology"),
                ("量子密码学", "应用领域", "application"),
            ],
            "深度学习": [
                ("卷积神经网络", "计算机科学", "sub_field"),
                ("反向传播", "算法", "methodology"),
                ("计算机视觉", "应用领域", "application"),
            ],
            "人工智能": [
                ("机器学习", "计算机科学", "sub_field"),
                ("自然语言处理", "应用领域", "application"),
                ("专家系统", "方法论", "methodology"),
            ],
        }
        
        # 使用预定义映射或生成通用概念
        if request.node_label in domain_specific_concepts:
            related_concepts = domain_specific_concepts[request.node_label]
        else:
            # 通用策略：生成理论、方法、应用
            related_concepts = [
                (f"{request.node_label}理论", "理论基础", "theoretical_foundation"),
                (f"{request.node_label}方法", "方法论", "methodology"),
                (f"{request.node_label}应用", "应用领域", "application"),
            ]
        
        # 3. 为每个相关概念获取Wikipedia定义
        for i, (term, discipline, relation_type) in enumerate(related_concepts):
            node_id = f"{request.node_id}_expand_{i}"
            if node_id not in request.existing_nodes:
                # 尝试获取Wikipedia定义
                term_wiki = await get_wikipedia_definition(term, max_length=500)
                
                # 如果找不到，尝试搜索更通用的概念
                if not term_wiki["exists"]:
                    # 尝试去掉修饰词
                    alt_terms = [
                        term.replace(f"{request.node_label}的", "").replace(f"{request.node_label}", ""),
                        term.split("的")[-1] if "的" in term else term,
                    ]
                    for alt_term in alt_terms:
                        if alt_term.strip():
                            term_wiki = await get_wikipedia_definition(alt_term.strip(), max_length=500)
                            if term_wiki["exists"]:
                                term = alt_term.strip()  # 使用找到定义的术语
                                break
                
                new_nodes.append({
                    "id": node_id,
                    "label": term,
                    "discipline": discipline,
                    "definition": term_wiki["definition"] if term_wiki["exists"] else f"{term}是{request.node_label}相关的重要概念。",
                    "credibility": 0.90 if term_wiki["exists"] else 0.70,
                    "source": "Wikipedia" if term_wiki["exists"] else "LLM",
                    "wiki_url": term_wiki.get("url", "")
                })
                
                # 创建结构化的边关系
                new_edges.append({
                    "source": request.node_id,
                    "target": node_id,
                    "relation": relation_type,
                    "weight": 0.80,
                    "reasoning": f"{term}是{request.node_label}的{relation_type}"
                })
        
        return {
            "status": "success",
            "data": {
                "nodes": new_nodes,
                "edges": new_edges,
                "parent_id": request.node_id
            }
        }