#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动修复routes.py，添加真实节点生成功能"""

import re

def fix_routes_file():
    """修复routes.py文件"""
    
    file_path = "backend/api/routes.py"
    
    print("="*60)
    print("开始修复routes.py")
    print("="*60)
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 在导入部分添加真实生成器导入
    print("\n[1] 添加真实节点生成器导入...")
    
    import_addition = '''
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
'''
    
    # 在第一个load_dotenv后添加
    if 'USE_REAL_GENERATOR' not in content:
        content = content.replace(
            'load_dotenv(dotenv_path=env_path)',
            'load_dotenv(dotenv_path=env_path)\n' + import_addition
        )
        print("   ✅ 已添加导入")
    else:
        print("   ⏭️  导入已存在")
    
    # 2. 修复AI问答prompt
    print("\n[2] 修复AI问答prompt...")
    
    old_ai_prompt = '''    try:
        system_prompt = f"""你是专业学术助手，擅长解答关于"{concept}"的问题。回答要准确简洁（150字以内）。"""'''
    
    new_ai_prompt = '''    # 添加上下文信息
    context = request.get("context", "")
    context_info = f"\\n\\n背景信息：{context}" if context else ""
    
    try:
        system_prompt = f"""你是一个专业的学术助手，擅长解答关于"{concept}"的学术问题。

要求：
1. 回答要准确、简洁（150字以内）
2. 使用通俗易懂的语言
3. 直接回答问题，不要说"您的问题不明确"
4. 如果问题是"什么是{concept}"，请直接解释该概念{context_info}"""'''
    
    content = content.replace(old_ai_prompt, new_ai_prompt)
    print("   ✅ AI问答prompt已修复")
    
    # 3. 添加generation_mode到返回值
    print("\n[3] 添加generation_mode到expand返回值...")
    
    # 查找expand函数的return语句
    expand_return_pattern = r'(return \{[^}]*"parent_id": request\.node_id[^}]*)\}'
    
    if '"generation_mode"' not in content:
        content = re.sub(
            expand_return_pattern,
            r'\1,\n            "generation_mode": "real_llm" if USE_REAL_GENERATOR else "fallback"\n        }',
            content
        )
        print("   ✅ 已添加generation_mode")
    else:
        print("   ⏭️  generation_mode已存在")
    
    # 保存文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ routes.py修复完成")
    print("="*60)
    
    print("\n下一步:")
    print("1. 重启后端服务")
    print("2. 测试节点展开功能")
    print("3. 查看日志确认使用真实生成器")

if __name__ == "__main__":
    try:
        fix_routes_file()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
