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
    2. 调用Agent服务进行概念挖掘
    3. 保存结果到Neo4j
    4. 缓存结果到Redis
    """
    
    # 1. 检查缓存
    cache_key = f"discover:{request.concept}:{':'.join(request.disciplines or [])}"
    cached = await redis_client.get_cached(cache_key)
    if cached:
        return DiscoverResponse(
            status="success",
            request_id=cached["request_id"],
            data=cached["data"]
        )
    
    # 2. 调用Agent服务（成员A提供）
    agent_url = f"{settings.AGENT_SERVICE_URL}/discover"
    request_id = str(uuid.uuid4())
    
    async with httpx.AsyncClient(timeout=settings.AGENT_TIMEOUT) as client:
        try:
            response = await client.post(
                agent_url,
                json=request.dict()
            )
            response.raise_for_status()
            result = response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="Agent服务超时，请稍后重试"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Agent服务错误: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Agent调用失败: {str(e)}"
            )
    
    # 3. 保存到Neo4j
    if result.get("status") == "success":
        nodes = result["data"]["nodes"]
        edges = result["data"]["edges"]
        
        try:
            await neo4j_client.save_graph(nodes, edges)
        except Exception as e:
            # Neo4j保存失败不影响返回结果，只记录错误
            print(f"[WARNING] 保存到Neo4j失败: {e}")
        
        # 4. 缓存结果
        cache_data = {
            "request_id": request_id,
            "data": result["data"]
        }
        try:
            await redis_client.cache_result(cache_key, cache_data)
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
