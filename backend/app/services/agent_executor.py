"""
Agent执行器
负责Agent的实际执行、多Agent协作、会话管理
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.services.agent_manager import AgentType, AgentSelector, AgentDefinition, AgentLLMConfig
from app.services.llm_client import get_llm_client
from app.services.knowledge_base import knowledge_manager
from app.services.safety_checker import SafetyChecker, safety_evaluator

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """消息"""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool
    response: str
    agent_type: str
    sources: List[Dict] = field(default_factory=list)
    safety_result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class AgentContext:
    """Agent执行上下文"""

    patient_id: Optional[str] = None
    patient_context: Dict = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)


class AgentExecutor:
    """
    Agent执行器
    负责协调Agent选择、知识检索、LLM调用、安全检查
    """

    def __init__(self):
        self.selector = AgentSelector()
        self.safety_checker = SafetyChecker()

    async def execute(
        self, query: str, context: AgentContext = None, agent_type: str = None
    ) -> ExecutionResult:
        """
        执行Agent问答

        Args:
            query: 用户问题
            context: 执行上下文
            agent_type: 指定Agent类型，None则自动选择
        """
        if context is None:
            context = AgentContext()

        try:
            # 1. 选择Agent
            if agent_type is None or agent_type == "general":
                auto_selected = self.selector.select(
                    query, context.patient_context if context.patient_context else None
                )
                if auto_selected != "general":
                    agent_type = auto_selected
                    logger.info(f"[AgentExecutor] Auto-routed from general to {agent_type} for query: {query[:30]}...")

            # 2. 获取Agent定义
            agent_def = self.selector.get_agent_definition(agent_type)
            if agent_def is None:
                # 回退到general
                agent_def = self.selector.get_agent_definition("general")
                agent_type = "general"

            if agent_def is None:
                return ExecutionResult(
                    success=False,
                    response="抱歉，AI服务暂时不可用",
                    agent_type="system",
                    error="No available agent",
                )

            # 3. 检索知识
            sources = await knowledge_manager.search(query, top_k=5)

            # 4. 构建prompt
            system_prompt = await self._build_system_prompt(agent_def, context)
            user_message = await self._build_user_message(query, sources, context)

            # 5. 获取 Agent 的 LLM 配置
            llm_config = agent_def.llm_config

            # 6. 根据配置调用 LLM
            response = await self._call_llm_with_config(
                llm_config=llm_config,
                system_prompt=system_prompt,
                user_message=user_message,
            )

            # 7. 安全检查
            safety_result = self.safety_checker.check(response)

            # 7. 添加免责声明
            if not safety_result.safe or safety_result.level.value != "safe":
                response = self.safety_checker.add_disclaimer(response)
                safety_result = self.safety_checker.check(response)

            # 添加消息到上下文以支持上下文记忆
            context.messages.append(Message(role="user", content=query))
            context.messages.append(Message(role="assistant", content=response))

            return ExecutionResult(
                success=True,
                response=response,
                agent_type=agent_type,
                sources=[
                    {"title": s.get("title", ""), "content": s.get("content", "")} for s in sources
                ],
                safety_result={
                    "level": safety_result.level.value,
                    "violations": safety_result.violations,
                    "suggestions": safety_result.suggestions,
                },
            )

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                response="抱歉，处理您的请求时出现错误，请稍后重试",
                agent_type=agent_type or "system",
                error=str(e),
            )

    async def _build_system_prompt(self, agent_def: AgentDefinition, context: AgentContext) -> str:
        """构建系统提示"""
        prompt = agent_def.system_prompt

        # 添加患者上下文
        if context.patient_context:
            patient_info = context.patient_context
            context_info = "\n\n## 患者信息\n"

            if patient_info.get("name"):
                context_info += f"- 姓名: {patient_info['name']}\n"
            if patient_info.get("diseases"):
                context_info += f"- 疾病: {', '.join(patient_info['diseases'])}\n"
            if patient_info.get("medications"):
                context_info += f"- 用药: {', '.join(patient_info['medications'])}\n"
            if patient_info.get("allergies"):
                context_info += f"- 过敏史: {', '.join(patient_info['allergies'])}\n"

            prompt += context_info

        return prompt

    async def _build_user_message(
        self, query: str, sources: List[Dict], context: AgentContext
    ) -> str:
        """构建用户消息"""
        message = query

        # 添加对话历史（最近5轮）
        if context.messages:
            recent_messages = context.messages[-10:]  # 最多10条消息
            history_text = "\n".join(
                [
                    f"{'用户' if m.role == 'user' else '助手'}: {m.content[:200]}"
                    for m in recent_messages
                    if m.content
                ]
            )
            if history_text:
                message = f"""【对话历史】
{history_text}

【当前问题】
{query}"""

        # 添加参考知识
        if sources:
            context_text = "\n\n".join(
                [f"【{s.get('title', '')}】\n{s.get('content', '')}" for s in sources[:3]]
            )
            message = f"""【参考知识】
{context_text}

{message}"""

        return message

    def _is_error_response(self, response: str) -> bool:
        """检查响应是否是错误响应"""
        if not response:
            return True
        error_keywords = [
            "暂时不可用",
            "error",
            "failed",
            "timeout",
            "timed out",
            "服务不可用",
            "LLM服务",
        ]
        return any(keyword.lower() in response.lower() for keyword in error_keywords)

    async def _call_llm_with_config(
        self,
        llm_config: AgentLLMConfig,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """
        根据 Agent 的 LLM 配置调用对应的 LLM
        支持自动切换 fallback provider

        Args:
            llm_config: Agent 的 LLM 配置
            system_prompt: 系统提示词
            user_message: 用户消息

        Returns:
            LLM 响应
        """
        from app.services.llm_client import LLMClient

        provider = llm_config.provider
        model = llm_config.model
        api_key = getattr(llm_config, 'api_key', None)
        logger.info(f"[AgentExecutor] Using LLM provider: {provider}, model: {model}")

        # 尝试主 provider
        llm_client = LLMClient(provider=provider, model=model, api_key=api_key)
        response = await llm_client.chat_with_system(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
        )

        # 检查是否需要 fallback
        if self._is_error_response(response) and llm_config.fallback_provider:
            logger.warning(
                f"[AgentExecutor] Primary provider {provider} returned error, trying fallback"
            )
            logger.info(f"[AgentExecutor] Trying fallback provider: {llm_config.fallback_provider}")

            fallback_provider = llm_config.fallback_provider
            fallback_model = llm_config.fallback_model or model

            llm_client = LLMClient(provider=fallback_provider, model=fallback_model)
            response = await llm_client.chat_with_system(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )

            # 如果 fallback 也失败
            if self._is_error_response(response):
                logger.error(f"[AgentExecutor] Fallback provider {fallback_provider} also failed")
                return f"抱歉，AI服务暂时不可用。已尝试 {provider} 和 {fallback_provider}，均失败。"

        return response

    async def execute_with_rag(
        self, query: str, context: AgentContext = None, agent_type: str = None
    ) -> ExecutionResult:
        """
        使用RAG执行问答
        """
        if context is None:
            context = AgentContext()

        try:
            # 1. 选择Agent
            if agent_type is None or agent_type == "general":
                auto_selected = self.selector.select(
                    query, context.patient_context if context.patient_context else None
                )
                if auto_selected != "general":
                    agent_type = auto_selected
                    logger.info(f"[AgentExecutor.execute_with_rag] Auto-routed from general to {agent_type} for query: {query[:30]}...")

            # 2. 获取Agent定义
            agent_def = self.selector.get_agent_definition(agent_type)
            if agent_def is None:
                agent_def = self.selector.get_agent_definition("general")
                agent_type = "general"

            # 3. RAG检索+生成
            patient_context = context.patient_context if context.patient_context else None
            rag_result = await knowledge_manager.rag.query_with_rag(
                query=query, patient_context=patient_context, system_prompt=agent_def.system_prompt
            )

            response = rag_result["response"]
            sources = rag_result["sources"]

            # 4. 安全检查
            safety_result = self.safety_checker.check(response)

            # 5. 添加免责声明
            if not safety_result.safe:
                response = self.safety_checker.add_disclaimer(response)
                safety_result = self.safety_checker.check(response)

            return ExecutionResult(
                success=True,
                response=response,
                agent_type=agent_type,
                sources=[
                    {"title": s.get("title", ""), "content": s.get("content", "")} for s in sources
                ],
                safety_result={
                    "level": safety_result.level.value,
                    "violations": safety_result.violations,
                    "suggestions": safety_result.suggestions,
                },
            )

        except Exception as e:
            logger.error(f"RAG execution error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                response="抱歉，处理您的请求时出现错误",
                agent_type=agent_type or "system",
                error=str(e),
            )

    async def multi_agent_consultation(
        self, query: str, context: AgentContext = None, agent_types: List[str] = None
    ) -> List[ExecutionResult]:
        """
        多Agent会诊
        多个Agent同时回答，综合给出最佳答案
        """
        if context is None:
            context = AgentContext()

        if agent_types is None:
            # 自动选择多个相关Agent
            agent_types = self._select_multiple_agents(query)

        results = []
        for agent_type in agent_types:
            result = await self.execute(query, context, agent_type)
            results.append(result)

        # 综合结果
        return await self._merge_results(results, query)

    def _select_multiple_agents(self, query: str) -> List[str]:
        """选择多个相关Agent"""
        agents = []
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["血糖", "糖尿病", "胰岛素"]):
            agents.append("diabetes")
        if any(kw in query_lower for kw in ["血压", "高血压"]):
            agents.append("hypertension")
        if any(kw in query_lower for kw in ["饮食", "食物", "营养", "食谱"]):
            agents.append("nutrition")
        if any(kw in query_lower for kw in ["运动", "锻炼", "跑步", "步行"]):
            agents.append("coach")
        if any(kw in query_lower for kw in ["药", "用药", "服用", "二甲双胍", "阿司匹林"]):
            agents.append("medication")
        if any(kw in query_lower for kw in ["焦虑", "抑郁", "心理", "失眠", "情绪", "压力"]):
            agents.append("psychology")
        if any(kw in query_lower for kw in ["康复", "脑梗", "中风", "偏瘫", "功能恢复", "训练"]):
            agents.append("rehabilitation")
        if any(kw in query_lower for kw in ["认知", "记忆力", "健忘", "忘事", "老年痴呆", "阿尔茨海默", "记不住", "注意力"]):
            agents.append("cognitive")

        if not agents:
            agents.append("general")

        return agents

    async def _merge_results(
        self, results: List[ExecutionResult], query: str
    ) -> List[ExecutionResult]:
        """合并多Agent结果"""
        # 简单的合并策略：返回所有结果，让前端展示
        # 实际生产中可以进一步处理
        return results


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self._sessions: Dict[str, AgentContext] = {}

    def create_session(self, patient_id: str = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = AgentContext(patient_id=patient_id, session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[AgentContext]:
        """获取会话"""
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, context: AgentContext):
        """更新会话"""
        self._sessions[session_id] = context

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息"""
        if session_id in self._sessions:
            self._sessions[session_id].messages.append(Message(role=role, content=content))

    def get_history(self, session_id: str) -> List[Dict]:
        """获取历史消息"""
        if session_id not in self._sessions:
            return []

        return [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
            for m in self._sessions[session_id].messages
        ]


# 全局单例
agent_executor = AgentExecutor()
session_manager = SessionManager()


@dataclass
class DialogueTurn:
    """对话轮次"""

    turn_index: int
    speaker_agent: str
    speaker_name: str
    content: str
    target_agent: str = None
    target_name: str = None
    sources: List[Dict] = field(default_factory=list)


@dataclass
class DialogueResult:
    """对话结果"""

    success: bool
    dialogue_id: str
    query: str
    turns: List[DialogueTurn]
    summary: str = ""
    error: str = None


class AgentDialogueManager:
    """
    Agent对话管理器
    实现多个Agent之间的顺序对话
    """

    def __init__(self):
        self.selector = AgentSelector()
        self.executor = AgentExecutor()
        self._dialogues: Dict[str, List[DialogueTurn]] = {}

    async def start_dialogue(
        self, query: str, agent_types: List[str], context: AgentContext = None, max_turns: int = 3
    ) -> DialogueResult:
        """
        开始Agent对话

        Args:
            query: 用户问题
            agent_types: 参与对话的Agent类型列表
            context: 执行上下文
            max_turns: 最大对话轮次
        """
        if context is None:
            context = AgentContext()

        dialogue_id = str(uuid.uuid4())
        turns = []

        # 获取Agent名称映射
        agent_names = {}
        for agent_type in agent_types:
            agent_def = self.selector.get_agent_definition(agent_type)
            agent_names[agent_type] = agent_def.metadata.name if agent_def else agent_type

        # 第一轮：所有Agent回答用户问题
        first_turn_content = f"用户问题：{query}\n\n请各专家给出专业建议。"

        for i, agent_type in enumerate(agent_types):
            # 获取Agent定义
            agent_def = self.selector.get_agent_definition(agent_type)
            if agent_def is None:
                continue

            # 执行Agent
            result = await self.executor.execute(query, context, agent_type)

            turn = DialogueTurn(
                turn_index=0,
                speaker_agent=agent_type,
                speaker_name=agent_names[agent_type],
                content=result.response,
                sources=result.sources,
            )
            turns.append(turn)

        # 保存到对话历史
        self._dialogues[dialogue_id] = turns

        # 后续轮次：Agent之间讨论
        for turn_idx in range(1, max_turns):
            # 轮流让Agent回应其他Agent的观点
            for i, agent_type in enumerate(agent_types):
                agent_def = self.selector.get_agent_definition(agent_type)
                if agent_def is None:
                    continue

                # 构建上下文：之前的对话
                dialogue_history = self._format_dialogue_history(turns)

                # 让Agent回应
                prompt = f"""你是一位专业的医疗健康顾问。请阅读以下多位专家的讨论，然后从你的专业角度给出你的观点和建议。

讨论历史：
{dialogue_history}

请给出你的专业建议和观点。"""

                result = await self._call_agent(prompt, context, agent_type)

                if result.success:
                    turn = DialogueTurn(
                        turn_index=turn_idx,
                        speaker_agent=agent_type,
                        speaker_name=agent_names[agent_type],
                        content=result.response,
                        sources=result.sources,
                    )
                    turns.append(turn)

            # 更新对话历史
            self._dialogues[dialogue_id] = turns

        # 生成总结
        summary = await self._generate_summary(query, turns, agent_names)

        return DialogueResult(
            success=True, dialogue_id=dialogue_id, query=query, turns=turns, summary=summary
        )

    async def _call_agent(
        self, prompt: str, context: AgentContext, agent_type: str
    ) -> ExecutionResult:
        """调用单个Agent"""
        try:
            agent_def = self.selector.get_agent_definition(agent_type)
            if agent_def is None:
                return ExecutionResult(success=False, response="", agent_type=agent_type)

            # 检索知识
            sources = await knowledge_manager.search(prompt, top_k=3)

            # 构建消息
            system_prompt = await self.executor._build_system_prompt(agent_def, context)
            user_message = prompt

            # 调用LLM
            response = await get_llm_client().chat_with_system(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.7,
                max_tokens=3000,
            )

            return ExecutionResult(
                success=True,
                response=response,
                agent_type=agent_type,
                sources=[
                    {"title": s.get("title", ""), "content": s.get("content", "")} for s in sources
                ],
            )
        except Exception as e:
            logger.error(f"Agent call error: {e}")
            return ExecutionResult(success=False, response="", agent_type=agent_type, error=str(e))

    def _format_dialogue_history(self, turns: List[DialogueTurn]) -> str:
        """格式化对话历史"""
        history = []
        for turn in turns:
            history.append(f"【{turn.speaker_name}】{turn.content}")
        return "\n\n".join(history)

    async def _generate_summary(
        self, query: str, turns: List[DialogueTurn], agent_names: Dict[str, str]
    ) -> str:
        """生成对话总结"""
        try:
            # 提取各Agent核心观点摘要（而非完整回答），避免prompt过长导致模型乱码
            turn_summaries = []
            for turn in turns:
                content = turn.content
                if len(content) > 500:
                    content = content[:500] + "..."
                turn_summaries.append(f"【{turn.speaker_name}】: {content}")
            dialogue_text = "\n\n".join(turn_summaries)

            summary_prompt = f"""用户问题：{query}

以下是各位专家的核心意见摘要：

{dialogue_text}

请综合以上专家意见，输出一份结构清晰的综合建议。要求：
1. 按类别组织：饮食调整、运动计划、药物调整、监测随访、注意事项
2. 每个类别列出2-3条关键建议，简洁明了
3. 药物名称、数值等关键信息必须准确完整
4. 最后附上温馨提醒

请直接输出综合建议："""

            summary = await get_llm_client().chat_with_system(
                system_prompt="你是一位专业健康顾问，请综合多位专家意见，输出准确、简洁、结构化的健康建议。注意：药物名称和数值必须准确无误，不要编造或篡改。",
                user_message=summary_prompt,
                temperature=0.3,
                max_tokens=3000,
            )
            return summary
        except Exception as e:
            logger.warning(f"Summary generation error: {e}")
            return "感谢各位专家的建议。请根据个人情况选择最适合的方案。"

    def get_dialogue(self, dialogue_id: str) -> List[DialogueTurn]:
        """获取对话历史"""
        return self._dialogues.get(dialogue_id, [])


# 全局单例
agent_dialogue_manager = AgentDialogueManager()
