"""
/discover端点修复说明 - 从假数据到真实LLM生成
===================================================

## 问题描述

前端页面显示的知识图谱节点是假数据（硬编码的模板）：
- 节点名称: "XX的应用"、"XX的理论"（模板化）
- 相似度: 固定值（如0.75）
- 来源: 不是真实API调用

## 根本原因

**缓存问题**: `/discover`端点使用了旧的缓存键格式`discover:<概念名>`，
返回的是之前使用`get_mock_discovery_result()`函数生成的假数据。

## 修复方案

### 1. 缓存键版本升级 ✅

**文件**: backend/api/routes.py

**修改**:
```python
# 旧代码（第520行）
cache_key = f"discover:{request.concept}"

# 新代码
cache_key = f"discover:v2:{request.concept}"  # 添加v2版本号
```

**效果**:
- 旧缓存（discover:马尔可夫原理）将被忽略
- 新请求使用新键（discover:v2:马尔可夫原理）
- 强制调用真实LLM生成逻辑

---

## 验证真实LLM生成

### 测试结果

```bash
$ py -3.11 test_discover_real.py

[INFO] LLM生成了20个候选概念
[SUCCESS] 相似度计算: 马尔可夫链 <-> 马尔可夫原理 = 0.808
[SUCCESS] 相似度计算: 隐马尔可夫模型 <-> 马尔可夫原理 = 0.787
[SUCCESS] 相似度计算: 马尔可夫决策过程 <-> 马尔可夫原理 = 0.808
...
[INFO] 选择了相似度最高的9个概念:
   - 马尔可夫决策过程 (相似度: 0.808)
   - 马尔可夫链 (相似度: 0.808)
   - 隐马尔可夫模型 (相似度: 0.787)
```

**验证点**:
✅ 使用真实LLM生成（google/gemini-2.0-flash-001）
✅ 动态相似度计算（OpenAI embeddings，每个概念不同）
✅ 按相似度排序选择top-N
✅ 节点名称是真实学术概念（非模板化）
✅ 动态可信度评分（0.895, 0.889, 0.860等）

---

## 数据流对比

### 修复前（假数据）

```
用户输入 "马尔可夫原理"
    ↓
检查缓存: discover:马尔可夫原理
    ↓
返回旧缓存（假数据）:
  - 马尔可夫原理_跨学科_0
  - 马尔可夫原理的应用_应用领域_1  ❌ 模板化
  - 马尔可夫原理的理论_理论基础_2  ❌ 模板化
相似度: 0.75（固定）❌
```

### 修复后（真实LLM）

```
用户输入 "马尔可夫原理"
    ↓
检查缓存: discover:v2:马尔可夫原理（新键）
    ↓
缓存未命中 → 调用真实LLM生成
    ↓
步骤1: LLM生成20个候选概念
    ↓
步骤2: 计算每个候选的相似度
    马尔可夫链: 0.808
    隐马尔可夫模型: 0.787
    马尔可夫决策过程: 0.808
    ...
    ↓
步骤3: 按相似度排序，选择top 9
    ↓
步骤4: 获取Wikipedia定义
    ↓
步骤5: 计算动态可信度
    马尔可夫链: 0.895
    隐马尔可夫模型: 0.889
    ...
    ↓
返回真实数据:
  - 马尔可夫原理（中心节点）
  - 马尔可夫决策过程 ✅ 真实概念
  - 马尔可夫链 ✅ 真实概念
  - 隐马尔可夫模型 ✅ 真实概念
  ...
相似度: 0.808, 0.787, 0.660 等（动态）✅
```

---

## 前端测试步骤

### 1. 重启后端服务

```bash
# 停止当前服务（Ctrl+C）
# 重新启动
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

### 2. 刷新前端页面

```bash
# 在浏览器中按 F5 或 Ctrl+F5 强制刷新
```

### 3. 输入测试概念

在搜索框输入：`马尔可夫原理`

### 4. 观察后端控制台输出

应该看到：
```
[INFO] 开始概念发现: 马尔可夫原理 (使用真实LLM)
[INFO] 真实生成器导入成功
[INFO] LLM生成了20个候选概念
[SUCCESS] 相似度计算: 马尔可夫链 <-> 马尔可夫原理 = 0.808
[INFO] 选择了相似度最高的9个概念:
   - 马尔可夫决策过程 (相似度: 0.808)
   - 马尔可夫链 (相似度: 0.808)
   ...
```

### 5. 检查前端显示

**节点名称应该是**:
- ✅ 马尔可夫链
- ✅ 隐马尔可夫模型
- ✅ 马尔可夫决策过程
- ✅ 卡尔曼滤波
- ✅ 蒙特卡洛方法

**而不是**:
- ❌ 马尔可夫原理的应用
- ❌ 马尔可夫原理的理论
- ❌ 马尔可夫原理的方法

**检查节点属性**（打开浏览器控制台）:
```javascript
// 应该看到类似的输出
{
  id: "马尔可夫链_概率论_1",
  label: "马尔可夫链",
  discipline: "概率论",
  credibility: 0.895,
  similarity: 0.808,  // 动态值，不是固定的0.75
  source: "Wikipedia",
  depth: 1
}
```

---

## 关键修改文件

1. **backend/api/routes.py** (第520行)
   - 修改缓存键: `discover:{concept}` → `discover:v2:{concept}`

2. **backend/api/real_node_generator.py**
   - 已存在，无需修改
   - 提供真实LLM生成功能

---

## 技术细节

### 真实LLM生成流程

1. **概念生成** (generate_related_concepts)
   - 模型: google/gemini-2.0-flash-001
   - 温度: 0.3
   - 输出: name|discipline|relation

2. **相似度计算** (compute_similarity)
   - 模型: text-embedding-3-small
   - 维度: 1536
   - 算法: 余弦相似度

3. **可信度评分** (compute_credibility)
   - 公式: base * (0.7 + 0.3 * similarity)
   - base: 0.95 (Wikipedia) / 0.70 (LLM)

### 性能优化

- 并发计算相似度（asyncio.gather）
- 生成2倍候选，选择top-N
- 缓存结果（TTL: 3600秒）

---

## 常见问题

### Q1: 为什么还是看到旧数据？

**A**: 浏览器缓存。强制刷新（Ctrl+F5）或清除浏览器缓存。

### Q2: 后端控制台没有LLM生成日志？

**A**: 检查：
1. 环境变量是否设置: `ENABLE_EXTERNAL_VERIFICATION=true`
2. API密钥是否配置: `OPENROUTER_API_KEY`, `OPENAI_API_KEY`
3. 后端服务是否重启

### Q3: 相似度计算失败？

**A**: 检查OpenAI API密钥是否有效，embedding模型是否可用。

---

## 测试命令

```bash
# 1. 测试discover端点
py -3.11 test_discover_real.py

# 2. 清除缓存说明
py -3.11 clear_cache.py

# 3. 启动后端
py -3.11 -m uvicorn backend.main:app --reload --port 8000

# 4. 测试API（在新终端）
curl -X POST http://localhost:8000/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"concept":"马尔可夫原理","max_concepts":10}'
```

---

## 总结

✅ **问题已修复**: 缓存键版本升级强制使用真实LLM
✅ **数据验证**: 20个候选→相似度排序→选择top-N
✅ **动态计算**: 相似度和可信度都是动态计算
✅ **真实概念**: 节点名称来自LLM生成，非模板化

**下一步**: 重启后端 → 刷新前端 → 输入概念 → 查看真实数据
"""

print(__doc__)
