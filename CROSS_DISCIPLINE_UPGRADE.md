# 跨学科概念挖掘系统升级说明

## 修改总结

### 1. ✅ LLM模型升级：Gemini 2.0 Flash → Gemini 2.0 Flash Thinking (3flash)

**修改原因**：Gemini 2.0 Flash Thinking (thinking-exp-01-21) 具有更强的推理能力，特别适合跨学科概念关联分析。

**修改文件**：
- `backend/api/routes.py` (3处)
- `backend/api/real_node_generator.py` (2处)
- `backend/api/ai_chat.py` (1处)

**修改内容**：
```python
# 修改前
model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001")

# 修改后
model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-thinking-exp-01-21")
```

**配置方式**：
在 `.env` 文件中添加：
```bash
LLM_MODEL=google/gemini-2.0-flash-thinking-exp-01-21
```

---

### 2. ✅ 完善跨学科Prompt：强制搜索"远亲概念"

**核心目标**：解决知识碎片化，挖掘跨领域概念的深层关联

**修改文件**：`backend/api/real_node_generator.py`

**新Prompt设计**：

#### 跨学科搜索策略（强制执行）

必须从以下6个领域各找至少1个概念：

1. **数学/统计学**：数学本质、理论基础
2. **物理学**：物理类比、能量/信息原理
3. **生物学/神经科学**：仿生学启发、演化机制
4. **计算机科学**：算法实现、工程应用
5. **社会学/经济学**：群体行为、博弈模型
6. **其他交叉学科**：心理学、语言学、复杂系统等

#### "远亲概念"判定标准

✅ **好的远亲概念**（必须满足至少一条）：
- 数学形式相同但应用领域不同（如：熵在热力学vs信息论）
- 底层原理一致（如：神经网络vs生物神经元、PageRank vs随机游走）
- 历史启发关系（如：遗传算法vs达尔文进化论）
- 结构同构（如：社交网络vs蛋白质网络）

❌ **避免的表面关联**：
- 仅仅名字相似（如："网络"在计算机网络vs神经网络）
- 单纯的应用关系（如：机器学习用于医疗诊断）

#### 输出格式（4字段）

```
概念名|学科|关系类型|跨学科原理

示例：
神经网络|生物学|bio_inspired|模拟生物神经元的突触连接和激活传播机制
信息熵|物理学|mathematical_analogy|与热力学熵数学形式完全一致(H=-Σp·log(p))
PageRank算法|图论|structural_isomorphism|本质是马尔可夫链的平稳分布求解
遗传算法|进化生物学|evolutionary_mechanism|复制达尔文的变异-选择-遗传进化过程
```

**System Prompt升级**：
```python
"你是跨学科知识挖掘专家，擅长发现不同领域间的深层原理关联和结构同构性。
你的核心能力是识别'远亲概念' - 那些表面看起来毫不相关，但底层数学、物理
或信息论原理完全一致的概念。"
```

**温度参数调整**：
```python
temperature=0.4  # 提高创造性（原0.3），允许更大胆的跨学科联想
max_tokens=800   # 增加输出长度（原500），支持更详细的原理解释
timeout=20.0     # 增加超时时间（原15秒），给thinking模型更多推理时间
```

---

### 3. ✅ 学科分类逻辑说明

**回答问题**：学科是怎么固定的？固定了6大学科还是有别的逻辑？

#### 当前学科分类机制

**定义位置**：`shared/constants.py`

```python
class Discipline:
    MATH = "数学"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    COMPUTER = "计算机"
    SOCIOLOGY = "社会学"
    
    ALL = [MATH, PHYSICS, CHEMISTRY, BIOLOGY, COMPUTER, SOCIOLOGY]
```

#### 学科分类的3种来源

##### 方式1：LLM动态生成（主要方式）⭐

**位置**：`backend/api/real_node_generator.py` - `generate_related_concepts()`

**工作原理**：
- LLM在生成概念时，自动判断学科归属
- **不限于6大学科**，可以生成任意学科名称
- 示例输出：
  ```
  卷积神经网络|计算机科学|sub_field
  反向传播|算法|methodology
  熵增原理|热力学|foundation
  遗传算法|进化生物学|bio_inspired
  ```

**灵活性**：
- ✅ 可生成细分学科：信息论、优化理论、统计力学
- ✅ 可生成交叉学科：生物信息学、神经科学、复杂系统
- ✅ 可生成方法论学科：方法论、算法、理论基础

##### 方式2：预定义映射（fallback）

**位置**：`backend/api/real_node_generator.py` - `_get_fallback_concepts()`

```python
domain_mapping = {
    "机器学习": [
        {"name": "深度学习", "discipline": "计算机科学", "relation": "sub_field"},
        {"name": "神经网络", "discipline": "人工智能", "relation": "foundation"},
    ],
    # ...
}
```

**触发条件**：LLM生成失败时使用

##### 方式3：前端颜色映射（仅可视化）

**位置**：`shared/constants.py` - `Discipline.COLORS`

**作用**：
- 仅用于前端图谱节点着色
- 如果LLM生成的学科不在预定义列表中，使用默认颜色

```python
COLORS = {
    "数学": "#FF6B6B",
    "物理": "#4ECDC4",
    "计算机": "#AA96DA",
    # ... 其他学科使用默认颜色
}
```

#### 总结：学科分类是动态的

✅ **不是固定6大学科**：
- LLM可以生成任何学科名称（计算机科学、信息论、神经科学等）
- 只有前端颜色映射限定了6种，但不影响功能

✅ **优势**：
- 自适应不同领域的概念
- 支持细分学科和交叉学科
- 更贴近真实学术体系

❌ **局限**：
- 学科名称可能不统一（如"计算机科学"vs"计算机"）
- 前端颜色映射可能不够精确

---

## 实际案例对比

### 修改前：浅层关联

**搜索"神经网络"**：
```
- 深度学习|计算机科学|sub_field
- 卷积神经网络|计算机科学|sub_field
- 反向传播|算法|methodology
```
**问题**：全是计算机领域，没有跨学科视角

### 修改后：深层跨学科关联

**搜索"神经网络"**（预期）：
```
1. 生物神经元|神经科学|bio_inspired|模拟生物神经元的突触和激活机制
2. 霍普菲尔德网络|统计物理|energy_model|基于伊辛模型的能量最小化原理
3. 贝叶斯网络|概率论|probabilistic_reasoning|图模型表示的概率推理框架
4. 图论|数学|structural_foundation|网络的拓扑结构和连通性分析
5. 深度学习|计算机科学|sub_field|多层神经网络的特征提取
6. 复杂系统|系统科学|emergent_behavior|简单节点交互产生复杂涌现行为
```

**优势**：
- 覆盖6个不同学科
- 揭示深层数学/物理原理
- 发现历史启发关系

---

## 测试验证

### 测试脚本

创建 `test_cross_discipline.py`：

```python
import asyncio
import httpx

async def test_cross_discipline_discovery():
    """测试跨学科概念挖掘"""
    test_cases = [
        ("神经网络", "期望找到：生物神经元、霍普菲尔德网络、图论"),
        ("熵", "期望找到：信息熵、热力学熵、统计熵"),
        ("PageRank", "期望找到：马尔可夫链、随机游走、图论"),
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for concept, expectation in test_cases:
            print(f"\n{'='*60}")
            print(f"测试概念: {concept}")
            print(f"预期: {expectation}")
            print(f"{'='*60}")
            
            response = await client.post(
                "http://localhost:8000/api/v1/discover",
                json={"concept": concept, "max_concepts": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                nodes = data["data"]["nodes"]
                
                # 统计学科分布
                disciplines = {}
                for node in nodes:
                    disc = node.get("discipline", "未知")
                    disciplines[disc] = disciplines.get(disc, 0) + 1
                
                print(f"\n[学科分布]")
                for disc, count in disciplines.items():
                    print(f"  {disc}: {count}个")
                
                # 检查是否有跨学科
                if len(disciplines) >= 3:
                    print(f"\n✅ 跨学科挖掘成功！覆盖{len(disciplines)}个领域")
                else:
                    print(f"\n⚠️  学科覆盖不足，仅{len(disciplines)}个领域")
                
                # 显示跨学科原理
                print(f"\n[跨学科原理]")
                for node in nodes[1:6]:  # 显示前5个
                    label = node.get("label", "")
                    disc = node.get("discipline", "")
                    principle = node.get("cross_principle", "N/A")
                    print(f"  {label} ({disc})")
                    print(f"    原理: {principle[:80]}...")

asyncio.run(test_cross_discipline_discovery())
```

### 验证点

1. ✅ 学科分布：每个概念应覆盖3-6个不同学科
2. ✅ 远亲概念：出现表面无关但原理相通的概念
3. ✅ 原理解释：每个概念有明确的跨学科原理说明
4. ✅ 多样性：避免同一领域扎堆

---

## 环境配置

### .env文件更新

```bash
# LLM配置
LLM_MODEL=google/gemini-2.0-flash-thinking-exp-01-21
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Embedding配置（相似度计算）
OPENAI_API_KEY=your_openai_key

# 外部验证开关
ENABLE_EXTERNAL_VERIFICATION=true
```

### 重启服务

```bash
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

---

## FAQ

### Q1: 为什么选择Gemini 2.0 Flash Thinking？

**A**: 
- 具有深度推理能力（thinking模式）
- 更擅长发现隐含的跨学科关联
- 支持更长的推理链条
- 成本与flash版本相同

### Q2: 温度参数为什么从0.3提升到0.4？

**A**: 
- 跨学科联想需要更高创造性
- 0.3过于保守，容易停留在直接关联
- 0.4平衡了创造性和准确性

### Q3: 学科不限于6大类会不会混乱？

**A**: 
- 优势：更贴近真实学术体系
- 前端处理：未预定义学科使用默认颜色
- 后续优化：可以引入学科本体规范化

### Q4: 如何保证"远亲概念"的质量？

**A**: 
1. Prompt明确要求底层原理关联
2. 增加"跨学科原理"字段强制解释
3. 相似度计算过滤无关概念
4. 动态阈值筛选（0.62）保证质量

### Q5: 旧数据会受影响吗？

**A**: 
- 兼容旧格式：支持3字段和4字段输出
- 缓存策略：v2版本缓存键独立
- 渐进升级：新查询使用新逻辑

---

## 下一步优化建议

1. **学科本体规范化**：引入学科标准分类体系
2. **关联强度量化**：为每个跨学科关联计算置信度
3. **可视化增强**：高亮跨学科边，不同颜色表示关联类型
4. **历史追溯**：记录概念间的历史启发关系
5. **用户反馈**：允许用户标注关联质量

---

**修改完成时间**：2026年1月21日  
**测试状态**：待验证  
**兼容性**：向后兼容
