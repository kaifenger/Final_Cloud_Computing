"""FastAPI主应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .config import settings
from .api import routes
from .database import neo4j_client, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库连接
    print("🚀 启动应用，初始化数据库连接...")
    try:
        await neo4j_client.connect()
        print("✅ Neo4j连接成功")
    except Exception as e:
        print(f"⚠️  Neo4j连接失败: {e}")
    
    try:
        await redis_client.connect()
        print("✅ Redis连接成功")
    except Exception as e:
        print(f"⚠️  Redis连接失败: {e}")
    
    yield
    
    # 关闭时清理资源
    print("🛑 关闭应用，清理资源...")
    await neo4j_client.disconnect()
    await redis_client.disconnect()
    print("✅ 资源清理完成")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="跨学科知识图谱智能体 API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(routes.router, prefix=settings.API_PREFIX)

# 根路径
@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api": settings.API_PREFIX
    }

# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查 - 用于Docker/K8S健康探针"""
    return {"status": "healthy"}

# 就绪检查接口
@app.get("/ready")
async def readiness_check():
    """就绪检查 - 检查依赖服务是否可用"""
    neo4j_ok = await neo4j_client.is_connected()
    redis_ok = await redis_client.is_connected()
    
    if neo4j_ok and redis_ok:
        return {
            "status": "ready",
            "services": {
                "neo4j": "connected",
                "redis": "connected"
            }
        }
    
    return {
        "status": "not ready",
        "services": {
            "neo4j": "connected" if neo4j_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected"
        }
    }, 503


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # 开发模式启用热重载
        log_level="info"
    )
