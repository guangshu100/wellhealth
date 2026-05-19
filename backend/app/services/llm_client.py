"""
LLM客户端封装
支持多种LLM提供商: OpenAI, Anthropic, 阿里云通义等
"""

import json
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLMProvider抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """带系统提示的聊天"""
        pass

    @abstractmethod
    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """带图像的聊天（多模态）"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI Provider"""

    def __init__(self, model_override: str = None):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = model_override or settings.OPENAI_MODEL
        self._client = None

    def _get_client(self):
        """获取OpenAI客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.warning("openai package not installed")
                return None
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        client = self._get_client()
        if client is None:
            logger.error("OpenAI: client is None")
            return "LLM服务暂时不可用"

        logger.info(f"OpenAI request - model: {self.model}, messages count: {len(messages)}")

        try:
            full_content = ""
            continuation_messages = list(messages)
            max_continuations = 3

            for _ in range(max_continuations + 1):
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=continuation_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                choice = response.choices[0]
                full_content += choice.message.content or ""

                if choice.finish_reason != "length":
                    break

                logger.warning(f"OpenAI response truncated (finish_reason=length), continuing...")
                continuation_messages = list(messages)
                continuation_messages.append({"role": "assistant", "content": full_content})
                continuation_messages.append({"role": "user", "content": "请从上文断开处继续输出，保持格式和内容连贯，不要重复已有内容："})

            logger.info(f"OpenAI response received, total length: {len(full_content)}")
            return full_content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """带系统提示的聊天"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """带图像的聊天（多模态）- OpenAI/GPT-4V"""
        client = self._get_client()
        if client is None:
            logger.error("OpenAI: client is None")
            return "LLM服务暂时不可用"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            }
        ]

        logger.info(f"OpenAI vision request - model: {self.model}")

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            logger.info(f"OpenAI vision response received")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Vision API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Provider"""

    def __init__(self, model_override: str = None):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = model_override or settings.ANTHROPIC_MODEL
        self._client = None

    def _get_client(self):
        """获取Anthropic客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")
                return None
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        client = self._get_client()
        if client is None:
            logger.error("Anthropic: client is None")
            return "LLM服务暂时不可用"

        logger.info(f"Anthropic request - model: {self.model}, messages count: {len(messages)}")

        try:
            # 转换消息格式
            system_message = ""
            anthropic_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append(msg)

            response = await client.messages.create(
                model=self.model,
                system=system_message,
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """图像分析需要支持多模态的模型（如 GPT-4V）"""
        return "当前Provider不支持图像分析，请使用OpenAI或SiliconFlow"


class DashScopeProvider(LLMProvider):
    """阿里云通义Provider"""

    def __init__(self, model_override: str = None):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = model_override or settings.DASHSCOPE_MODEL
        self._client = None

    def _get_client(self):
        """获取DashScope客户端"""
        if self._client is None:
            try:
                import dashscope

                dashscope.api_key = self.api_key
                self._client = dashscope
            except ImportError:
                logger.warning("dashscope package not installed")
                return None
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        client = self._get_client()
        if client is None:
            logger.error("DashScope: client is None")
            return "LLM服务暂时不可用"

        logger.info(f"DashScope request - model: {self.model}, messages count: {len(messages)}")

        try:
            from dashscope import Generation

            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format="message",
                **kwargs,
            )

            if response.status_code == 200:
                logger.info(f"DashScope response received")
                return response.output.choices[0].message.content
            else:
                logger.error(f"DashScope API error: {response.code} - {response.message}")
                return f"抱歉，AI服务暂时不可用: {response.message}"
        except Exception as e:
            logger.error(f"DashScope API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """图像分析需要支持多模态的模型"""
        return "当前Provider不支持图像分析，请使用OpenAI或SiliconFlow"


class OllamaProvider(LLMProvider):
    """Ollama 本地大模型 Provider"""

    def __init__(self, model_override: str = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = model_override or settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._client = None

    def _get_client(self):
        """获取Ollama客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key="ollama",  # Ollama 不需要 API Key
                    timeout=self.timeout,
                )
            except ImportError:
                logger.warning("openai package not installed")
                return None
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        client = self._get_client()
        if client is None:
            logger.error("Ollama: client is None, check if Ollama is running")
            return "LLM服务暂时不可用，请检查Ollama是否启动"

        logger.info(f"Ollama request - model: {self.model}, messages count: {len(messages)}")

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            logger.info(f"Ollama response received")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """图像分析需要支持多模态的模型"""
        return "当前Provider不支持图像分析，请使用OpenAI或SiliconFlow"

    async def list_models(self) -> List[dict]:
        """获取本地可用的模型列表"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("models", [])
                    return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def check_health(self) -> bool:
        """检查Ollama服务是否健康"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False


class SiliconFlowProvider(LLMProvider):
    """硅基流动 Provider - OpenAI 兼容接口"""

    def __init__(self, model_override: str = None):
        self.api_key = settings.SILICONFLOW_API_KEY
        self.base_url = settings.SILICONFLOW_BASE_URL
        self.model = model_override or settings.SILICONFLOW_MODEL
        logger.info(f"SiliconFlowProvider init: model={self.model}")
        self._client = None

    def _get_client(self):
        """获取SiliconFlow客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                logger.warning("openai package not installed")
                return None
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        client = self._get_client()
        if client is None:
            logger.error("SiliconFlow: client is None, API key or package issue")
            return "LLM服务暂时不可用"

        logger.info(f"SiliconFlow request - model: {self.model}, messages count: {len(messages)}")
        if self.api_key:
            logger.info(f"SiliconFlow - API Key: {self.api_key[:10]}..., Base URL: {self.base_url}")
        else:
            logger.error("SiliconFlow - API Key is None or empty!")

        try:
            full_content = ""
            continuation_messages = list(messages)
            max_continuations = 3

            for _ in range(max_continuations + 1):
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=continuation_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                if not response.choices:
                    logger.error("SiliconFlow response has no choices")
                    return full_content if full_content else "抱歉，AI服务暂时没有返回有效响应"

                choice = response.choices[0]
                content = choice.message.content

                if content is None:
                    refusal = getattr(choice.message, 'refusal', None)
                    if refusal:
                        logger.warning(f"SiliconFlow refusal: {refusal}")
                        return full_content if full_content else f"抱歉，AI服务拒绝回答: {refusal}"
                    if not full_content:
                        return "抱歉，AI服务没有返回有效内容"
                    break

                full_content += content

                if choice.finish_reason != "length":
                    break

                logger.warning(f"SiliconFlow response truncated (finish_reason=length), continuing...")
                continuation_messages = list(messages)
                continuation_messages.append({"role": "assistant", "content": full_content})
                continuation_messages.append({"role": "user", "content": "请从上文断开处继续输出，保持格式和内容连贯，不要重复已有内容："})

            logger.info(f"SiliconFlow response received, total content length: {len(full_content)}")
            return full_content
        except Exception as e:
            logger.error(f"SiliconFlow API error: {e}")
            import traceback

            logger.error(f"SiliconFlow traceback: {traceback.format_exc()}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """带图像的聊天（多模态）- SiliconFlow"""
        client = self._get_client()
        if client is None:
            logger.error("SiliconFlow: client is None")
            return "LLM服务暂时不可用"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            }
        ]

        logger.info(f"SiliconFlow vision request - model: {self.model}")

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if not response.choices:
                return "抱歉，AI服务没有返回有效响应"
            content = response.choices[0].message.content
            if content is None:
                return "抱歉，AI服务没有返回有效内容"
            logger.info(f"SiliconFlow vision response received")
            return content
        except Exception as e:
            logger.error(f"SiliconFlow Vision API error: {e}")
            return f"抱歉，AI服务暂时不可用: {str(e)}"


class LLMClient:
    """LLM客户端工厂"""

    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "dashscope": DashScopeProvider,
        "ollama": OllamaProvider,
        "siliconflow": SiliconFlowProvider,
    }

    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        if provider is None:
            provider = settings.LLM_PROVIDER
        logger.info(f"LLMClient init with provider: {provider}, model: {model}")
        self.provider_name = provider
        self._provider = self._get_provider(provider, model, api_key)

    def _get_provider(self, provider: str, model: str = None, api_key: str = None) -> LLMProvider:
        """获取Provider实例"""
        provider_class = self._providers.get(provider)
        if provider_class is None:
            provider_class = OpenAIProvider
            logger.warning(f"Unknown provider: {provider}, using OpenAI as fallback")
        instance = provider_class(model_override=model) if model else provider_class()
        if api_key and hasattr(instance, 'api_key'):
            instance.api_key = api_key
            instance._client = None
        return instance

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """发送聊天请求"""
        logger.info(f"[LLMClient] Using provider: {self.provider_name}")
        return await self._provider.chat(messages, temperature, max_tokens, **kwargs)

    async def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """带系统提示的聊天"""
        logger.info(
            f"[LLMClient] chat_with_system called - provider: {self.provider_name}, model: {self._provider.model if self._provider else 'N/A'}"
        )
        return await self._provider.chat_with_system(
            system_prompt, user_message, temperature, max_tokens, **kwargs
        )

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """带图像的聊天（多模态）"""
        logger.info(f"[LLMClient] chat_with_image called - provider: {self.provider_name}")
        return await self._provider.chat_with_image(image_base64, prompt, temperature, max_tokens)

    async def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000, **kwargs
    ) -> str:
        """简单生成(不带对话历史)"""
        return await self.chat_with_system("", prompt, temperature, max_tokens, **kwargs)

    def get_provider_name(self) -> str:
        """获取当前Provider名称"""
        return self.provider_name

    async def check_health(self) -> dict:
        """检查LLM服务健康状态"""
        provider = self.provider_name

        if provider == "ollama":
            ollama_provider = self._provider
            is_healthy = await ollama_provider.check_health()
            models = []
            if is_healthy:
                try:
                    models = await ollama_provider.list_models()
                except Exception:
                    pass
            return {
                "provider": provider,
                "healthy": is_healthy,
                "model": ollama_provider.model,
                "models": models,
                "base_url": ollama_provider.base_url,
            }

        return {
            "provider": provider,
            "healthy": True,
            "model": getattr(self._provider, "model", "unknown"),
        }


# 全局单例 - 懒加载
_llm_client_instance = None


def get_llm_client() -> "LLMClient":
    """获取LLM客户端单例 - 懒加载"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance


# 保持向后兼容
llm_client = get_llm_client()


async def get_llm_client_by_provider(provider: str = None) -> "LLMClient":
    """获取指定Provider的LLM客户端"""
    return LLMClient(provider)
