#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OpenAI API连接
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# 加载.env文件
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("="*60)
print("检查OpenAI API配置")
print("="*60)

# 检查API Key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OPENAI_API_KEY: 已配置 (前10字符: {api_key[:10]}...)")
else:
    print("❌ OPENAI_API_KEY: 未配置")
    sys.exit(1)

# 测试连接
print("\n测试OpenAI API连接...")

async def test_connection():
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        response = await asyncio.wait_for(
            client.embeddings.create(
                model="text-embedding-3-small",
                input=["测试"]
            ),
            timeout=10.0
        )
        print("✅ OpenAI API连接成功")
        print(f"   返回embedding维度: {len(response.data[0].embedding)}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API连接失败: {e}")
        return False

result = asyncio.run(test_connection())

if result:
    print("\n✅ 所有检查通过！")
else:
    print("\n❌ 连接测试失败，请检查：")
    print("1. API Key是否有效")
    print("2. 网络连接是否正常")
    print("3. 是否需要配置代理")
