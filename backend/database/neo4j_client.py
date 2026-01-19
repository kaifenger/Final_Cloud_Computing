"""Neo4j图数据库客户端"""
import os
from typing import List, Dict, Any, Optional
from loguru import logger


class Neo4jClient:
    """Neo4j数据库客户端（支持Mock模式）"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "conceptgraph")
        self.driver = None
        self.mock_mode = os.getenv("MOCK_DB", "true").lower() == "true"
        
    async def connect(self):
        """连接到Neo4j数据库"""
        if self.mock_mode:
            logger.info("[MOCK] Neo4j客户端运行在Mock模式")
            return
            
        try:
            from neo4j import AsyncGraphDatabase
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 测试连接
            async with self.driver.session(database=self.database) as session:
                await session.run("RETURN 1")
            logger.info(f"已连接到Neo4j: {self.uri}")
        except ImportError:
            logger.warning("neo4j包未安装，切换到Mock模式")
            self.mock_mode = True
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}，切换到Mock模式")
            self.mock_mode = True
    
    async def disconnect(self):
        """断开连接"""
        if self.driver:
            await self.driver.close()
            logger.info("已断开Neo4j连接")
    
    async def is_connected(self) -> bool:
        """检查连接状态"""
        if self.mock_mode:
            return True
        return self.driver is not None
    
    async def query(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        if self.mock_mode:
            logger.debug(f"[MOCK] 执行查询: {cypher[:100]}...")
            return self._mock_query_result(cypher, parameters)
        
        if not self.driver:
            raise RuntimeError("未连接到Neo4j数据库")
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(cypher, parameters or {})
            return [record.data() async for record in result]
    
    def _mock_query_result(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Mock查询结果"""
        # 根据查询类型返回不同的mock数据
        if "MATCH" in cypher.upper() and "RETURN" in cypher.upper():
            # 模拟节点查询
            return [
                {
                    "node": {
                        "id": "mock-1",
                        "label": "神经网络",
                        "discipline": "计算机科学",
                        "definition": "一种模仿生物神经网络的计算模型",
                        "credibility": 0.95
                    }
                },
                {
                    "node": {
                        "id": "mock-2",
                        "label": "深度学习",
                        "discipline": "人工智能",
                        "definition": "基于多层神经网络的机器学习方法",
                        "credibility": 0.92
                    }
                }
            ]
        elif "CREATE" in cypher.upper():
            # 模拟创建操作
            return [{"created": True}]
        else:
            return []
    
    async def create_concept_node(self, concept_data: Dict[str, Any]) -> str:
        """创建概念节点"""
        cypher = """
        MERGE (c:Concept {id: $id})
        SET c.label = $label,
            c.discipline = $discipline,
            c.definition = $definition,
            c.credibility = $credibility,
            c.created_at = timestamp(),
            c.updated_at = timestamp()
        RETURN c.id as id
        """
        result = await self.query(cypher, concept_data)
        return result[0]["id"] if result else concept_data["id"]
    
    async def create_concept_edge(self, edge_data: Dict[str, Any]) -> bool:
        """创建概念关系边"""
        cypher = """
        MATCH (s:Concept {id: $source})
        MATCH (t:Concept {id: $target})
        MERGE (s)-[r:RELATES {type: $relation}]->(t)
        SET r.weight = $weight,
            r.reasoning = $reasoning,
            r.created_at = timestamp(),
            r.updated_at = timestamp()
        RETURN r
        """
        result = await self.query(cypher, edge_data)
        return len(result) > 0
    
    async def get_concept_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """根据标签查询概念"""
        cypher = """
        MATCH (c:Concept {label: $label})
        RETURN c
        """
        result = await self.query(cypher, {"label": label})
        return result[0]["c"] if result else None
    
    async def get_related_concepts(self, concept_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取关联概念"""
        cypher = f"""
        MATCH path = (c:Concept {{id: $concept_id}})-[*1..{depth}]-(related:Concept)
        RETURN DISTINCT related
        """
        result = await self.query(cypher, {"concept_id": concept_id})
        return [r["related"] for r in result]


# 全局实例
neo4j_client = Neo4jClient()
