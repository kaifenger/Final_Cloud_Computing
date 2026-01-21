# 修复说明

## 已创建真实节点生成器

文件：`backend/api/real_node_generator.py`

功能：
1. ✅ 使用LLM生成相关概念（不是预定义映射）
2. ✅ OpenAI embeddings计算语义相似度
3. ✅ 动态可信度公式：base * (0.7 + 0.3 * similarity)
4. ✅ 学术概念过滤器

## 需要手动修改routes.py

### 1. 在文件开头添加导入（第13行后）：

```python
# 导入真实节点生成器
try:
    from backend.api.real_node_generator import (
        generate_related_concepts,
        compute_credibility,
        is_academic_concept
    )
    USE_REAL_GENERATOR = True
    print("[INFO] 真实节点生成器已加载")
except ImportError as e:
    print(f"[WARNING] 真实节点生成器加载失败: {e}")
    USE_REAL_GENERATOR = False
```

### 2. 修改AI问答函数（第682行）：

替换：
```python
system_prompt = f"""你是专业学术助手，擅长解答关于"{concept}"的问题。回答要准确简洁（150字以内）。"""
```

为：
```python
context = request.get("context", "")
context_info = f"\n\n背景信息：{context}" if context else ""

system_prompt = f"""你是一个专业的学术助手，擅长解答关于"{concept}"的学术问题。

要求：
1. 回答要准确、简洁（150字以内）
2. 使用通俗易懂的语言
3. 直接回答问题，不要说"您的问题不明确"
4. 如果问题是"什么是{concept}"，请直接解释该概念{context_info}"""
```

### 3. 完全替换expand_node函数（第556-652行）：

```python
@router.post("/expand")
async def expand_node(request: ExpandRequest):
    """展开节点 - 使用LLM生成相关概念 + 语义相似度计算"""
    print(f"[INFO] 展开节点: {request.node_label}")
    print(f"[INFO] 使用真实生成器: {USE_REAL_GENERATOR}")
    
    new_nodes = []
    new_edges = []
    
    # 使用LLM生成概念
    if USE_REAL_GENERATOR:
        try:
            llm_concepts = await generate_related_concepts(
                parent_concept=request.node_label,
                existing_concepts=[request.node_label] + request.existing_nodes,
                max_count=request.max_new_nodes
            )
            
            for i, concept_info in enumerate(llm_concepts):
                concept_name = concept_info["name"]
                discipline = concept_info["discipline"]
                relation_type = concept_info["relation"]
                
                node_id = f"{request.node_id}_expand_{i}"
                if node_id in request.existing_nodes:
                    continue
                
                # 学术过滤
                if not await is_academic_concept(concept_name):
                    print(f"[FILTER] 跳过非学术概念: {concept_name}")
                    continue
                
                # 获取Wikipedia
                wiki_result = await get_wikipedia_definition(concept_name, max_length=500)
                
                # 计算动态可信度（基于相似度）
                credibility = await compute_credibility(
                    concept=concept_name,
                    parent_concept=request.node_label,
                    has_wikipedia=wiki_result["exists"]
                )
                
                new_nodes.append({
                    "id": node_id,
                    "label": concept_name,
                    "discipline": discipline,
                    "definition": wiki_result["definition"] if wiki_result["exists"] else f"{concept_name}是{request.node_label}相关的学术概念。",
                    "credibility": credibility,
                    "source": "Wikipedia" if wiki_result["exists"] else "LLM",
                    "wiki_url": wiki_result.get("url", "")
                })
                
                new_edges.append({
                    "source": request.node_id,
                    "target": node_id,
                    "relation": relation_type,
                    "weight": credibility * 0.9,
                    "reasoning": f"{concept_name}是{request.node_label}的{relation_type}"
                })
            
            print(f"[SUCCESS] 最终生成{len(new_nodes)}个有效节点")
            
        except Exception as e:
            print(f"[ERROR] 真实生成器失败: {str(e)}")
            USE_REAL_GENERATOR = False
    
    # 回退方案
    if not USE_REAL_GENERATOR or len(new_nodes) == 0:
        # 使用预定义映射...（保留原代码）
        pass
    
    return {
        "status": "success",
        "data": {
            "nodes": new_nodes,
            "edges": new_edges,
            "parent_id": request.node_id,
            "generation_mode": "real_llm" if USE_REAL_GENERATOR else "fallback"
        }
    }
```

## 测试真实生成器

```powershell
cd d:\yunjisuanfinal
py -3.11 backend/api/real_node_generator.py
```

## 重启后端测试

```powershell
# 停止当前后端
# Ctrl+C

# 重启
py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 预期日志输出

```
[INFO] 真实节点生成器已加载
[INFO] LLM客户端已初始化（文本生成）
[INFO] Embedding客户端已初始化（OpenAI）
[INFO] 展开节点: 机器学习
[INFO] 使用真实生成器: True
[SUCCESS] LLM生成了3个概念
[SUCCESS] 相似度计算: 深度学习 <-> 机器学习 = 0.87
[INFO] 可信度: 深度学习 = 0.92 (base=0.95, similarity=0.87)
[FILTER] 跳过非学术概念: 笨蛋
[SUCCESS] 最终生成3个有效节点
```
