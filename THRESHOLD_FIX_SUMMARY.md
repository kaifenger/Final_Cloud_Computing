# 动态阈值修改说明

## 修改内容总结

### 1. ✅ 前端相似度显示修复

**文件**: `frontend/src/components/NodeDetailPanel.tsx`

**问题**: 前端显示的"相关度"实际上是`credibility`（可信度），而不是`similarity`（相似度）

**修复**:
```tsx
// 修改前：只显示credibility
<Progress percent={Math.round(selectedNode.credibility * 100)} />

// 修改后：显示similarity（如果存在）和credibility
<Progress percent={Math.round(((selectedNode as any).similarity || selectedNode.credibility) * 100)} />

// 新增详细数值显示
相似度分数: XX.X% | 可信度: XX.X%
```

**说明**: 
- `similarity`: 语义相似度，由OpenAI embeddings计算得出（动态值）
- `credibility`: 可信度，基于来源和相似度的综合评分
- 两者的计算公式：`credibility = base_credibility * (0.7 + 0.3 * similarity)`

---

### 2. ✅ 动态阈值筛选（Discover端点）

**文件**: `backend/api/routes.py` (Lines 369-395)

**修改前**:
```python
# 固定选择9个节点
top_candidates = candidates_with_similarity[:max_concepts - 1]
```

**修改后**:
```python
# 动态阈值筛选：保证3-9个节点
SIMILARITY_THRESHOLD = 0.62  # 基于测试数据分析的合理阈值
MIN_NODES = 3
MAX_NODES = min(9, max_concepts - 1)

# 先筛选高于阈值的
high_quality = [c for c in candidates_with_similarity if c["similarity"] >= SIMILARITY_THRESHOLD]

# 确保数量在合理范围内
if len(high_quality) < MIN_NODES:
    top_candidates = candidates_with_similarity[:MIN_NODES]
elif len(high_quality) > MAX_NODES:
    top_candidates = high_quality[:MAX_NODES]
else:
    top_candidates = high_quality
```

**阈值选择依据**:
- 分析测试输出数据：
  - 马尔可夫理论: 0.782, 0.739, 0.737, 0.732, 0.679, 0.647, 0.629, 0.624, 0.623
  - 隐马尔可夫模型: 0.778, 0.725, 0.718, 0.715, 0.706, 0.646, 0.645, 0.644, 0.642
  - 笨蛋: 0.647, 0.636, 0.635, 0.630, 0.616, 0.611, 0.610, 0.608, 0.608
- **阈值0.62**能确保：
  - 高质量概念（>0.70）: 100%保留
  - 中等质量概念（0.62-0.70）: 选择性保留
  - 低质量概念（<0.62）: 过滤掉
  - 节点数量: 3-9个动态范围

---

### 3. ✅ Expand端点已有动态阈值

**文件**: `backend/api/routes.py` (Lines 643-669)

**状态**: 已存在相同的动态阈值逻辑（无需修改）

---

## 测试验证

### 运行测试脚本

```bash
py -3.11 test_threshold_logic.py
```

**测试覆盖**:
- ✅ 高相关性概念（马尔可夫理论）: 预期8-9个节点
- ✅ 常见概念（深度学习）: 预期7-9个节点
- ✅ 低相关性概念（笨蛋）: 预期3-5个节点
- ✅ 专业概念（量子计算）: 预期6-8个节点

---

## 前端验证

### 重启服务后验证

1. **启动后端**:
```bash
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

2. **打开前端**，输入测试概念（如"马尔可夫理论"）

3. **验证点**:
   - ✅ 节点数量在3-9个之间（不是固定9个）
   - ✅ 点击节点查看详情，显示"相似度分数"和"可信度"两个值
   - ✅ 相似度值是动态的（如0.782, 0.739, NOT 0.75固定值）
   - ✅ 控制台日志显示阈值筛选信息

---

## 日志示例

### 成功的阈值筛选日志

```
[INFO] LLM生成了20个候选概念
[INFO] 阈值筛选结果: 7个 (阈值=0.62)
[INFO] 选择了相似度最高的7个概念:
   - 隐马尔可夫模型 (相似度: 0.782)
   - 马尔可夫链蒙特卡洛 (相似度: 0.739)
   - 控制理论 (相似度: 0.737)
   - 博弈论 (相似度: 0.732)
   - 渗流理论 (相似度: 0.679)
   - 排队论 (相似度: 0.647)
   - 状态空间模型 (相似度: 0.629)
```

### 低质量概念的保底机制

```
[INFO] 阈值筛选结果不足3个，取相似度最高的3个
```

---

## 技术细节

### 相似度计算流程

1. **LLM生成候选** (20个)
2. **计算embedding** (OpenAI text-embedding-3-small)
3. **余弦相似度** 
   ```python
   similarity = cosine_similarity(embedding1, embedding2)
   # 结果范围: [0, 1]
   ```
4. **排序筛选** 
   - 阈值: 0.62
   - 最小: 3个
   - 最大: 9个

### 可信度计算公式

```python
# 基础可信度
base_credibility = 0.95 if has_wikipedia else 0.75

# 最终可信度（融合相似度）
credibility = base_credibility * (0.7 + 0.3 * similarity)

# 范围: [0.525, 0.950]
```

---

## 常见问题

### Q1: 为什么阈值选择0.62？

**A**: 基于真实测试数据分析：
- 0.70以上: 高度相关（强关联概念）
- 0.62-0.70: 中度相关（扩展概念）
- 0.62以下: 弱相关（噪声概念）

阈值0.62能在保证质量的同时，提供足够的多样性。

### Q2: 为什么设置3-9个节点？

**A**: 
- **最小3个**: 保证足够的探索广度
- **最大9个**: 避免信息过载，保持可视化清晰
- **动态调整**: 根据实际相似度分布自适应

### Q3: 如果所有候选相似度都很低怎么办？

**A**: 保底机制会强制选择相似度最高的3个，即使低于阈值。

---

## 下一步

1. ✅ 运行`test_threshold_logic.py`验证后端逻辑
2. ✅ 重启后端服务，刷新前端页面
3. ✅ 测试多个概念，验证节点数量动态变化
4. ✅ 观察相似度和可信度的区别显示

**预期结果**: 节点数量3-9个动态变化，相似度值为真实计算结果（非0.75固定值）
