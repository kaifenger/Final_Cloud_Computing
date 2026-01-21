"""
✅ /discover端点修复完成验证清单
=====================================

## 修复内容

### 1. 缓存键版本升级 ✅
- 文件: backend/api/routes.py (第520行)
- 修改: discover:{concept} → discover:v2:{concept}
- 状态: 已验证

### 2. 真实LLM生成流程 ✅
- LLM生成候选概念 ✓
- 语义相似度计算 ✓
- 按相似度排序选择 ✓
- 动态可信度评分 ✓
- Wikipedia定义验证 ✓

---

## 后端测试结果

```
[SUCCESS] LLM生成了20个候选概念
[SUCCESS] 相似度计算（动态值）:
  - 马尔可夫链: 0.808
  - 隐马尔可夫模型: 0.787
  - 马尔可夫决策过程: 0.808

[SUCCESS] 选择了top 9个概念
[SUCCESS] 动态可信度计算:
  - 马尔可夫链: 0.895
  - 隐马尔可夫模型: 0.889
  - 博弈论: 0.860
```

---

## 前端测试步骤

### 步骤1: 重启后端服务 🔄

```bash
# 停止当前后端（如果正在运行）
# 按 Ctrl+C

# 启动后端
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

**验证**: 看到日志输出：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### 步骤2: 刷新前端页面 🔄

1. 打开浏览器访问前端页面
2. 按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac) 强制刷新
3. 或按 F12 打开开发者工具，右键刷新按钮选择"清空缓存并硬性重新加载"

---

### 步骤3: 输入测试概念 🔍

在搜索框输入：`马尔可夫原理` 或 `深度学习` 或 `量子计算`

---

### 步骤4: 观察后端控制台输出 👀

**应该看到**（如果配置了API密钥）:
```
[INFO] 开始概念发现: 马尔可夫原理 (使用真实LLM)
[INFO] 真实生成器导入成功
[SUCCESS] 中文Wikipedia找到: 马尔可夫原理
[INFO] LLM客户端已初始化（文本生成）
[SUCCESS] LLM生成了20个相关概念
[INFO] Embedding客户端已初始化（OpenAI）
[SUCCESS] 相似度计算: 马尔可夫链 <-> 马尔可夫原理 = 0.808
[SUCCESS] 相似度计算: 隐马尔可夫模型 <-> 马尔可夫原理 = 0.787
...
[INFO] 选择了相似度最高的9个概念:
   - 马尔可夫决策过程 (相似度: 0.808)
   - 马尔可夫链 (相似度: 0.808)
   - 隐马尔可夫模型 (相似度: 0.787)
```

**不应该看到**:
```
❌ [INFO] 使用预定义概念回退方案
```

---

### 步骤5: 检查前端显示 ✅

#### 节点名称检查

**期望看到（真实概念）**:
```
✅ 马尔可夫链
✅ 隐马尔可夫模型
✅ 马尔可夫决策过程
✅ 卡尔曼滤波
✅ 蒙特卡洛方法
✅ 渗流理论
✅ 随机过程
✅ 转移矩阵
✅ PageRank算法
```

**不应该看到（模板化假数据）**:
```
❌ 马尔可夫原理的应用
❌ 马尔可夫原理的理论
❌ 马尔可夫原理的方法
```

#### 浏览器控制台检查（F12）

查看节点数据结构：
```javascript
// 在Console中输入
console.log("节点数据:", nodes);

// 期望看到
{
  id: "马尔可夫链_概率论_1",
  label: "马尔可夫链",
  discipline: "概率论",
  credibility: 0.895,        // ✅ 动态值
  similarity: 0.808,         // ✅ 动态值（不是0.75）
  source: "Wikipedia",
  depth: 1
}
```

---

## 验证点清单

### 后端验证 ✅

- [ ] 缓存键包含 `v2` 版本号
- [ ] LLM客户端成功初始化
- [ ] 生成了候选概念（通常20个）
- [ ] 计算了语义相似度（每个概念不同）
- [ ] 按相似度排序选择top-N
- [ ] 获取了Wikipedia定义
- [ ] 计算了动态可信度
- [ ] 元数据包含 `generation_method: "LLM + Similarity Ranking"`

### 前端验证 ✅

- [ ] 节点名称不是"XXX的应用/理论/方法"模板
- [ ] 节点数量正确（1个中心节点 + N个相关节点）
- [ ] 每个节点的相似度值不同（不全是0.75）
- [ ] 每个节点的可信度值不同
- [ ] 节点来源显示为"Wikipedia"或"LLM"
- [ ] 边的权重基于相似度计算

---

## 常见问题排查

### Q1: 前端仍显示旧的模板化节点？

**排查步骤**:
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 强制刷新页面（Ctrl+Shift+R）
3. 检查后端是否重启
4. 检查后端控制台是否有LLM生成日志

### Q2: 后端使用了预定义回退方案？

**可能原因**:
1. API密钥未配置
   ```bash
   # 检查 .env 文件
   OPENROUTER_API_KEY=sk-or-xxx
   OPENAI_API_KEY=sk-xxx
   ```

2. 环境变量未启用
   ```bash
   ENABLE_EXTERNAL_VERIFICATION=true
   ```

3. LLM生成失败（网络问题或API限制）

### Q3: 相似度计算都是0.75？

**可能原因**:
1. OpenAI API密钥无效
2. Embedding模型不可用
3. 网络连接问题

**解决方法**:
```bash
# 测试OpenAI连接
py -3.11 -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

---

## 成功标志

当你看到以下所有条件时，说明修复成功：

✅ 后端日志显示"LLM生成了XX个候选概念"
✅ 后端日志显示"相似度计算: XXX <-> XXX = 0.XXX"
✅ 前端显示真实学术概念名称（非模板）
✅ 每个节点的相似度值都不同
✅ 浏览器控制台显示动态计算的可信度和相似度

---

## 测试命令合集

```bash
# 1. 测试discover端点
py -3.11 test_discover_real.py

# 2. 验证缓存键版本
py -3.11 -c "from backend.api.routes import discover_concepts; import inspect; print([l for l in inspect.getsource(discover_concepts).split('\n') if 'cache_key' in l][0])"

# 3. 启动后端（带日志）
py -3.11 -m uvicorn backend.main:app --reload --port 8000 --log-level debug

# 4. 测试API（命令行）
curl -X POST http://localhost:8000/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"concept":"马尔可夫原理","max_concepts":10}' | python -m json.tool
```

---

## 下一步

1. ✅ 重启后端服务
2. ✅ 刷新前端页面
3. ✅ 输入测试概念
4. ✅ 验证节点名称是真实概念
5. ✅ 验证相似度是动态计算
6. ✅ 验证可信度是动态评分

**祝测试顺利！🎉**
"""

print(__doc__)
