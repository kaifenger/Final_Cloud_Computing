# 跨学科知识图谱系统 - 环境配置与部署指南

## 📋 项目概述

本项目是一个基于LLM和图数据库的跨学科知识图谱挖掘系统，支持：
- 功能1：自动跨学科概念挖掘
- 功能2：指定学科的概念挖掘
- 功能3：多概念桥接发现

## 🏗️ 系统架构

```
├── backend/          # FastAPI后端服务
├── frontend/         # React前端应用
├── neo4j             # 图数据库（持久化存储）
├── redis             # 缓存数据库（临时缓存）
└── docker-compose.yml # Docker编排文件
```

**技术栈：**
- 后端：Python 3.11 + FastAPI + Neo4j + Redis
- 前端：React 18 + TypeScript + Ant Design
- LLM：OpenRouter API (Google Gemini Flash)
- 部署：Docker + Docker Compose

---

## 🚀 快速开始（Docker部署 - 推荐）

### 前提条件
- Docker Desktop 已安装
- Docker Compose 已安装
- 至少 4GB 可用内存

### 1. 克隆项目
```bash
git clone https://github.com/kaifenger/Final_Cloud_Computing.git
cd Final_Cloud_Computing
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的OpenRouter API密钥
# Windows: notepad .env
# Linux/Mac: nano .env
```

**.env 文件内容：**
```env
OPENROUTER_API_KEY=your-openrouter-api-key-here
LLM_MODEL=google/gemini-flash-1.5
```

### 3. 启动所有服务
```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问系统
- **前端界面**: http://localhost:3000
- **后端API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474 (用户名: neo4j, 密码: conceptgraph123)

### 5. 停止服务
```bash
# 停止所有服务（保留数据）
docker-compose down

# 停止并删除数据（完全清理）
docker-compose down -v
```

---

## 💻 本地开发部署（无Docker）

### 前提条件
- Python 3.11+
- Node.js 18+
- Neo4j 5.15+
- Redis 7.2+

### 1. 启动数据库

#### Neo4j
```bash
# Docker方式
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15.0

# 或下载安装包：https://neo4j.com/download/
```

#### Redis
```bash
# Docker方式
docker run -d --name redis -p 6379:6379 redis:7.2-alpine

# 或使用包管理器安装
```

### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动后端（端口8000）
uvicorn main:app --reload --port 8000
```

**后端环境变量配置：**
```env
# .env 文件
MOCK_DB=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=conceptgraph
REDIS_HOST=localhost
REDIS_PORT=6379
OPENROUTER_API_KEY=your-api-key
LLM_MODEL=google/gemini-flash-1.5
```

### 3. 配置前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（端口3000）
npm start
```

**前端环境变量：**
```env
# frontend/.env
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 📦 依赖配置文件说明

### 后端依赖 (requirements.txt)
```
fastapi==0.109.0          # Web框架
uvicorn[standard]==0.27.0 # ASGI服务器
neo4j==5.15.0             # Neo4j数据库客户端
redis==5.0.1              # Redis客户端
openai>=1.6.1             # OpenAI API客户端
httpx==0.26.0             # 异步HTTP客户端
loguru==0.7.2             # 日志库
pydantic==2.5.3           # 数据验证
python-dotenv==1.0.0      # 环境变量管理
```

完整依赖见 `requirements.txt`

### 前端依赖 (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "antd": "^5.12.0",
    "d3": "^7.8.5",
    "axios": "^1.6.0",
    "typescript": "^4.9.5"
  }
}
```

---

## 🔧 Dockerfile说明

### 后端Dockerfile
位置: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端Dockerfile
位置: `frontend/Dockerfile`

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 🗄️ 数据库配置

### Neo4j配置
- **默认端口**: 7474 (HTTP), 7687 (Bolt)
- **默认密码**: 
  - Docker环境: conceptgraph123
  - 本地开发: password
- **数据库名**: conceptgraph
- **内存配置**: 2GB heap

### Redis配置
- **默认端口**: 6379
- **默认密码**: 
  - Docker环境: conceptgraph123
  - 本地开发: 无密码
- **持久化**: AOF模式

---

## 🔑 API密钥获取

### OpenRouter API
1. 访问 https://openrouter.ai/
2. 注册账号
3. 进入 Settings → API Keys
4. 创建新密钥
5. 将密钥填入 `.env` 文件的 `OPENROUTER_API_KEY`

**推荐模型：**
- `google/gemini-flash-1.5` - 快速且便宜
- `google/gemini-pro-1.5` - 更强大但稍贵
- `anthropic/claude-3-haiku` - 备选方案

---

## 🧪 功能测试

### 1. 测试功能1（自动跨学科挖掘）
```bash
curl -X POST "http://localhost:8000/api/v1/discover" \
  -H "Content-Type: application/json" \
  -d '{
    "concept": "熵",
    "depth": 2,
    "max_concepts": 10
  }'
```

### 2. 测试功能2（指定学科挖掘）
```bash
curl -X POST "http://localhost:8000/api/v1/discover/disciplined" \
  -H "Content-Type: application/json" \
  -d '{
    "concept": "神经网络",
    "disciplines": ["生物学", "计算机科学"]
  }'
```

### 3. 测试功能3（桥接概念发现）
```bash
curl -X POST "http://localhost:8000/api/v1/discover/bridge" \
  -H "Content-Type: application/json" \
  -d '{
    "concepts": ["熵", "最小二乘法"],
    "max_bridges": 5
  }'
```

### 4. 验证数据持久化
```bash
# 进入Neo4j容器
docker exec -it conceptgraph-neo4j cypher-shell -u neo4j -p conceptgraph123

# 查询概念数量
MATCH (c:Concept) RETURN count(c);

# 查询所有概念标签
MATCH (c:Concept) RETURN c.label, c.discipline LIMIT 10;

# 退出
:exit
```

---

## 🐛 故障排查

### 问题1：后端无法连接数据库
**错误**: `Neo4j连接失败` 或 `Redis连接失败`

**解决方案**:
```bash
# 检查容器状态
docker ps

# 查看Neo4j日志
docker logs conceptgraph-neo4j

# 查看Redis日志
docker logs conceptgraph-redis

# 重启数据库容器
docker-compose restart neo4j redis
```

### 问题2：LLM调用失败
**错误**: `LLM生成失败` 或 `API密钥无效`

**解决方案**:
1. 检查 `.env` 文件中的 `OPENROUTER_API_KEY`
2. 验证API密钥: https://openrouter.ai/settings/keys
3. 检查账户余额
4. 查看后端日志: `docker-compose logs backend`

### 问题3：前端无法访问后端
**错误**: `Network Error` 或 `Failed to fetch`

**解决方案**:
1. 确认后端已启动: http://localhost:8000/docs
2. 检查前端环境变量 `REACT_APP_API_BASE_URL`
3. 检查浏览器控制台错误信息
4. 清除浏览器缓存并刷新

### 问题4：Docker构建失败
**错误**: `Error building image`

**解决方案**:
```bash
# 清理Docker缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache

# 重启Docker Desktop
```

---

## 📊 性能优化

### 三层缓存架构
1. **Neo4j** (第一优先级): 持久化存储，永久保存
2. **Redis** (第二优先级): 临时缓存，1小时TTL
3. **LLM** (第三优先级): 实时生成，10-30秒

**查询流程**:
```
用户请求 → Neo4j查询 (0.1秒)
  ↓ 未命中
Redis查询 (0.05秒)
  ↓ 未命中
LLM生成 (15秒) → 保存到Neo4j + Redis → 返回
```

### 清除缓存
```bash
# 清除Redis所有缓存
curl -X DELETE "http://localhost:8000/api/v1/cache/clear"

# 清除特定功能缓存
curl -X DELETE "http://localhost:8000/api/v1/cache/clear?pattern=discover:v2:*"

# 清除Neo4j数据
docker exec -it conceptgraph-neo4j cypher-shell -u neo4j -p conceptgraph123
MATCH (n) DETACH DELETE n;
```

---

## 📁 项目结构

```
.
├── backend/                # 后端服务
│   ├── api/               # API路由
│   │   ├── routes.py      # 主路由文件
│   │   ├── multi_function_generator.py
│   │   └── real_node_generator.py
│   ├── database/          # 数据库客户端
│   │   ├── neo4j_client.py
│   │   └── redis_client.py
│   ├── main.py            # FastAPI入口
│   ├── requirements.txt   # Python依赖
│   ├── Dockerfile         # 后端Docker配置
│   └── .dockerignore
│
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── App.tsx        # 主组件
│   │   ├── components/    # 子组件
│   │   └── services/      # API服务
│   ├── package.json       # Node依赖
│   ├── Dockerfile         # 前端Docker配置
│   └── .dockerignore
│
├── docker-compose.yml     # Docker编排文件
├── .env.example           # 环境变量模板
├── README.md              # 项目说明
├── DEPLOYMENT.md          # 本文档
└── NEO4J_USAGE.md         # Neo4j使用说明
```

---

## 🔐 安全注意事项

1. **不要提交 .env 文件到Git**
   - 已添加到 `.gitignore`
   - 使用 `.env.example` 作为模板

2. **生产环境建议**
   - 修改默认数据库密码
   - 启用HTTPS
   - 配置防火墙规则
   - 限制API访问频率

3. **API密钥管理**
   - 定期轮换密钥
   - 使用环境变量，不要硬编码
   - 监控API使用量和费用

---

## 📞 技术支持

- **项目仓库**: https://github.com/kaifenger/Final_Cloud_Computing
- **Issue跟踪**: https://github.com/kaifenger/Final_Cloud_Computing/issues
- **文档**: 
  - [README.md](./README.md) - 项目介绍
  - [NEO4J_USAGE.md](./NEO4J_USAGE.md) - Neo4j详细说明
  - [DEPLOYMENT.md](./DEPLOYMENT.md) - 本文档

---

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

---

## 🎯 交付清单

- ✅ **Dockerfile**: 
  - `backend/Dockerfile` - 后端服务镜像
  - `frontend/Dockerfile` - 前端服务镜像
  
- ✅ **依赖配置文件**: 
  - `requirements.txt` - Python后端依赖
  - `frontend/package.json` - Node.js前端依赖
  - `docker-compose.yml` - Docker编排配置
  
- ✅ **完整源码**: 
  - `backend/` - 后端完整代码
  - `frontend/` - 前端完整代码
  - `shared/` - 共享模块
  
- ✅ **环境配置指南**: 
  - 本文档 (DEPLOYMENT.md)
  - README.md
  - NEO4J_USAGE.md
  - .env.example

---

**最后更新**: 2026年1月22日
**版本**: v1.0.0
