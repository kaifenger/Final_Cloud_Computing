"""节点展开逻辑说明 - 数据流演示"""
import sys

print("=" * 80)
print("节点展开逻辑 - 数据流设计")
print("=" * 80)

print("""
## 核心问题解答

### 1. 节点展开使用真实LLM生成 ✓

**当前实现**: `/expand` 端点已更新为使用 `real_node_generator.py`

```python
# 步骤1: LLM生成相关概念
candidates = await generate_related_concepts(
    parent_concept=request.node_label,
    existing_concepts=request.existing_nodes,
    max_count=request.max_new_nodes * 2  # 生成2倍候选
)

# LLM提示词示例:
# "请为概念'机器学习'生成5个相关的学术概念"
# 输出格式: 概念名|学科|关系类型
```

**输出示例**:
- 深度学习|计算机科学|sub_field
- 监督学习|方法论|methodology
- 神经网络|人工智能|foundation
- 强化学习|计算机科学|sub_field
- 特征工程|数据科学|methodology

---

### 2. 语义相似度计算的作用

**三重作用**:

#### (1) 质量筛选 - 最重要
```
问题: LLM生成的概念质量参差不齐
解决: 计算相似度，过滤低相关概念

示例:
  机器学习 <-> 深度学习: 0.892  ✓ 保留
  机器学习 <-> 云计算: 0.512    ✗ 丢弃
```

#### (2) 排序依据
```
策略: 按相似度降序排列，选择top-N

结果: 用户看到的都是最相关的概念
```

#### (3) 可信度加权
```
公式: credibility = base * (0.7 + 0.3 * similarity)

效果: 
  高相似度 → 高可信度
  低相似度 → 低可信度（即使有Wikipedia）
```

**技术实现**:
```python
# 使用OpenAI text-embedding-3-small (1536维向量)
emb1 = get_embedding(concept1)  # [1536]
emb2 = get_embedding(concept2)  # [1536]

# 余弦相似度
similarity = dot(emb1, emb2) / (norm(emb1) * norm(emb2))

# 归一化到 [0, 1]
normalized = (similarity + 1) / 2
```

---

### 3. 节点选择策略: Top-N相似度排序

**完整流程**:

```
步骤1: 生成候选
  LLM生成 10个候选概念 (需要5个，生成2倍)

步骤2: 计算相似度
  对每个候选计算与父节点的语义相似度
  - 深度学习: 0.892
  - 监督学习: 0.854
  - 神经网络: 0.831
  - 强化学习: 0.798
  - 特征工程: 0.776
  - 决策树: 0.742
  - 计算机视觉: 0.712
  - 自然语言处理: 0.689
  - 云计算: 0.512
  - 区块链: 0.421

步骤3: 排序选择Top-5
  [✓] 深度学习 (0.892)
  [✓] 监督学习 (0.854)
  [✓] 神经网络 (0.831)
  [✓] 强化学习 (0.798)
  [✓] 特征工程 (0.776)
  [✗] 决策树 (0.742) - 被丢弃
  [✗] 计算机视觉 (0.712) - 被丢弃
  ...其他低相关概念也被丢弃
```

**为什么生成2倍候选?**
- LLM质量波动，多生成候选保证有足够选择
- 相似度筛选后仍有高质量概念

---

### 4. 动态可信度评分

**公式**:
```
credibility = base_credibility * (0.7 + 0.3 * similarity)
```

**参数说明**:
| 参数 | 来源 | 取值 |
|------|------|------|
| base_credibility | 数据来源 | 0.95 (Wikipedia) / 0.70 (LLM) |
| similarity | 语义相似度 | [0, 1] |

**计算示例**:

```
示例1: 深度学习 (有Wikipedia, 相似度0.892)
  credibility = 0.95 * (0.7 + 0.3 * 0.892)
              = 0.95 * 0.9676
              = 0.919 ✓

示例2: 特征工程 (无Wikipedia, 相似度0.776)
  credibility = 0.70 * (0.7 + 0.3 * 0.776)
              = 0.70 * 0.9328
              = 0.653 ✓

示例3: 云计算 (有Wikipedia, 但相似度仅0.512)
  credibility = 0.95 * (0.7 + 0.3 * 0.512)
              = 0.95 * 0.8536
              = 0.811 
  (虽然有Wiki，但因相似度低，可信度也被降低)
```

**可信度范围**:
- 最高: 0.95 * (0.7 + 0.3 * 1.0) = **0.950**
- 最低: 0.70 * (0.7 + 0.3 * 0.0) = **0.490**
- 典型: 0.95 * (0.7 + 0.3 * 0.85) = **0.907**

---

## 完整数据流

```
用户点击节点 "机器学习"
    ↓
POST /expand {node_label: "机器学习", max_new_nodes: 3}
    ↓
步骤1: LLM生成 6个候选 (3 * 2)
    ↓
步骤2: 计算每个候选与"机器学习"的相似度
    深度学习: 0.892
    监督学习: 0.854
    神经网络: 0.831
    强化学习: 0.798
    特征工程: 0.776
    计算机视觉: 0.712
    ↓
步骤3: 按相似度排序，选择Top-3
    [✓] 深度学习 (0.892)
    [✓] 监督学习 (0.854)
    [✓] 神经网络 (0.831)
    [✗] 强化学习 (0.798)
    [✗] 特征工程 (0.776)
    [✗] 计算机视觉 (0.712)
    ↓
步骤4: 获取Wikipedia定义
    深度学习: ✓ 找到
    监督学习: ✓ 找到
    神经网络: ✓ 找到
    ↓
步骤5: 计算动态可信度
    深度学习: 0.95 * (0.7 + 0.3 * 0.892) = 0.919
    监督学习: 0.95 * (0.7 + 0.3 * 0.854) = 0.909
    神经网络: 0.95 * (0.7 + 0.3 * 0.831) = 0.902
    ↓
步骤6: 生成简介（LLM）
    深度学习: "通过多层神经网络学习数据表示的方法"
    监督学习: "通过标注数据训练模型的学习范式"
    神经网络: "模拟生物神经系统的计算模型"
    ↓
返回结果 (3个节点 + 3条边)
    {
      "nodes": [
        {
          "label": "深度学习",
          "credibility": 0.919,
          "similarity": 0.892,
          "source": "Wikipedia"
        },
        ...
      ],
      "metadata": {
        "total_candidates": 6,
        "selected_count": 3,
        "avg_similarity": 0.859,
        "generation_method": "LLM + Similarity Ranking"
      }
    }
    ↓
前端展示 (按可信度或相似度排序)
```

---

## 关键技术栈

| 组件 | 技术 | 模型/API |
|------|------|----------|
| 概念生成 | OpenRouter | google/gemini-2.0-flash-001 |
| 语义相似度 | OpenAI | text-embedding-3-small (1536维) |
| 定义验证 | Wikipedia | zh/en Wikipedia API |
| 简介生成 | OpenRouter | google/gemini-2.0-flash-001 |

---

## 代码验证

### 查看当前实现
```bash
# 查看/expand端点代码
code backend/api/routes.py:465

# 查看真实生成器
code backend/api/real_node_generator.py
```

### 运行测试
```bash
# 测试real_node_generator模块
py -3.11 backend/api/real_node_generator.py

# 测试完整展开流程（需要API密钥）
py -3.11 test_expand_logic.py
```

---

## 总结

✓ **真实LLM生成**: 使用OpenRouter Gemini 2.0生成概念
✓ **语义相似度排序**: OpenAI embeddings计算，选择top-N
✓ **动态可信度**: base * (0.7 + 0.3 * similarity)
✓ **Wikipedia验证**: 获取权威定义提高可信度
✓ **优雅降级**: LLM失败时使用预定义概念

**数据流核心**: LLM生成 → 相似度筛选 → 排序选择 → 动态评分 → 返回结果
""")

print("=" * 80)
print("[文档]")
print("  详细设计: NODE_EXPANSION_LOGIC.md")
print("  代码实现: backend/api/routes.py (expand_node)")
print("  核心模块: backend/api/real_node_generator.py")
print("=" * 80)
