"""Redis缓存客户端"""
import redis.asyncio as redis
import json
import os
from typing import Any, Optional


class RedisClient:
    """Redis异步客户端"""
    
    def __init__(self):
        self.client = None
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")
        self.ttl = int(os.getenv("REDIS_CACHE_TTL", 3600))
    
    async def connect(self):
        """建立Redis连接"""
        self.client = await redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True
        )
    
    async def disconnect(self):
        """关闭Redis连接"""
        if self.client:
            await self.client.close()
    
    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False
    
    async def cache_result(self, key: str, value: Any, ttl: Optional[int] = None):
        """缓存查询结果
        
        Args:
            key: 缓存键
            value: 缓存值（会自动序列化为JSON）
            ttl: 过期时间（秒），默认使用配置的TTL
        """
        if ttl is None:
            ttl = self.ttl
        
        await self.client.setex(
            key,
            ttl,
            json.dumps(value, ensure_ascii=False)
        )
    
    async def get_cached(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值（自动反序列化），如果不存在返回None
        """
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete_cache(self, key: str):
        """删除缓存
        
        Args:
            key: 缓存键
        """
        await self.client.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """清除匹配模式的所有缓存
        
        Args:
            pattern: 键模式，如 "discover:*"
        """
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.client.delete(*keys)
    
    async def get_stats(self) -> dict:
        """获取Redis统计信息"""
        info = await self.client.info()
        return {
            'used_memory': info.get('used_memory_human', 'N/A'),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
        }


# 创建全局单例
redis_client = RedisClient()
