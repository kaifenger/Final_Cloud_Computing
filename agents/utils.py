"""Agent工具函数"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
            return None
        return wrapper
    return decorator


def validate_json_output(json_str: str) -> Dict[str, Any]:
    """
    验证并解析JSON输出
    
    Args:
        json_str: JSON字符串
        
    Returns:
        解析后的字典
        
    Raises:
        ValueError: JSON格式无效
    """
    try:
        # 尝试提取JSON块（处理Markdown格式）
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败，尝试自动修复: {str(e)}")
        
        # 尝试修复常见的JSON错误
        try:
            import re
            
            # 1. 修复无效的转义字符（如 \e, \a 等）
            # 这个正则匹配反斜杠后面不是合法转义字符的情况
            # 合法的JSON转义: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
            fixed_json = re.sub(
                r'\\(?!["\\/bfnrtu])',  # 匹配不是合法转义的反斜杠
                r'\\\\',  # 替换为双反斜杠（转义反斜杠本身）
                json_str
            )
            
            # 2. 如果还是失败，尝试更激进的修复
            try:
                data = json.loads(fixed_json)
                logger.info("✓ JSON自动修复成功（转义字符修复）")
                return data
            except json.JSONDecodeError:
                # 尝试使用json.loads的strict=False（如果可用）
                # 或者手动清理更多问题
                fixed_json2 = fixed_json.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                data = json.loads(fixed_json2)
                logger.info("✓ JSON自动修复成功（换行符修复）")
                return data
                
        except Exception as repair_error:
            # 如果修复失败，记录详细错误并抛出
            logger.error(f"JSON修复失败: {str(repair_error)}")
            logger.debug(f"原始JSON (前500字符): {json_str[:500]}")
            raise ValueError(f"Invalid JSON format: {str(e)}")


def extract_concepts_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从LLM响应中提取概念列表
    
    Args:
        response: LLM响应
        
    Returns:
        概念列表
    """
    # 如果response本身就是列表
    if isinstance(response, list):
        return response
    
    # 如果response是字典，尝试找到概念列表
    if isinstance(response, dict):
        # 尝试常见的键名
        for key in ['concepts', 'related_concepts', 'results', 'data']:
            if key in response and isinstance(response[key], list):
                return response[key]
        
        # 如果字典中有学科信息，包装成列表
        if 'discipline' in response and 'concept_name' in response:
            return [response]
    
    return []


def calculate_graph_metrics(nodes: List, edges: List) -> Dict[str, Any]:
    """
    计算图谱统计指标
    
    Args:
        nodes: 节点列表
        edges: 边列表
        
    Returns:
        统计指标字典
    """
    if not nodes:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "verified_nodes": 0,
            "avg_credibility": 0.0,
            "disciplines": []
        }
    
    # 计算平均可信度
    total_credibility = sum(
        node.get('credibility', 0.0) if isinstance(node, dict) else node.credibility
        for node in nodes
    )
    avg_credibility = total_credibility / len(nodes) if nodes else 0.0
    
    # 统计学科分布
    disciplines = set()
    for node in nodes:
        discipline = node.get('discipline') if isinstance(node, dict) else node.discipline
        if discipline:
            disciplines.add(discipline)
    
    # 统计验证通过的节点
    verified_count = sum(
        1 for node in nodes
        if (node.get('credibility', 0.0) if isinstance(node, dict) else node.credibility) >= 0.5
    )
    
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "verified_nodes": verified_count,
        "avg_credibility": round(avg_credibility, 2),
        "disciplines": list(disciplines)
    }


def merge_nodes(existing_nodes: List[Dict], new_nodes: List[Dict]) -> List[Dict]:
    """
    合并节点列表，去重并保留可信度更高的
    
    Args:
        existing_nodes: 已有节点
        new_nodes: 新节点
        
    Returns:
        合并后的节点列表
    """
    node_dict = {}
    
    # 添加已有节点
    for node in existing_nodes:
        node_id = node.get('id')
        if node_id:
            node_dict[node_id] = node
    
    # 添加新节点（如果ID重复，保留可信度更高的）
    for node in new_nodes:
        node_id = node.get('id')
        if not node_id:
            continue
        
        if node_id not in node_dict:
            node_dict[node_id] = node
        else:
            existing_cred = node_dict[node_id].get('credibility', 0.0)
            new_cred = node.get('credibility', 0.0)
            if new_cred > existing_cred:
                node_dict[node_id] = node
    
    return list(node_dict.values())


def merge_edges(existing_edges: List[Dict], new_edges: List[Dict]) -> List[Dict]:
    """
    合并边列表，去重并保留权重更高的
    
    Args:
        existing_edges: 已有边
        new_edges: 新边
        
    Returns:
        合并后的边列表
    """
    edge_dict = {}
    
    # 添加已有边
    for edge in existing_edges:
        edge_key = (edge.get('source'), edge.get('target'))
        if edge_key[0] and edge_key[1]:
            edge_dict[edge_key] = edge
    
    # 添加新边（如果重复，保留权重更高的）
    for edge in new_edges:
        edge_key = (edge.get('source'), edge.get('target'))
        if not edge_key[0] or not edge_key[1]:
            continue
        
        if edge_key not in edge_dict:
            edge_dict[edge_key] = edge
        else:
            existing_weight = edge_dict[edge_key].get('weight', 0.0)
            new_weight = edge.get('weight', 0.0)
            if new_weight > existing_weight:
                edge_dict[edge_key] = edge
    
    return list(edge_dict.values())


class ProgressTracker:
    """进度追踪器（用于WebSocket实时推送）"""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.current_stage = ""
        self.progress = 0
        self.callbacks = []
    
    def add_callback(self, callback):
        """添加进度回调"""
        self.callbacks.append(callback)
    
    async def update(self, stage: str, progress: int, message: str, **kwargs):
        """更新进度"""
        self.current_stage = stage
        self.progress = progress
        
        logger.info(f"[{self.request_id}] {stage}: {progress}% - {message}")
        
        # 调用所有回调
        for callback in self.callbacks:
            try:
                await callback({
                    "request_id": self.request_id,
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                    **kwargs
                })
            except Exception as e:
                logger.error(f"Progress callback failed: {str(e)}")
