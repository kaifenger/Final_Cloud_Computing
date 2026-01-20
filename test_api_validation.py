"""测试API验证脚本"""
import requests
import json

print('=' * 60)
print('测试1: 验证Wikipedia API是否真实调用')
print('=' * 60)

# 测试1: 量子计算
print('\n【测试概念: 量子计算】')
r = requests.post('http://localhost:8888/api/v1/discover', 
    json={'concept': '量子计算', 'depth': 1, 'max_concepts': 10}, 
    timeout=120)
data = r.json()
nodes = data.get('data', {}).get('nodes', [])
print(f'返回节点数: {len(nodes)}')
for i, node in enumerate(nodes[:3]):
    print(f'\n{i+1}. {node.get("label")}')
    print(f'   来源: {node.get("source")}')
    print(f'   定义: {node.get("definition", "")[:100]}...')

print('\n' + '=' * 60)
print('测试2: 非学科概念处理（笨蛋、爱情）')
print('=' * 60)

# 测试2: 笨蛋
print('\n【测试概念: 笨蛋】')
r = requests.post('http://localhost:8888/api/v1/discover', 
    json={'concept': '笨蛋', 'depth': 1, 'max_concepts': 10}, 
    timeout=120)
data = r.json()
nodes = data.get('data', {}).get('nodes', [])
print(f'返回节点数: {len(nodes)}')
if nodes:
    print(f'首节点: {nodes[0].get("label")} - {nodes[0].get("source")}')
    print(f'定义: {nodes[0].get("definition", "")[:100]}...')

# 测试3: 爱情
print('\n【测试概念: 爱情】')
r = requests.post('http://localhost:8888/api/v1/discover', 
    json={'concept': '爱情', 'depth': 1, 'max_concepts': 10}, 
    timeout=120)
data = r.json()
nodes = data.get('data', {}).get('nodes', [])
print(f'返回节点数: {len(nodes)}')
if nodes:
    print(f'首节点: {nodes[0].get("label")} - {nodes[0].get("source")}')
    print(f'定义: {nodes[0].get("definition", "")[:100]}...')

print('\n' + '=' * 60)
print('测试3: 节点展开逻辑')
print('=' * 60)

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
new_nodes = data.get('data', {}).get('nodes', [])
new_edges = data.get('data', {}).get('edges', [])
print(f'新增节点数: {len(new_nodes)}')
print(f'新增边数: {len(new_edges)}')

for i, node in enumerate(new_nodes):
    print(f'\n{i+1}. {node.get("label")}')
    print(f'   学科: {node.get("discipline")}')
    print(f'   来源: {node.get("source")}')

if new_edges:
    print('\n边关系:')
    for edge in new_edges[:3]:
        print(f'  {edge.get("source")} -> {edge.get("target")} ({edge.get("relation")})')

print('\n' + '=' * 60)
print('测试完成')
print('=' * 60)
