"""LLM API调用模块"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from shared.error_codes import ErrorCode
from shared.constants import AgentConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端（支持OpenRouter + Gemini 3 Pro）"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "google/gemini-3-pro-preview",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = 60,
        base_url: Optional[str] = None,
        enable_reasoning: bool = True
    ):
        """
        初始化LLM客户端
        
        Args:
            api_key: OpenRouter API密钥
            model: 模型名称（默认Gemini 3 Pro）
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）
            base_url: API base URL（默认OpenRouter）
            enable_reasoning: 是否启用推理模式
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set, LLM calls will fail")
        
        self.model = model or os.getenv("LLM_MODEL", "google/gemini-3-pro-preview")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.enable_reasoning = enable_reasoning
        
        # 使用OpenRouter作为默认base_url
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        # 初始化OpenAI客户端（兼容OpenRouter）
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"LLM Client initialized: model={self.model}, base_url={self.base_url}")
        else:
            self.client = None
    
    async def call_with_retry(
        self,
        prompt: str,
        system_role: str = "You are a helpful assistant.",
        max_retries: int = AgentConfig.MAX_RETRIES,
        messages_history: Optional[List[Dict]] = None
    ) -> str:
        """
        调用LLM（带重试机制和推理支持）
        
        Args:
            prompt: 用户提示
            system_role: 系统角色
            max_retries: 最大重试次数
            messages_history: 消息历史（用于多轮对话）
            
        Returns:
            LLM响应文本
            
        Raises:
            Exception: LLM调用失败
        """
        if not self.client:
            raise ValueError("LLM client not initialized. Please set OPENROUTER_API_KEY.")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling LLM (attempt {attempt + 1}/{max_retries}, model={self.model})")
                
                # 构建消息列表
                if messages_history:
                    messages = messages_history.copy()
                    messages.append({"role": "user", "content": prompt})
                else:
                    messages = [
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": prompt}
                    ]
                
                # 构建请求参数
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                
                # Gemini 3 Pro支持推理模式
                if self.enable_reasoning and "gemini-3-pro" in self.model.lower():
                    request_params["extra_body"] = {"reasoning": {"enabled": True}}
                
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(**request_params),
                    timeout=self.timeout
                )
                
                content = response.choices[0].message.content
                logger.info(f"LLM response received ({len(content)} chars)")
                
                # 记录推理详情（如果有）
                if hasattr(response.choices[0].message, 'reasoning_details'):
                    logger.debug(f"Reasoning details: {response.choices[0].message.reasoning_details}")
                
                return content
                
            except asyncio.TimeoutError:
                logger.error(f"LLM timeout (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise Exception(ErrorCode.LLM_TIMEOUT)
                await asyncio.sleep(AgentConfig.RETRY_DELAY * (2 ** attempt))
                
            except Exception as e:
                logger.error(f"LLM API error: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(ErrorCode.LLM_API_ERROR)
                await asyncio.sleep(AgentConfig.RETRY_DELAY * (2 ** attempt))
        
        raise Exception(ErrorCode.LLM_API_ERROR)
    
    async def call_json(
        self,
        prompt: str,
        system_role: str = "You are a helpful assistant.",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        调用LLM并解析JSON响应
        
        Args:
            prompt: 用户提示
            system_role: 系统角色
            max_retries: 最大重试次数
            
        Returns:
            解析后的JSON对象
        """
        import json
        from agents.utils import validate_json_output
        
        response_text = await self.call_with_retry(
            prompt=prompt,
            system_role=system_role,
            max_retries=max_retries
        )
        
        try:
            return validate_json_output(response_text)
        except ValueError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            # 尝试让LLM修复JSON
            fix_prompt = f"""以下JSON格式有误，请修复并返回有效的JSON：

{response_text}

要求：
1. 只返回有效的JSON，不要包含任何其他文字
2. 确保所有引号、括号、逗号都正确
3. 不要使用markdown代码块"""
            
            fixed_response = await self.call_with_retry(
                prompt=fix_prompt,
                system_role="You are a JSON formatting expert.",
                max_retries=2
            )
            
            return validate_json_output(fixed_response)
    
    async def call_batch(
        self,
        prompts: List[str],
        system_role: str = "You are a helpful assistant."
    ) -> List[str]:
        """
        批量调用LLM
        
        Args:
            prompts: 提示列表
            system_role: 系统角色
            
        Returns:
            响应列表
        """
        tasks = [
            self.call_with_retry(prompt, system_role)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)


# 全局LLM客户端实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端实例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def set_llm_client(client: LLMClient):
    """设置全局LLM客户端实例"""
    global _llm_client
    _llm_client = client
