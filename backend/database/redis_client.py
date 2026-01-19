"""Redis缓存客户端"""
import os
import json
from typing import Optional, Any
from loguru import logger


class RedisClient:
    """Redis缓存客户端（支持Mock模式）"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.client = None
        self.mock_mode = os.getenv("MOCK_DB", "true").lower() == "true"
        self._mock_cache = {}
        
    async def connect(self):
        """连接到Redis"""
        if self.mock_mode:
            logger.info("[MOCK] Redis客户端运行在Mock模式")
            return
            
        try:
            import redis.asyncio as aioredis
            self.client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await self.client.ping()
            logger.info(f"已连接到Redis: {self.host}:{self.port}")
        except ImportError:
            logger.warning("redis包未安装，切换到Mock模式")
            self.mock_mode = True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}，切换到Mock模式")
            self.mock_mode = True
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.close()
            logger.info("已断开Redis连接")
    
    async def is_connected(self) -> bool:
        """检查连接状态"""
        if self.mock_mode:
            return True
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except:
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self.mock_mode:
            value = self._mock_cache.get(key)
            logger.debug(f"[MOCK] GET {key}: {'HIT' if value else 'MISS'}")
            return value
        
        if not self.client:
            return None
        
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        """设置缓存值"""
        if self.mock_mode:
            self._mock_cache[key] = value
            logger.debug(f"[MOCK] SET {key} (ttl={ex}s)")
            return True
        
        if not self.client:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        await self.client.set(key, value, ex=ex)
        return True
    
    async def delete(self, key: str):
        """删除缓存"""
        if self.mock_mode:
            self._mock_cache.pop(key, None)
            logger.debug(f"[MOCK] DEL {key}")
            return True
        
        if not self.client:
            return False
        
        await self.client.delete(key)
        return True
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self.mock_mode:
            return key in self._mock_cache
        
        if not self.client:
            return False
        
        return await self.client.exists(key) > 0


# 全局实例
redis_client = RedisClient()
