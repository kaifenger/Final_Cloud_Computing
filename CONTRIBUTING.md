# 贡献指南

感谢你对 ConceptGraph AI 项目的关注！

## 开发环境搭建

### 后端
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动后端服务
cd backend
uvicorn main:app --reload --port 8888
```

### 前端
```bash
cd frontend
npm install

# 解决内存溢出问题（如需要）
# Windows:
set NODE_OPTIONS=--max-old-space-size=4096

# 启动开发服务器
npm start
```

## 代码规范

- **Python**: PEP 8 + Black格式化
- **TypeScript**: ESLint + Prettier
- **测试覆盖率**: 目标 80%+

### 代码格式化
```bash
# Python
black agents/ backend/ --line-length 100
isort agents/ backend/

# TypeScript
cd frontend && npm run lint
```

## 提交规范

使用 Conventional Commits:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具
- `refactor`: 代码重构

示例:
```
feat(agent): 添加知识校验Agent

- 实现多源验证（Wikipedia + Arxiv）
- 添加可信度评分算法
- 支持定义截断（≤500字）
```

## Pull Request流程

1. Fork项目
2. 创建功能分支 (`git checkout -b feat/my-feature`)
3. 完成开发和测试
4. 确保代码格式正确
5. 提交PR并描述改动
6. 等待代码审查
7. 合并到主分支

## 项目结构说明

```
conceptgraph-ai/
├── agents/           # 智能体核心（概念挖掘、验证、图谱构建）
├── algorithms/       # 算法模块（数据抓取、相似度计算）
├── backend/          # FastAPI后端服务
├── frontend/         # React前端应用
├── shared/           # 共享模块（数据模型、常量）
├── prompts/          # Prompt模板库
├── tests/            # 测试代码
└── docs/             # 文档
```

## 核心功能清单

- [x] 概念定义截断（≤500字）
- [x] 来源标签显示（Wikipedia/LLM/Arxiv）
- [x] 节点展开功能
- [x] 边有效性验证
- [x] 错误处理与日志
- [ ] WebSocket实时推送
- [ ] Neo4j完整集成
- [ ] Docker部署脚本

## 许可证

MIT License
