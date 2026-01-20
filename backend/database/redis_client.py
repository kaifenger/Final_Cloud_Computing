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
    
    async def clear_pattern(self, pattern: str = "*"):
        """清除匹配模式的缓存"""
        if self.mock_mode:
            if pattern == "*":
                self._mock_cache.clear()
            else:
                # 简单的模式匹配
                prefix = pattern.replace("*", "")
                keys_to_delete = [k for k in self._mock_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self._mock_cache[key]
            logger.debug(f"[MOCK] CLEAR pattern={pattern}")
            return True
        
        if not self.client:
            return False
        
        cursor = 0
        while True:
            cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
            if keys:
                await self.client.delete(*keys)
            if cursor == 0:
                break
        return True
    
    async def get_stats(self) -> dict:
        """获取缓存统计信息"""
        if self.mock_mode:
            return {
                "mode": "mock",
                "keys_count": len(self._mock_cache),
                "memory_usage": "N/A"
            }
        
        if not self.client:
            return {"mode": "disconnected"}
        
        try:
            info = await self.client.info("memory")
            return {
                "mode": "redis",
                "memory_usage": info.get("used_memory_human", "N/A"),
                "keys_count": await self.client.dbsize()
            }
        except Exception as e:
            return {"mode": "error", "error": str(e)}


# 全局实例
redis_client = RedisClient()
