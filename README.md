# ConceptGraph AI - 跨学科知识图谱智能体

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **📦 交付说明**: 本项目已包含完整的Dockerfile、依赖配置文件、源码及部署指南 → 详见 [DEPLOYMENT.md](./DEPLOYMENT.md)

## 📖 项目简介

**ConceptGraph AI** 是一个基于大语言模型（LLM）和图数据库的跨学科知识图谱挖掘系统。通过三层缓存架构（Neo4j + Redis + LLM）实现高性能概念关联发现和可视化。

### 核心功能

1. **功能1 - 自动跨学科挖掘**: 输入单个概念，自动发现跨学科关联概念
2. **功能2 - 指定学科挖掘**: 在指定学科范围内挖掘相关概念  
3. **功能3 - 桥接概念发现**: 找到连接多个概念的"桥梁节点"

### 技术亮点

- ✅ **三层缓存架构**: Neo4j（持久化） → Redis（1小时） → LLM（实时生成）
- ✅ **语义相似度排序**: 基于Embedding的智能排序
- ✅ **Wikipedia验证**: 多源验证提升可信度
- ✅ **完整图可视化**: D3.js + Ant Design交互式展示
- ✅ **Docker一键部署**: docker-compose快速启动

---

## 🚀 快速开始（推荐）

### Docker一键启动
```bash
# Windows
start.bat

# Linux/Mac  
chmod +x start.sh && ./start.sh
```

### 访问系统
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474

**完整部署指南**: 见 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📦 交付清单（课程要求）

### ✅ Dockerfile
- `backend/Dockerfile` - 后端Python服务镜像
- `frontend/Dockerfile` - 前端React应用镜像
- `docker-compose.yml` - 完整服务编排配置

### ✅ 依赖配置文件
- `requirements.txt` - Python依赖（FastAPI, Neo4j, Redis, OpenAI等）
- `frontend/package.json` - Node.js依赖（React, Ant Design, D3.js等）

### ✅ 完整源码
```
backend/              # FastAPI后端服务
├── api/              # API路由和业务逻辑
│   ├── routes.py     # 三个核心功能接口
│   ├── multi_function_generator.py
│   └── real_node_generator.py
├── database/         # 数据库客户端
│   ├── neo4j_client.py
│   └── redis_client.py
└── main.py           # 应用入口

frontend/             # React前端应用
├── src/
│   ├── App.tsx       # 主应用组件
│   ├── components/   # UI组件库
│   └── services/     # API服务层

shared/               # 共享数据模型
prompts/              # LLM提示词模板
```

### ✅ 环境配置指南
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - 完整部署指南（**必读**）
- **[NEO4J_USAGE.md](./NEO4J_USAGE.md)** - Neo4j使用说明
- `.env.example` - 环境变量配置模板
- `start.sh` / `start.bat` - 快速启动脚本

---

## 🏗️ 系统架构

```
用户请求
    ↓
AgentOrchestrator（编排器）
    ↓
┌─────────────────────────────────────────┐
│  ConceptDiscoveryAgent（概念挖掘）        │
│  - LLM + CoT推理                        │
│  - 跨学科搜索                            │
│  - 输出：24个候选概念                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  VerificationAgent（知识校验）⭐          │
│  - 多源验证                              │
│  - 可信度评分                            │
│  - 输出：18个验证通过的概念                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  GraphBuilderAgent（图谱构建）            │
│  - 提取节点和边                          │
│  - 生成JSON（nodes + edges）             │
│  - 输出：标准图谱数据                     │
└─────────────────────────────────────────┘
    ↓
返回图谱数据 → Neo4j → 前端可视化
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- OpenRouter API Key（推荐）或 OpenAI API Key
- Docker（可选）

### 安装步骤

```bash
# 1. 克隆仓库
git clone git@github.com:kaifenger/Final_Cloud_Computing.git
cd Final_Cloud_Computing

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API Key和数据库配置：
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
# LLM_MODEL=google/gemini-flash-1.5
# 
# 数据库密码需与Docker启动指令匹配：
# NEO4J_PASSWORD=password（与docker run中的NEO4J_AUTH一致）
# REDIS_PASSWORD=（留空，因为Redis容器未设置密码）
```

### 启动方式

#### 方式一：手动启动（开发环境）

**启动数据库（使用Docker）：**
```bash
# 如果容器已存在，先启动已有容器
docker start redis neo4j

# 如果容器不存在或需要重新创建，执行以下命令：

# 启动Redis（端口6379）
docker run -d --name redis -p 6379:6379 redis:latest

# 启动Neo4j（端口7474浏览器界面, 7687数据库连接）
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 查看容器状态
docker ps

# 访问Neo4j浏览器界面：http://localhost:7474
# 默认用户名: neo4j, 密码: password

# （可选）停止数据库
# docker stop redis neo4j

# （可选）删除容器（需要重新创建时使用）
# docker rm redis neo4j
```

**启动后端：**
```bash
# 安装后端依赖
pip install -r backend/requirements.txt

# 启动后端服务（端口8000）
python start_backend.py
```

**启动前端：**
```bash
# 进入前端目录
cd frontend

# 安装前端依赖
npm install

# 启动前端开发服务器（端口3000）
npm start
```

访问 http://localhost:3000 即可使用系统。

#### 方式二：Docker 启动（生产环境）

**使用 docker-compose（推荐）：**
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**单独使用 Docker：**
```bash
# 构建后端镜像
docker build -t conceptgraph-backend -f backend/Dockerfile .

# 运行后端容器
docker run -d -p 8000:8000 --env-file .env conceptgraph-backend

# 构建前端镜像
docker build -t conceptgraph-frontend -f frontend/Dockerfile ./frontend

# 运行前端容器
docker run -d -p 3000:80 conceptgraph-frontend
```

访问 http://localhost:3000 即可使用系统。

### 基础使用

```python
import asyncio
from agents import get_orchestrator

async def main():
    # 创建编排器
    orchestrator = get_orchestrator()
    
    # 发现跨学科概念
    response = await orchestrator.discover(
        concept="熵",
        disciplines=["数学", "物理", "信息论", "计算机"],
        depth=2,
        max_concepts=20
    )
    
    # 输出结果
    if response.status == "success":
        data = response.data
        print(f"发现 {data.metadata.total_nodes} 个节点")
        print(f"平均可信度: {data.metadata.avg_credibility}")
        
        # 输出节点
        for node in data.nodes:
            print(f"- {node.label} ({node.discipline}): {node.definition}")

# 运行
asyncio.run(main())
```

---

## 📁 项目结构

```
conceptgraph-ai/
├── shared/                     # 共享模块
│   ├── schemas/               # 数据模型（ConceptNode, ConceptEdge）
│   ├── constants.py           # 常量定义（学科、关系类型）
│   ├── error_codes.py         # 错误码
│   └── utils.py               # 工具函数
│
├── agents/                     # Agent核心代码（成员A负责）
│   ├── orchestrator.py        # Agent编排器（主入口）
│   ├── concept_discovery_agent.py   # 概念挖掘Agent
│   ├── verification_agent.py        # 知识校验Agent
│   ├── graph_builder_agent.py       # 图谱构建Agent
│   ├── llm_client.py          # LLM API调用封装
│   ├── utils.py               # Agent工具函数
│   └── config.yaml            # Agent配置
│
├── prompts/                    # Prompt模板库
│   ├── discovery_prompts.py   # 挖掘Prompt（带CoT）
│   ├── verification_prompts.py # 校验Prompt
│   └── graph_prompts.py       # 图谱生成Prompt
│
├── tests/                      # 测试代码
│   ├── test_agents.py         # Agent单元测试
│   └── mock_data.py           # Mock数据
│
├── docs/                       # 文档
│   ├── agent-design.md        # Agent设计文档
│   ├── prompt-templates.md    # Prompt模板说明
│   └── api-agent.md           # Agent API接口文档
│
├── .env.example               # 环境变量模板
├── .gitignore                 # Git忽略文件
└── README.md                  # 项目说明
```

---

## 🔧 核心组件

### 1. ConceptDiscoveryAgent（概念挖掘Agent）

**功能**：在多个学科领域发现与核心概念相关的知识

**特点**：
- Chain-of-Thought推理
- 学科强制覆盖（每个学科至少1个概念）
- 关联强度评分（0-1）

**示例**：
```python
discovery_agent = ConceptDiscoveryAgent()
result = await discovery_agent.discover_concepts(
    concept="熵",
    disciplines=["信息论", "物理", "计算机"]
)
```

### 2. VerificationAgent（知识校验Agent）⭐ 核心创新

**功能**：验证概念关联的准确性，解决大模型幻觉

**验证策略**：
1. 定义核查（Wikipedia、学术定义）
2. 文献支持（学术论文、教科书）
3. 逻辑一致性（检查反例）

**可信度评分**：
- 0.9-1.0：学术界公认
- 0.7-0.9：有论文支持
- 0.5-0.7：依据不充分
- <0.5：过滤

### 3. GraphBuilderAgent（图谱构建Agent）

**功能**：将验证后的概念转换为标准图数据结构

**输出格式**：
```json
{
  "nodes": [{"id": "...", "label": "...", "credibility": 0.95}],
  "edges": [{"source": "...", "target": "...", "weight": 0.92}],
  "metadata": {"total_nodes": 18, "avg_credibility": 0.87}
}
```

---

## 📊 API接口

### 概念挖掘

```bash
POST /api/v1/agent/discover
Content-Type: application/json

{
  "concept": "熵",
  "disciplines": ["数学", "物理", "信息论"],
  "depth": 2,
  "max_concepts": 30
}
```

### 概念验证

```bash
POST /api/v1/agent/verify

{
  "concept_a": "熵",
  "concept_b": "香农熵",
  "claimed_relation": "香农熵是信息论中熵的具体定义"
}
```

### 节点扩展

```bash
POST /api/v1/agent/expand

{
  "node_id": "entropy_xinxilun",
  "max_new_nodes": 10
}
```

详细API文档见：[docs/api-agent.md](docs/api-agent.md)

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/test_agents.py -v

# 运行特定测试
pytest tests/test_agents.py::test_discover_concepts_basic -v

# 查看覆盖率
pytest tests/test_agents.py --cov=agents --cov-report=html
```

---

## 📚 文档

- [Agent设计文档](docs/agent-design.md) - 详细架构和设计思路
- [Prompt模板说明](docs/prompt-templates.md) - CoT推理链和Prompt优化
- [API接口文档](docs/api-agent.md) - 完整API规范

---

## 🛠️ 开发指南

### 分支策略

```bash
main              # 主分支
├── dev-agent     # 成员A开发分支（智能体）
└── dev-infra     # 成员B开发分支（架构）
```

### 提交规范

```bash
feat: 新功能
fix: Bug修复
docs: 文档更新
test: 测试相关

# 示例
git commit -m "feat(agent): 实现概念挖掘Agent"
git commit -m "fix(verification): 修复可信度计算错误"
```

### 代码规范

```bash
# 格式化
black agents/ --line-length 100
isort agents/

# 检查
flake8 agents/
mypy agents/
```

---

## 🔍 技术栈

### 核心技术
- **Python 3.9+** - 主要开发语言
- **Google Gemini 3 Pro** - 大语言模型（via OpenRouter）
- **OpenRouter** - 统一LLM API接口
- **Pydantic** - 数据验证
- **AsyncIO** - 异步编程

### 未来扩展
- **Neo4j** - 图数据库（成员B负责）
- **Milvus** - 向量数据库（成员B负责）
- **Docker + K8S** - 容器化部署（成员B负责）
- **React + D3.js** - 前端可视化（成员B负责）

---

## 🤝 分工说明

### 成员A（智能体与算法组）- 本仓库负责

- ✅ 智能体编排系统（AgentOrchestrator）
- ✅ 三个核心Agent（Discovery, Verification, GraphBuilder）
- ✅ Prompt模板库（CoT推理）
- ✅ LLM API调用封装
- ✅ 共享数据模型和常量

### 成员B（架构与工程组）- 后续开发

- ⏳ 后端API服务（FastAPI）
- ⏳ Neo4j图数据库集成
- ⏳ 前端可视化（React + D3.js）
- ⏳ Docker + K8S部署
- ⏳ 监控和日志

---

## 📈 路线图

### 阶段一：智能体框架 ✅（当前）
- [x] Agent编排器
- [x] 概念挖掘Agent
- [x] 知识校验Agent
- [x] 图谱构建Agent
- [x] Prompt模板库

### 阶段二：关联挖掘算法（下一步）
- [ ] 语义相似度计算
- [ ] 学科分类器
- [ ] 数据抓取器（Wikipedia/Arxiv）
- [ ] 可信度评分算法

### 阶段三：后端集成
- [ ] FastAPI服务
- [ ] Neo4j集成
- [ ] WebSocket实时推送

### 阶段四：前端与部署
- [ ] React可视化
- [ ] Docker部署
- [ ] K8S编排

---

## 📝 许可证

MIT License

---

## 👥 贡献者

- **成员A**（智能体组）- 负责Agent系统和算法
- **成员B**（架构组）- 负责后端、前端和云原生部署

---

## 📧 联系方式

- **GitHub**: [kaifenger/Final_Cloud_Computing](https://github.com/kaifenger/Final_Cloud_Computing)
- **Issue**: 提交问题和建议

---

**ConceptGraph AI** - 用智能体连接知识的孤岛 🌉
