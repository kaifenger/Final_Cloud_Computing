# 部署文档

## Docker部署

### 前置条件
- Docker 20.10+
- Docker Compose 2.0+

### 部署步骤

1. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件
```

2. 启动服务
```bash
cd infrastructure/docker
docker-compose up -d
```

3. 查看日志
```bash
docker-compose logs -f
```

## Kubernetes部署

### 前置条件
- Kubernetes集群
- kubectl工具

### 部署步骤

```bash
kubectl apply -f infrastructure/k8s/
```

（待完善）
