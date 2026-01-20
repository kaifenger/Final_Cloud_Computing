"""直接测试Wikipedia API"""
import asyncio
import sys
sys.path.insert(0, "D:/yunjisuanfinal")

async def test_wikipedia():
    from backend.api.routes import get_wikipedia_definition
    
    test_terms = ["量子计算", "机器学习", "深度学习", "笨蛋", "爱情"]
    
    for term in test_terms:
        print(f"\n测试: {term}")
        result = await get_wikipedia_definition(term, max_length=200)
        print(f"  存在: {result['exists']}")
        print(f"  来源: {result['source']}")
        if result['exists']:
            print(f"  定义: {result['definition'][:100]}...")
        else:
            print(f"  错误: {result.get('definition', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_wikipedia())
