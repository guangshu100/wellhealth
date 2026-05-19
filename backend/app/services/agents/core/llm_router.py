"""
LLM 路由器
根据 Agent 的 LLM 配置选择正确的 LLM Provider
"""

import logging
from typing import Dict, Optional
from app.services.agents.core.agent_definition import AgentLLMConfig, AgentDefinition
from app.services.llm_client import LLMClient, get_llm_client_by_provider
from app.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    LLM 路由器
    根据 Agent 配置选择正确的 LLM
    """

    _provider_clients: Dict[str, LLMClient] = {}

    def __init__(self):
        self._init_default_clients()

    def _init_default_clients(self):
        """初始化默认的 LLM 客户端"""
        providers = [
            settings.LLM_PROVIDER,
            "openai",
            "anthropic",
            "siliconflow",
            "ollama",
            "dashscope",
        ]
        for provider in set(providers):
            if provider and provider != "default":
                try:
                    self._provider_clients[provider] = get_llm_client_by_provider(provider)
                    logger.info(f"Initialized LLM client for provider: {provider}")
                except Exception as e:
                    logger.warning(f"Failed to initialize provider {provider}: {e}")

    def get_client(self, llm_config: AgentLLMConfig) -> LLMClient:
        """
        根据配置获取 LLM 客户端

        Args:
            llm_config: Agent 的 LLM 配置

        Returns:
            LLMClient 实例
        """
        provider = llm_config.provider if llm_config else "default"

        if provider == "default":
            return get_llm_client_by_provider()

        if provider not in self._provider_clients:
            try:
                self._provider_clients[provider] = get_llm_client_by_provider(provider)
            except Exception as e:
                logger.warning(f"Failed to get provider {provider}: {e}, using default")
                return get_llm_client_by_provider()

        return self._provider_clients[provider]

    def get_client_for_agent(self, agent: AgentDefinition) -> LLMClient:
        """根据 Agent 定义获取 LLM 客户端"""
        return self.get_client(agent.llm_config)

    async def route_chat(
        self,
        agent: AgentDefinition,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        根据 Agent 配置路由聊天请求

        Args:
            agent: Agent 定义
            messages: 消息列表
            temperature: 温度参数（覆盖配置）
            max_tokens: 最大 token 数（覆盖配置）

        Returns:
            AI 响应文本
        """
        client = self.get_client_for_agent(agent)

        temp = temperature if temperature is not None else agent.llm_config.temperature
        tokens = max_tokens if max_tokens is not None else agent.llm_config.max_tokens

        logger.info(f"Routing chat to {agent.llm_config.provider}/{agent.llm_config.model}")
        return await client.chat(messages, temperature=temp, max_tokens=tokens)

    async def route_chat_with_system(
        self,
        agent: AgentDefinition,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        根据 Agent 配置路由带系统提示的聊天请求
        """
        client = self.get_client_for_agent(agent)

        temp = temperature if temperature is not None else agent.llm_config.temperature
        tokens = max_tokens if max_tokens is not None else agent.llm_config.max_tokens

        logger.info(
            f"Routing chat_with_system to {agent.llm_config.provider}/{agent.llm_config.model}"
        )
        return await client.chat_with_system(
            system_prompt, user_message, temperature=temp, max_tokens=tokens
        )

    async def route_chat_with_image(
        self,
        agent: AgentDefinition,
        image_base64: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        根据 Agent 配置路由图像聊天请求
        """
        client = self.get_client_for_agent(agent)

        temp = temperature if temperature is not None else agent.llm_config.temperature
        tokens = max_tokens if max_tokens is not None else agent.llm_config.max_tokens

        logger.info(
            f"Routing chat_with_image to {agent.llm_config.provider}/{agent.llm_config.model}"
        )
        return await client.chat_with_image(
            image_base64, prompt, temperature=temp, max_tokens=tokens
        )

    async def route_with_fallback(
        self,
        agent: AgentDefinition,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        带降级策略的路由
        如果主 Provider 失败，尝试 fallback provider
        """
        try:
            return await self.route_chat(agent, messages, temperature, max_tokens)
        except Exception as primary_error:
            logger.warning(f"Primary provider failed: {primary_error}")

            if agent.llm_config.fallback_provider:
                fallback_config = AgentLLMConfig(
                    provider=agent.llm_config.fallback_provider,
                    model=agent.llm_config.fallback_model or "default",
                    temperature=agent.llm_config.temperature,
                    max_tokens=agent.llm_config.max_tokens,
                )
                try:
                    client = self.get_client(fallback_config)
                    temp = temperature if temperature is not None else fallback_config.temperature
                    tokens = max_tokens if max_tokens is not None else fallback_config.max_tokens
                    logger.info(
                        f"Falling back to {fallback_config.provider}/{fallback_config.model}"
                    )
                    return await client.chat(messages, temperature=temp, max_tokens=tokens)
                except Exception as fallback_error:
                    logger.error(f"Fallback provider also failed: {fallback_error}")

            raise primary_error

    def get_available_providers(self) -> Dict[str, str]:
        """获取可用的 Provider 列表"""
        return {
            "openai": "OpenAI GPT",
            "anthropic": "Anthropic Claude",
            "siliconflow": "SiliconFlow",
            "ollama": "Ollama (本地)",
            "dashscope": "阿里云通义",
        }


# 全局单例
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取 LLM 路由器单例"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
