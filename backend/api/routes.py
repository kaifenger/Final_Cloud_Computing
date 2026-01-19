"""API路由定义"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import uuid
import sys
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
    neo4j_client = MockClient()
    redis_client = MockClient()
    
    class MockSettings:
        AGENT_API_URL = "http://localhost:5000"
        REDIS_CACHE_TTL = 3600
    settings = MockSettings()
    
    ConceptNode = dict
    ConceptEdge = dict

router = APIRouter()


# ==================== Mock数据生成函数 ====================

def get_mock_discovery_result(concept: str) -> dict:
    """生成Mock概念挖掘结果（当Agent服务不可用时）"""
    
    # 预定义一些测试概念关系
    mock_graphs = {
        "神经网络": {
            "nodes": [
                {
                    "id": "neural_network_cs",
                    "label": "神经网络",
                    "discipline": "计算机科学",
                    "definition": "模拟生物神经元的计算模型",
                    "credibility": 0.95
                },
                {
                    "id": "neuron_biology",
                    "label": "神经元",
                    "discipline": "生物学",
                    "definition": "神经系统的基本结构和功能单位",
                    "credibility": 0.98
                },
                {
                    "id": "activation_function_math",
                    "label": "激活函数",
                    "discipline": "数学",
                    "definition": "非线性变换函数",
                    "credibility": 0.92
                }
            ],
            "edges": [
                {
                    "source": "neuron_biology",
                    "target": "neural_network_cs",
                    "relation": "inspires",
                    "weight": 0.9,
                    "reasoning": "人工神经网络受生物神经元启发而设计"
                },
                {
                    "source": "activation_function_math",
                    "target": "neural_network_cs",
                    "relation": "is_component_of",
                    "weight": 0.88,
                    "reasoning": "激活函数是神经网络的核心数学组件"
                }
            ]
        },
        "深度学习": {
            "nodes": [
                {
                    "id": "deep_learning_cs",
                    "label": "深度学习",
                    "discipline": "计算机科学",
                    "definition": "基于多层神经网络的机器学习方法",
                    "credibility": 0.96
                },
                {
                    "id": "backprop_math",
                    "label": "反向传播",
                    "discipline": "数学",
                    "definition": "计算梯度的链式法则算法",
                    "credibility": 0.94
                },
                {
                    "id": "gradient_descent_math",
                    "label": "梯度下降",
                    "discipline": "数学",
                    "definition": "优化算法，沿梯度方向迭代更新参数",
                    "credibility": 0.93
                }
            ],
            "edges": [
                {
                    "source": "backprop_math",
                    "target": "deep_learning_cs",
                    "relation": "is_foundation_of",
                    "weight": 0.95,
                    "reasoning": "反向传播是深度学习训练的核心算法"
                },
                {
                    "source": "gradient_descent_math",
                    "target": "deep_learning_cs",
                    "relation": "is_foundation_of",
                    "weight": 0.9,
                    "reasoning": "梯度下降用于优化深度学习模型参数"
                }
            ]
        }
    }
    
    # 如果有预定义的图谱，返回它
    if concept in mock_graphs:
        graph_data = mock_graphs[concept]
    else:
        # 否则生成通用的Mock数据
        graph_data = {
            "nodes": [
                {
                    "id": f"{concept}_concept",
                    "label": concept,
                    "discipline": "跨学科",
                    "definition": f"关于{concept}的基本概念",
                    "credibility": 0.85
                },
                {
                    "id": f"{concept}_related_1",
                    "label": f"{concept}的应用",
                    "discipline": "应用领域",
                    "definition": f"{concept}在实际中的应用",
                    "credibility": 0.80
                },
                {
                    "id": f"{concept}_related_2",
                    "label": f"{concept}的理论基础",
                    "discipline": "理论基础",
                    "definition": f"支撑{concept}的基础理论",
                    "credibility": 0.82
                }
            ],
            "edges": [
                {
                    "source": f"{concept}_related_2",
                    "target": f"{concept}_concept",
                    "relation": "is_foundation_of",
                    "weight": 0.85,
                    "reasoning": f"理论基础支撑{concept}的发展"
                },
                {
                    "source": f"{concept}_concept",
                    "target": f"{concept}_related_1",
                    "relation": "applied_in",
                    "weight": 0.80,
                    "reasoning": f"{concept}在该领域有广泛应用"
                }
            ]
        }
    
    return {
        "status": "success",
        "data": {
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"],
            "metadata": {
                "total_nodes": len(graph_data["nodes"]),
                "total_edges": len(graph_data["edges"]),
                "verified_nodes": len(graph_data["nodes"]),
                "avg_credibility": sum(n["credibility"] for n in graph_data["nodes"]) / len(graph_data["nodes"]),
                "processing_time": 0.5,
                "mode": "mock"
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
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                agent_url,
                json=request.dict()
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            # Agent服务不可用，使用Mock数据（开发模式）
            print(f"[WARNING] Agent服务不可用: {str(e)}")
            print(f"[INFO] 使用Mock模式返回测试数据")
            result = get_mock_discovery_result(request.concept)
    
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
