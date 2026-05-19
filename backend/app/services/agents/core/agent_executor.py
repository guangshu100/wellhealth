"""
增强的 Agent 执行器
支持质量门控和重试逻辑
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from app.services.agents.core.agent_definition import AgentDefinition
from app.services.agents.core.agent_loader import EnhancedAgentLoader
from app.services.agents.core.llm_router import get_llm_router
from app.services.agents.quality.quality_gate import QualityGate, ValidationResult

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class ExecutionContext:
    """执行上下文"""

    agent: AgentDefinition
    messages: List[Dict[str, str]]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """执行结果"""

    status: ExecutionStatus
    response: str
    agent_type: str
    quality_result: Optional[ValidationResult] = None
    execution_time: float = 0
    retry_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def is_success(self) -> bool:
        return self.status in (ExecutionStatus.PASSED, ExecutionStatus.SKIPPED)


class EnhancedAgentExecutor:
    """
    增强的 Agent 执行器
    支持质量门控、重试逻辑、多轮对话
    """

    def __init__(
        self,
        agents_dir: Optional[str] = None,
        enable_quality_gate: bool = True,
        max_retries: int = 2,
    ):
        self.loader = EnhancedAgentLoader(agents_dir)
        self.router = get_llm_router()
        self.quality_gate = QualityGate() if enable_quality_gate else None
        self.max_retries = max_retries

    async def execute(
        self,
        agent_type: str,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_quality_check: bool = True,
    ) -> ExecutionResult:
        """
        执行 Agent

        Args:
            agent_type: Agent 类型
            messages: 消息列表
            user_id: 用户 ID
            session_id: 会话 ID
            temperature: 温度参数
            max_tokens: 最大 token 数
            enable_quality_check: 是否启用质量检查

        Returns:
            ExecutionResult
        """
        import time

        start_time = time.time()
        agent = self.loader.load(agent_type)

        if not agent:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                response="",
                agent_type=agent_type,
                error=f"Agent not found: {agent_type}",
                execution_time=time.time() - start_time,
            )

        context = ExecutionContext(
            agent=agent,
            messages=messages,
            user_id=user_id,
            session_id=session_id,
        )

        retry_count = 0
        last_error = None

        while retry_count <= self.max_retries:
            try:
                response = await self._generate_response(agent, messages, temperature, max_tokens)

                execution_time = time.time() - start_time

                if enable_quality_check and self.quality_gate:
                    quality_result = await self.quality_gate.validate(
                        agent=agent,
                        response=response,
                        context=context,
                    )

                    if quality_result.passed:
                        return ExecutionResult(
                            status=ExecutionStatus.PASSED,
                            response=response,
                            agent_type=agent_type,
                            quality_result=quality_result,
                            execution_time=execution_time,
                            retry_count=retry_count,
                        )
                    else:
                        logger.warning(f"Quality check failed: {quality_result.reasons}")
                        if retry_count < self.max_retries:
                            retry_count += 1
                            messages = self._improve_messages(messages, response, quality_result)
                            continue
                        else:
                            return ExecutionResult(
                                status=ExecutionStatus.FAILED,
                                response=response,
                                agent_type=agent_type,
                                quality_result=quality_result,
                                execution_time=execution_time,
                                retry_count=retry_count,
                                error="Quality check failed after max retries",
                            )
                else:
                    return ExecutionResult(
                        status=ExecutionStatus.PASSED,
                        response=response,
                        agent_type=agent_type,
                        execution_time=execution_time,
                        retry_count=retry_count,
                    )

            except Exception as e:
                last_error = str(e)
                logger.error(f"Agent execution error: {e}")
                retry_count += 1
                if retry_count > self.max_retries:
                    break

        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            response="",
            agent_type=agent_type,
            execution_time=time.time() - start_time,
            retry_count=retry_count,
            error=last_error or "Max retries exceeded",
        )

    async def _generate_response(
        self,
        agent: AgentDefinition,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """生成响应"""
        if agent.system_prompt:
            system_messages = [{"role": "system", "content": agent.system_prompt}]
            all_messages = system_messages + messages
        else:
            all_messages = messages

        return await self.router.route_with_fallback(agent, all_messages, temperature, max_tokens)

    def _improve_messages(
        self,
        original_messages: List[Dict[str, str]],
        last_response: str,
        quality_result: ValidationResult,
    ) -> List[Dict[str, str]]:
        """根据质量反馈改进消息"""
        improvement_prompt = f"""请根据以下质量检查反馈，改进回答：

质量检查失败原因：
{chr(10).join(f"- {reason}" for reason in quality_result.reasons)}

之前的回答：
{last_response}

请生成一个改进后的回答。"""

        improved_messages = original_messages.copy()
        improved_messages.append({"role": "user", "content": improvement_prompt})
        return improved_messages

    async def execute_with_tools(
        self,
        agent_type: str,
        messages: List[Dict[str, str]],
        tools: List[Callable],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """使用工具执行 Agent"""
        agent = self.loader.load(agent_type)
        if not agent:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                response="",
                agent_type=agent_type,
                error=f"Agent not found: {agent_type}",
            )

        tool_map = {tool.__name__: tool for tool in tools}
        available_tools = [tool_map[t] for t in agent.tools if t in tool_map]

        if not available_tools:
            return await self.execute(agent_type, messages, user_id, session_id)

        for tool in available_tools:
            try:
                tool_result = await tool(messages)
                messages.append(
                    {"role": "system", "content": f"[TOOL: {tool.__name__}]\n{tool_result}"}
                )
            except Exception as tool_error:
                logger.warning(f"Tool {tool.__name__} failed: {tool_error}")

        return await self.execute(agent_type, messages, user_id, session_id)


# 全局单例
_executor: Optional[EnhancedAgentExecutor] = None


def get_executor() -> EnhancedAgentExecutor:
    """获取执行器单例"""
    global _executor
    if _executor is None:
        _executor = EnhancedAgentExecutor()
    return _executor
