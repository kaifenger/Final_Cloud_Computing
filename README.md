# ConceptGraph AI - 跨学科知识图谱智能体

## 项目概述

**ConceptGraph AI** 是一个基于云原生架构和大模型智能体的跨学科知识图谱系统，能够自动挖掘不同学科间的深层联系并可视化展示。

### 核心功能
- 🔍 **智能关联挖掘**：在6个学科领域自动发现概念关联
- ✅ **知识校验层**：多源验证避免大模型幻觉
- 🌐 **交互式图谱**：基于D3.js的动态可视化
- ☁️ **云原生部署**：Docker + K8S + Redis + Neo4j

---

## 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+
- Node.js 18+

### 一键启动（推荐）

```bash
# 克隆仓库
git clone git@github.com:kaifenger/Final_Cloud_Computing.git
cd Final_Cloud_Computing

# 配置环境变量
cp .env.example .env
# 编辑.env，填入必要的API密钥

# 启动所有服务
cd infrastructure/docker
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 访问服务

- **前端**: http://localhost:3000
- **后端API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474 (用户名: neo4j, 密码: password)
- **Redis**: localhost:6379
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (用户名: admin, 密码: admin)

---

## 项目结构

```
conceptgraph-ai/
├── backend/                 # 后端API服务（成员B）
├── frontend/                # 前端可视化（成员B）
├── agents/                  # 智能体模块（成员A）
├── prompts/                 # Prompt模板（成员A）
├── algorithms/              # 算法实现（成员A）
├── shared/                  # 共享代码
├── infrastructure/          # 云原生配置（成员B）
│   ├── docker/             # Docker配置
│   └── k8s/                # Kubernetes配置
├── docs/                    # 技术文档
├── tests/                   # 测试代码
└── .github/                # CI/CD配置
```

---

## 技术栈

### 云原生组件
- **Docker**: 容器化部署
- **Kubernetes**: 服务编排、自动扩缩容
- **Redis**: 分布式缓存
- **MinIO**: 对象存储
- **Prometheus + Grafana**: 监控和可视化

### 后端技术
- **FastAPI**: 高性能异步框架
- **Neo4j**: 图数据库
- **Milvus**: 向量数据库
- **WebSocket**: 实时通信

### 前端技术
- **React 18**: 前端框架
- **D3.js**: 图谱可视化
- **TypeScript**: 类型安全
- **Ant Design**: UI组件库

### 智能体技术
- **LangChain**: Agent框架
- **OpenAI GPT-4**: 大语言模型
- **Sentence-Transformers**: 向量化

---

## 本地开发

### 后端开发

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend
npm install
npm start
```

### Agent开发

```bash
cd agents
pip install -r requirements.txt
python orchestrator.py
```

---

## Kubernetes部署

### 前置条件
- Kubernetes集群（Minikube/Kind/云服务商）
- kubectl命令行工具

### 部署步骤

```bash
# 创建命名空间
kubectl create namespace conceptgraph

# 应用配置
kubectl apply -f infrastructure/k8s/configmap.yaml
kubectl apply -f infrastructure/k8s/secrets.yaml

# 部署数据库
kubectl apply -f infrastructure/k8s/deployments/neo4j-deployment.yaml
kubectl apply -f infrastructure/k8s/deployments/redis-deployment.yaml

# 部署应用服务
kubectl apply -f infrastructure/k8s/deployments/backend-deployment.yaml
kubectl apply -f infrastructure/k8s/deployments/frontend-deployment.yaml

# 部署Service
kubectl apply -f infrastructure/k8s/services/

# 部署Ingress
kubectl apply -f infrastructure/k8s/ingress.yaml

# 检查状态
kubectl get pods -n conceptgraph
kubectl get services -n conceptgraph
```

---

## 环境变量配置

复制 `.env.example` 为 `.env` 并配置以下关键变量：

```bash
# LLM配置（成员A负责）
OPENAI_API_KEY=your-api-key-here

# 数据库配置（成员B负责）
NEO4J_PASSWORD=your-password
```

---

## API文档

启动后端服务后访问 http://localhost:8000/docs 查看完整API文档。

### 核心接口

#### 1. 概念挖掘
```bash
POST /api/v1/discover
Content-Type: application/json

{
  "concept": "熵",
  "disciplines": ["数学", "物理", "信息论"],
  "depth": 2
}
```

#### 2. 图谱查询
```bash
GET /api/v1/graph/{concept_id}
```

---

## 测试

```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd frontend
npm test

# Agent测试
cd agents
pytest tests/
```

---

## 团队分工

- **成员A**：智能体设计、算法开发、Prompt工程（50%）
- **成员B**：云原生架构、后端服务、前端开发、DevOps（50%）

详细分工请查看 [命题三-实现方案与分工.md](命题三-实现方案与分工.md)

---

## 常见问题

### Q1: Docker启动失败？
检查端口占用：
```bash
docker-compose down
docker-compose up -d
```

### Q2: Neo4j连接失败？
确认配置正确：
```bash
docker-compose logs neo4j
```

### Q3: 前端无法访问后端？
检查CORS配置和网络连接。

---

## 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 演示视频

[点击观看演示视频](docs/demo-video.md)

---

## License

MIT License

---

## 联系方式

- 项目Issue: https://github.com/kaifenger/Final_Cloud_Computing/issues
- 文档: [docs/](docs/)

---

**开发中...** 🚀
