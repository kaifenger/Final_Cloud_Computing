# API参考文档

## 核心接口

### 1. 概念挖掘

**URL**: `POST /api/v1/discover`

**请求体**:
```json
{
  "concept": "熵",
  "disciplines": ["数学", "物理", "信息论"],
  "depth": 2
}
```

**响应**:
```json
{
  "status": "success",
  "request_id": "req_123456",
  "data": {
    "nodes": [...],
    "edges": [...],
    "metadata": {...}
  }
}
```

（待完善）
