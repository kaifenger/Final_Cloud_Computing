"""
测试discover接口，检查返回的数据结构
"""
import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.api.routes import get_mock_discovery_result

async def test_discover():
    print("=" * 50)
    print("测试概念挖掘接口")
    print("=" * 50)
    
    concept = "神经网络"
    print(f"\n搜索概念: {concept}\n")
    
    result = await get_mock_discovery_result(concept)
    
    print(f"\n状态: {result['status']}")
    print(f"节点数量: {len(result['data']['nodes'])}")
    print(f"边数量: {len(result['data']['edges'])}")
    
    print("\n节点列表:")
    for i, node in enumerate(result['data']['nodes']):
        print(f"  {i+1}. {node['id']} - {node['label']} (学科: {node['discipline']})")
    
    print("\n边列表:")
    for i, edge in enumerate(result['data']['edges']):
        print(f"  {i+1}. {edge['source']} -> {edge['target']} (权重: {edge['weight']})")
    
    # 验证边的正确性
    print("\n验证边连接:")
    node_ids = {node['id'] for node in result['data']['nodes']}
    center_id = result['data']['nodes'][0]['id']
    
    invalid_edges = []
    for edge in result['data']['edges']:
        if edge['source'] not in node_ids:
            invalid_edges.append(f"source {edge['source']} 不存在")
        if edge['target'] not in node_ids:
            invalid_edges.append(f"target {edge['target']} 不存在")
        if edge['source'] != center_id:
            invalid_edges.append(f"source {edge['source']} 不是中心节点 {center_id}")
    
    if invalid_edges:
        print("❌ 发现无效边:")
        for err in invalid_edges:
            print(f"  - {err}")
    else:
        print("✅ 所有边都有效，且都从中心节点出发")

if __name__ == "__main__":
    asyncio.run(test_discover())
