#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整的后端检查和修复脚本"""

import subprocess
import time
import sys
import os
from pathlib import Path

def check_backend_status():
    """检查后端状态"""
    print("\n" + "="*60)
    print("📋 后端状态检查")
    print("="*60)
    
    # 1. 检查routes.py语法
    print("\n[1] 检查routes.py语法...")
    try:
        with open("backend/api/routes.py", "r", encoding="utf-8") as f:
            compile(f.read(), "routes.py", "exec")
        print("   ✅ routes.py 语法正确")
    except Exception as e:
        print(f"   ❌ routes.py 语法错误: {e}")
        return False
    
    # 2. 检查导入
    print("\n[2] 检查模块导入...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from backend.api import routes; print('导入成功')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("   ✅ routes模块导入成功")
        else:
            print(f"   ❌ 导入失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ 导入检查失败: {e}")
        return False
    
    # 3. 检查端口配置
    print("\n[3] 检查端口配置...")
    api_ts_path = Path("frontend/src/services/api.ts")
    if api_ts_path.exists():
        with open(api_ts_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "localhost:8000" in content:
                print("   ✅ 前端配置端口: 8000")
            elif "localhost:8888" in content:
                print("   ⚠️  前端配置端口: 8888 (与后端8000不匹配)")
            else:
                print("   ❓ 未找到端口配置")
    
    # 4. 检查环境变量
    print("\n[4] 检查环境变量...")
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "ENABLE_EXTERNAL_VERIFICATION" in content:
                if "ENABLE_EXTERNAL_VERIFICATION=true" in content or "ENABLE_EXTERNAL_VERIFICATION = true" in content:
                    print("   ⚠️  外部验证已启用 (会调用Wikipedia和Arxiv)")
                else:
                    print("   ✅ 外部验证已禁用")
            else:
                print("   ⚠️  未设置ENABLE_EXTERNAL_VERIFICATION")
    
    # 5. 列出所有API端点
    print("\n[5] 检查API端点...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", """
from backend.api import routes
router = routes.router
print(f"路由数量: {len(router.routes)}")
for route in router.routes:
    if hasattr(route, 'path'):
        print(f"  - {route.methods} {route.path}")
"""],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"   ❌ 获取路由失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 检查完成")
    print("="*60)
    
    return True

def show_startup_commands():
    """显示启动命令"""
    print("\n" + "="*60)
    print("🚀 后端启动命令")
    print("="*60)
    print("\n方案1: 启动在8000端口（前端已配置）")
    print("  cd d:\\yunjisuanfinal")
    print("  py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    
    print("\n方案2: 启动在8888端口")
    print("  cd d:\\yunjisuanfinal")
    print("  py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8888")
    
    print("\n方案3: 使用配置文件端口")
    print("  cd d:\\yunjisuanfinal")
    print("  py -3.11 -m uvicorn backend.main:app --reload")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    if check_backend_status():
        show_startup_commands()
        
        print("\n💡 提示:")
        print("  1. 确保前端api.ts配置的端口与后端启动端口一致")
        print("  2. 如需禁用外部验证，在.env中设置: ENABLE_EXTERNAL_VERIFICATION=false")
        print("  3. 访问 http://localhost:8000/docs 查看API文档")
        print("  4. Neo4j和Redis连接失败会自动切换到Mock模式")
    else:
        print("\n❌ 检查失败，请修复上述问题后再启动")
        sys.exit(1)
