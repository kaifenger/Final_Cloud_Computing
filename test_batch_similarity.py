"""测试批量相似度计算功能"""
import requests
import json

def test_discover():
    """测试功能一：自动跨学科发现"""
    url = "http://localhost:8000/api/v1/discover"  # 修正路由路径
    data = {
        "concept": "量子纠缠",
        "max_concepts": 10
    }
    
    print("=" * 60)
    print("测试功能一：自动跨学科发现")
    print("输入概念:", data["concept"])
    print("=" * 60)
    
    try:
        response = requests.post(url, json=data, timeout=120)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.text}")
            return
            
        result = response.json()
        
        if result.get("status") == "success":
            nodes = result["data"]["nodes"]
            print(f"\n✅ 成功生成 {len(nodes)} 个节点")
            print("\n节点列表:")
            for i, node in enumerate(nodes, 1):
                print(f"{i}. {node['label']} - 学科: {node.get('discipline', 'N/A')}")
                print(f"   相似度: {node.get('similarity', 'N/A'):.3f}")
        else:
            print(f"\n❌ 请求失败: {result.get('data', {}).get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")

if __name__ == "__main__":
    test_discover()
