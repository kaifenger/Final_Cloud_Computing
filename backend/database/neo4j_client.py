"""Neo4j图数据库客户端"""
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any
import os


class Neo4jClient:
    """Neo4j异步客户端"""
    
    def __init__(self):
        self.driver = None
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    async def connect(self):
        """建立数据库连接"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri, 
            auth=(self.user, self.password)
        )
        # 验证连接
        await self.driver.verify_connectivity()
    
    async def disconnect(self):
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
    
    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.driver:
            return False
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False
    
    async def save_graph(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        """保存图谱到Neo4j
        
        Args:
            nodes: 节点列表，每个节点包含 {id, label, discipline, definition, credibility}
            edges: 边列表，每个边包含 {source, target, relation, weight, reasoning}
        """
        async with self.driver.session(database=self.database) as session:
            # 创建节点
            for node in nodes:
                await session.run(
                    """
                    MERGE (n:Concept {id: $id})
                    SET n.label = $label,
                        n.discipline = $discipline,
                        n.definition = $definition,
                        n.credibility = $credibility,
                        n.updated_at = datetime()
                    """,
                    **node
                )
            
            # 创建关系
            for edge in edges:
                await session.run(
                    """
                    MATCH (a:Concept {id: $source})
                    MATCH (b:Concept {id: $target})
                    MERGE (a)-[r:RELATES {type: $relation}]->(b)
                    SET r.weight = $weight,
                        r.reasoning = $reasoning,
                        r.updated_at = datetime()
                    """,
                    **edge
                )
    
    async def query_graph(self, concept_id: str) -> Dict[str, Any]:
        """查询指定概念的图谱数据
        
        Args:
            concept_id: 概念ID
            
        Returns:
            包含nodes和edges的字典
        """
        async with self.driver.session(database=self.database) as session:
            # 查询节点及其关系
            result = await session.run(
                """
                MATCH (n:Concept {id: $concept_id})-[r]-(m:Concept)
                RETURN n, r, m
                """,
                concept_id=concept_id
            )
            
            records = await result.data()
            
            # 解析结果
            nodes = []
            edges = []
            node_ids = set()
            
            for record in records:
                # 添加中心节点
                if record['n']['id'] not in node_ids:
                    nodes.append({
                        'id': record['n']['id'],
                        'label': record['n']['label'],
                        'discipline': record['n']['discipline'],
                        'definition': record['n']['definition'],
                        'credibility': record['n']['credibility']
                    })
                    node_ids.add(record['n']['id'])
                
                # 添加关联节点
                if record['m']['id'] not in node_ids:
                    nodes.append({
                        'id': record['m']['id'],
                        'label': record['m']['label'],
                        'discipline': record['m']['discipline'],
                        'definition': record['m']['definition'],
                        'credibility': record['m']['credibility']
                    })
                    node_ids.add(record['m']['id'])
                
                # 添加边
                edges.append({
                    'source': record['n']['id'],
                    'target': record['m']['id'],
                    'relation': record['r']['type'],
                    'weight': record['r']['weight'],
                    'reasoning': record['r']['reasoning']
                })
            
            return {
                'nodes': nodes,
                'edges': edges
            }
    
    async def search_concepts(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索概念
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            匹配的概念列表
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (n:Concept)
                WHERE n.label CONTAINS $keyword 
                   OR n.definition CONTAINS $keyword
                RETURN n
                ORDER BY n.credibility DESC
                LIMIT $limit
                """,
                keyword=keyword,
                limit=limit
            )
            
            records = await result.data()
            return [
                {
                    'id': record['n']['id'],
                    'label': record['n']['label'],
                    'discipline': record['n']['discipline'],
                    'definition': record['n']['definition'],
                    'credibility': record['n']['credibility']
                }
                for record in records
            ]
    
    async def get_all_disciplines(self) -> List[str]:
        """获取所有学科列表"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (n:Concept)
                RETURN DISTINCT n.discipline as discipline
                ORDER BY discipline
                """
            )
            records = await result.data()
            return [record['discipline'] for record in records]


# 创建全局单例
neo4j_client = Neo4jClient()
