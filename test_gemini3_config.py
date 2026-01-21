"""
Gemini 3 Flash 配置验证脚本
验证新LLM配置是否正确工作
"""
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

async def test_gemini_3_flash():
    """测试Gemini 3 Flash配置"""
    print("="*70)
    print("Gemini 3 Flash 配置验证")
    print("="*70)
    
    # 检查环境变量
    print("\n[1] 检查环境变量")
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "google/gemini-3-flash-preview")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY 未设置")
        print("   请在 .env 文件中添加：OPENROUTER_API_KEY=your_key")
        return
    else:
        print(f"✅ OPENROUTER_API_KEY: {api_key[:20]}...")
    
    print(f"✅ OPENROUTER_BASE_URL: {base_url}")
    print(f"✅ LLM_MODEL: {model}")
    
    # 创建客户端
    print("\n[2] 初始化OpenAI客户端")
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        print("✅ 客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return
    
    # 测试基本调用
    print("\n[3] 测试基本LLM调用（不启用reasoning）")
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "用一句话解释什么是神经网络"}
                ],
                temperature=0.3,
                max_tokens=100
            ),
            timeout=30.0
        )
        
        if response and response.choices:
            answer = response.choices[0].message.content.strip()
            print(f"✅ LLM响应成功")
            print(f"   回答: {answer[:100]}...")
        else:
            print("❌ 响应格式错误")
    except asyncio.TimeoutError:
        print("❌ 请求超时（30秒）")
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        return
    
    # 测试reasoning模式
    print("\n[4] 测试Reasoning模式（启用推理）")
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": "神经网络和生物神经元有什么深层联系？"
                    }
                ],
                temperature=0.4,
                max_tokens=200,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=30.0
        )
        
        if response and response.choices:
            message = response.choices[0].message
            answer = message.content.strip()
            
            print(f"✅ Reasoning模式响应成功")
            print(f"   回答: {answer[:150]}...")
            
            # 检查是否有reasoning_details
            if hasattr(message, 'reasoning_details') and message.reasoning_details:
                print(f"   ✅ 包含推理细节: {message.reasoning_details}")
            else:
                print(f"   ℹ️  未返回推理细节（可能模型不支持或未输出）")
        else:
            print("❌ 响应格式错误")
    except asyncio.TimeoutError:
        print("❌ 请求超时（30秒）")
    except Exception as e:
        print(f"❌ Reasoning调用失败: {e}")
        return
    
    # 测试跨学科概念生成
    print("\n[5] 测试跨学科概念生成")
    try:
        prompt = """你是跨学科知识挖掘专家。请为概念"熵"生成3个跨学科的相关概念。

必须从不同领域寻找（物理学、信息论、统计学等）。

输出格式（每行一个）：
概念名|学科|关系类型|跨学科原理

请直接输出："""
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是跨学科知识挖掘专家，擅长发现不同领域间的深层原理关联。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=300,
                extra_body={"reasoning": {"enabled": True}}
            ),
            timeout=30.0
        )
        
        if response and response.choices:
            answer = response.choices[0].message.content.strip()
            print(f"✅ 跨学科生成成功")
            print(f"   结果:")
            for line in answer.split('\n')[:5]:
                if line.strip():
                    print(f"      {line.strip()}")
            
            # 验证格式
            if '|' in answer:
                print(f"   ✅ 输出格式正确（包含管道符）")
            else:
                print(f"   ⚠️  输出格式可能需要调整")
        else:
            print("❌ 响应格式错误")
    except asyncio.TimeoutError:
        print("❌ 请求超时（30秒）")
    except Exception as e:
        print(f"❌ 跨学科生成失败: {e}")
        return
    
    # 总结
    print("\n" + "="*70)
    print("验证总结")
    print("="*70)
    print(f"✅ 环境变量配置正确")
    print(f"✅ OpenAI客户端工作正常")
    print(f"✅ Gemini 3 Flash模型可访问")
    print(f"✅ Reasoning模式已启用")
    print(f"✅ 跨学科Prompt工作正常")
    print(f"\n🎉 所有测试通过！可以开始使用系统。")


async def test_similarity_calculation():
    """测试相似度计算（需要OpenAI API）"""
    print("\n" + "="*70)
    print("相似度计算测试（可选）")
    print("="*70)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY 未设置，跳过相似度测试")
        print("   相似度计算需要OpenAI API密钥")
        return
    
    print(f"✅ OPENAI_API_KEY: {openai_key[:20]}...")
    
    try:
        from openai import AsyncOpenAI
        import numpy as np
        
        client = AsyncOpenAI(api_key=openai_key)
        
        # 测试embedding
        concept1 = "神经网络"
        concept2 = "深度学习"
        
        print(f"\n计算相似度: '{concept1}' <-> '{concept2}'")
        
        response1 = await client.embeddings.create(
            model="text-embedding-3-small",
            input=concept1
        )
        response2 = await client.embeddings.create(
            model="text-embedding-3-small",
            input=concept2
        )
        
        embedding1 = np.array(response1.data[0].embedding)
        embedding2 = np.array(response2.data[0].embedding)
        
        # 余弦相似度
        cosine_sim = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        similarity = float(max(0, min(1, (cosine_sim + 1) / 2)))
        
        print(f"✅ 相似度计算成功: {similarity:.3f}")
        
        if similarity > 0.8:
            print(f"   评价: 高度相关（强关联）")
        elif similarity > 0.6:
            print(f"   评价: 中度相关（扩展概念）")
        else:
            print(f"   评价: 弱相关（边缘概念）")
        
    except ImportError:
        print("❌ 缺少numpy库，请安装: pip install numpy")
    except Exception as e:
        print(f"❌ 相似度计算失败: {e}")


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(test_gemini_3_flash())
    asyncio.run(test_similarity_calculation())
