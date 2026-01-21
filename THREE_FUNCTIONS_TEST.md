# 三功能测试指南

## 前端界面使用说明

### 功能1：自动跨学科发现 🔍
**使用方法：**
1. 点击"🔍 自动跨学科"按钮
2. 在输入框输入概念（如：朴素贝叶斯）
3. 点击"搜索"
4. 系统自动生成20个跨学科相关概念，通过语义相似度筛选出最相关的3-9个

**API端点：** `POST /api/v1/discover`

**测试用例：**
- 朴素贝叶斯
- 神经网络
- 量子纠缠
- 熵

---

### 功能2：限定学科发现 🎯
**使用方法：**
1. 点击"🎯 限定学科"按钮
2. 选择目标学科（可多选）：
   - 计算机科学
   - 物理学
   - 数学
   - 生物学
   - 心理学
   - 经济学
   - 社会学
3. 输入概念
4. 点击"搜索"
5. 系统只在选定的学科中搜索相关概念

**API端点：** `POST /api/v1/discover/disciplined`

**测试用例：**
- 概念：机器学习
  - 选择学科：计算机科学、数学
- 概念：熵
  - 选择学科：物理学、信息论

---

### 功能3：桥接概念发现 🌉
**使用方法：**
1. 点击"🌉 桥接发现"按钮
2. 输入至少2个概念（每行一个）
3. 可点击"+ 添加概念"增加更多概念
4. 点击"发现桥接概念"
5. 系统自动找出连接这些概念的桥梁概念

**API端点：** `POST /api/v1/discover/bridge`

**测试用例：**
- 概念组1：神经网络、生物神经元
- 概念组2：PageRank、马尔可夫链
- 概念组3：遗传算法、达尔文进化论

---

## 后端测试命令

### 测试功能1
```bash
curl -X POST http://localhost:8888/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"concept": "朴素贝叶斯", "max_concepts": 5}'
```

### 测试功能2
```bash
curl -X POST http://localhost:8888/api/v1/discover/disciplined \
  -H "Content-Type: application/json" \
  -d '{"concept": "机器学习", "disciplines": ["计算机科学", "数学"], "max_concepts": 10}'
```

### 测试功能3
```bash
curl -X POST http://localhost:8888/api/v1/discover/bridge \
  -H "Content-Type: application/json" \
  -d '{"concepts": ["神经网络", "生物神经元"], "max_bridges": 5}'
```

---

## 预期输出

所有三个功能都返回相同的数据结构：

```json
{
  "status": "success",
  "request_id": "req_xxx",
  "data": {
    "nodes": [
      {
        "id": "node_id",
        "label": "概念名称",
        "discipline": "学科",
        "definition": "维基定义",
        "brief_summary": "AI生成的简介",
        "similarity": 0.665,
        "credibility": 0.855,
        "source": "Wikipedia",
        "wiki_url": "https://..."
      }
    ],
    "edges": [
      {
        "source": "node1_id",
        "target": "node2_id",
        "relation": "related_to",
        "weight": 0.8,
        "reasoning": "关联原因"
      }
    ],
    "metadata": {
      "total_nodes": 10,
      "total_edges": 9,
      "avg_similarity": 0.625
    }
  }
}
```

---

## 故障排查

### 1. 热重载导致请求中断
**现象：** 修改代码后服务器自动重启，正在进行的请求失败

**解决方案：**
- 已在 `backend/main.py` 中配置 `reload_excludes` 排除测试文件
- 如仍频繁重载，可临时禁用：将 `reload=True` 改为 `reload=False`

### 2. 相似度计算失败
**现象：** `[RETRY] 网络错误，重试...`

**解决方案：**
- 检查 OPENAI_API_KEY 是否配置
- 运行测试：`py -3.11 test_openai_connection.py`
- 已添加自动重试机制（最多1次）

### 3. 简介显示不完整
**现象：** 显示 "*Draft 2:* 布鲁姆..."

**解决方案：**
- 已添加清理逻辑，自动移除 Draft 标记和星号
- 重启后端服务生效

---

## 启动服务

### 后端
```bash
cd backend
py -3.11 main.py
```

### 前端
```bash
cd frontend
npm start
```

访问：http://localhost:3000

---

## 修复内容总结

### 热重载问题
- ✅ 配置 `reload_excludes` 排除不必要的文件监控
- ✅ 避免测试文件修改触发重载

### 重复相似度计算
- ✅ `compute_credibility` 添加 `similarity` 可选参数
- ✅ 功能1和功能2传入已计算的相似度值
- ✅ 减少约50%的API调用

### 简介清理
- ✅ 移除 Draft 标记
- ✅ 移除星号和不必要的标点
- ✅ 确保显示完整干净的简介

### 前端功能
- ✅ 添加三功能模式切换按钮
- ✅ 功能2：学科多选标签
- ✅ 功能3：多概念输入框
- ✅ API 服务封装
