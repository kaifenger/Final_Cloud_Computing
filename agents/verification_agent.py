"""知识校验Agent"""

import logging
from typing import List, Dict, Any, Optional
from prompts.verification_prompts import VerificationPrompt
from shared.constants import AgentConfig
from agents.llm_client import get_llm_client
from agents.utils import validate_json_output

logger = logging.getLogger(__name__)


class VerificationAgent:
    """知识校验Agent"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_generator = VerificationPrompt()
        self.credibility_threshold = AgentConfig.CREDIBILITY_THRESHOLD
    
    async def verify_relation(
        self,
        concept_a: str,
        concept_b: str,
        claimed_relation: str,
        strength: float
    ) -> Dict[str, Any]:
        """
        验证概念关联的准确性
        
        Args:
            concept_a: 概念A
            concept_b: 概念B
            claimed_relation: 声称的关联
            strength: 声称的关联强度
            
        Returns:
            验证结果
        """
        logger.info(f"Verifying relation: {concept_a} -> {concept_b}")
        
        try:
            # 生成验证Prompt
            prompt = self.prompt_generator.get_verification_prompt(
                concept_a=concept_a,
                concept_b=concept_b,
                claimed_relation=claimed_relation,
                strength=strength
            )
            
            # 调用LLM
            response = await self.llm_client.call_json(
                prompt=prompt,
                system_role="你是一个严谨的知识验证专家，负责核查信息的准确性。"
            )
            
            # 提取验证结果
            credibility_score = response.get('credibility_score', 0.0)
            is_valid = credibility_score >= self.credibility_threshold
            
            result = {
                "concept_a": concept_a,
                "concept_b": concept_b,
                "credibility_score": credibility_score,
                "is_valid": is_valid,
                "evidence": response.get('evidence', []),
                "logical_reasoning": response.get('logical_reasoning', ''),
                "warnings": response.get('warnings', [])
            }
            
            # 如果可信度低，添加警告
            if not is_valid:
                if not result['warnings']:
                    result['warnings'] = []
                result['warnings'].append(
                    f"可信度 ({credibility_score:.2f}) 低于阈值 ({self.credibility_threshold})"
                )
            
            logger.info(f"Verification result: credibility={credibility_score:.2f}, valid={is_valid}")
            
            return result
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise
    
    async def batch_verify(
        self,
        relations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量验证概念关联
        
        Args:
            relations: 待验证的关系列表
            
        Returns:
            验证结果列表
        """
        logger.info(f"Batch verifying {len(relations)} relations")
        
        try:
            # 生成批量验证Prompt
            prompt = self.prompt_generator.get_batch_verification_prompt(relations)
            
            # 调用LLM
            response = await self.llm_client.call_json(
                prompt=prompt,
                system_role="你是一个严谨的知识验证专家。"
            )
            
            # 确保响应是列表
            if not isinstance(response, list):
                response = [response]
            
            # 处理验证结果
            results = []
            for item in response:
                credibility_score = item.get('credibility_score', 0.0)
                is_valid = credibility_score >= self.credibility_threshold
                
                results.append({
                    "index": item.get('index', 0),
                    "concept_a": item.get('concept_a', ''),
                    "concept_b": item.get('concept_b', ''),
                    "credibility_score": credibility_score,
                    "is_valid": is_valid,
                    "quick_reasoning": item.get('quick_reasoning', ''),
                    "warnings": item.get('warnings', [])
                })
            
            verified_count = sum(1 for r in results if r['is_valid'])
            logger.info(f"Batch verification complete: {verified_count}/{len(results)} passed")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch verification failed: {str(e)}")
            raise
    
    async def verify_concepts(
        self,
        concepts: List[Dict[str, Any]],
        source_concept: str
    ) -> List[Dict[str, Any]]:
        """
        验证发现的概念列表
        
        Args:
            concepts: 概念列表
            source_concept: 源概念
            
        Returns:
            验证后的概念列表（可信度评分）
        """
        logger.info(f"Verifying {len(concepts)} concepts")
        
        verified_concepts = []
        
        for concept in concepts:
            try:
                concept_name = concept.get('concept_name', '')
                reasoning = concept.get('reasoning', '')
                strength = concept.get('strength', 0.5)
                
                # 验证关联
                verification = await self.verify_relation(
                    concept_a=source_concept,
                    concept_b=concept_name,
                    claimed_relation=reasoning,
                    strength=strength
                )
                
                # 更新可信度
                concept['credibility'] = verification['credibility_score']
                concept['verification'] = {
                    "is_valid": verification['is_valid'],
                    "evidence": verification['evidence'],
                    "warnings": verification['warnings']
                }
                
                # 只保留有效的概念
                if verification['is_valid']:
                    verified_concepts.append(concept)
                else:
                    logger.warning(f"Concept filtered: {concept_name} (credibility={verification['credibility_score']:.2f})")
                
            except Exception as e:
                logger.error(f"Failed to verify concept {concept.get('concept_name')}: {str(e)}")
                continue
        
        logger.info(f"Verification complete: {len(verified_concepts)}/{len(concepts)} passed")
        
        return verified_concepts
    
    async def check_fact(self, statement: str) -> Dict[str, Any]:
        """
        事实核查
        
        Args:
            statement: 待核查的陈述
            
        Returns:
            核查结果
        """
        logger.info(f"Checking fact: {statement[:100]}...")
        
        try:
            prompt = self.prompt_generator.get_fact_check_prompt(statement)
            
            response = await self.llm_client.call_json(
                prompt=prompt,
                system_role="你是一个事实核查专家。"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Fact check failed: {str(e)}")
            raise
