# 贡献指南

感谢你对 ConceptGraph AI 项目的关注！

## 开发环境搭建

### 后端
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm start
```

## 代码规范

- Python: PEP 8 + Black格式化
- TypeScript: ESLint + Prettier
- 测试覆盖率: 80%+

## 提交规范

使用 Conventional Commits:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档
- `test`: 测试
- `chore`: 构建/工具

示例:
```
feat(agent): 添加知识校验Agent

- 实现多源验证
- 添加可信度评分
```

## Pull Request流程

1. Fork项目
2. 创建功能分支
3. 完成开发和测试
4. 提交PR
5. 代码审查
6. 合并

## 许可证

MIT License
