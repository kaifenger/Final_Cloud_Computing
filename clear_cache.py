"""清除旧的Redis缓存，强制使用新的LLM生成逻辑"""
import asyncio
import os

async def clear_old_cache():
    print("=" * 80)
    print("清除旧的discover缓存")
    print("=" * 80)
    
    try:
        from backend.database.redis_client import redis_client
        
        print("\n[检查Redis连接]")
        # 尝试获取一个测试键
        test = await redis_client.get("test_key")
        print("  Redis连接: OK")
        
        # 注意：MockClient没有真正的Redis，所以这只是演示
        print("\n[说明]")
        print("  旧缓存键格式: discover:<概念名>")
        print("  新缓存键格式: discover:v2:<概念名>")
        print("  ")
        print("  由于缓存键格式已更新（添加了v2版本号），")
        print("  旧的缓存数据将被自动忽略。")
        print("  ")
        print("  下次访问 /discover 端点时，将自动使用新的LLM生成逻辑。")
        
        print("\n[手动清除方法（如果需要）]")
        print("  1. 重启Redis服务")
        print("  2. 或使用Redis CLI: redis-cli FLUSHDB")
        print("  3. 或等待TTL过期（3600秒/1小时）")
        
    except Exception as e:
        print(f"[INFO] Redis客户端不可用（使用MockClient）: {e}")
        print("\n[说明]")
        print("  当前使用MockClient，没有真实的Redis缓存。")
        print("  每次请求都会调用真实的LLM生成逻辑。")
    
    print("\n" + "=" * 80)
    print("[下一步]")
    print("  1. 重启后端服务: py -3.11 -m uvicorn backend.main:app --reload")
    print("  2. 刷新前端页面")
    print("  3. 输入概念测试（如：马尔可夫原理）")
    print("  4. 观察控制台输出，应该看到:")
    print("     - [INFO] LLM生成了XX个候选概念")
    print("     - [SUCCESS] 相似度计算: XXX <-> XXX = 0.XXX")
    print("     - [INFO] 选择了相似度最高的X个概念")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(clear_old_cache())
