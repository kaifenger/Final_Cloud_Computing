"""测试节点展开功能"""
import requests
import json

print('=' * 60)
print('测试节点展开逻辑')
print('=' * 60)

# 测试1: 机器学习
print('\n【展开节点: 机器学习】')
r = requests.post('http://localhost:8888/api/v1/expand',
    json={
        'node_id': 'ml_test', 
        'node_label': '机器学习', 
        'existing_nodes': [],
        'max_new_nodes': 5
    }, 
    timeout=60)
data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))

# 测试2: 量子计算
print('\n' + '=' * 60)
print('【展开节点: 量子计算】')
r = requests.post('http://localhost:8888/api/v1/expand',
    json={
        'node_id': 'qc_test', 
        'node_label': '量子计算', 
        'existing_nodes': [],
        'max_new_nodes': 5
    }, 
    timeout=60)
data = r.json()
new_nodes = data.get('data', {}).get('nodes', [])
new_edges = data.get('data', {}).get('edges', [])
print(f'新增节点数: {len(new_nodes)}')
for i, node in enumerate(new_nodes):
    print(f'\n{i+1}. {node.get("label")}')
    print(f'   学科: {node.get("discipline")}')
    print(f'   定义: {node.get("definition", "")[:80]}...')

if new_edges:
    print('\n边关系:')
    for edge in new_edges:
        print(f'  {edge.get("relation")}')

print('\n' + '=' * 60)
print('测试完成')
print('=' * 60)
