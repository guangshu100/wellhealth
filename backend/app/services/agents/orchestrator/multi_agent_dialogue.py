"""
多 Agent 对话管理器
支持多轮 Agent 对话、Agent 间通信、会诊模式
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from app.services.agents.core.agent_definition import AgentDefinition
from app.services.agents.core.agent_loader import EnhancedAgentLoader
from app.services.agents.core.agent_executor import (
    EnhancedAgentExecutor,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class DialogueMode(str, Enum):
    """对话模式"""

    SINGLE = "single"  # 单 Agent
    CONSULTATION = "consultation"  # 会诊模式
    DEBATE = "debate"  # 辩论模式
    COLLABORATION = "collaboration"  # 协作模式


@dataclass
class AgentMessage:
    """Agent 消息"""

    sender: str
    receiver: Optional[str]
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueTurn:
    """对话回合"""

    turn_number: int
    agent: str
    message: str
    response: str
    context_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsultationResult:
    """会诊结果"""

    primary_agent: str
    participating_agents: List[str]
    consensus: str
    disagreements: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiAgentDialogueManager:
    """
    多 Agent 对话管理器
    支持多种对话模式
    """

    def __init__(
        self,
        agents_dir: Optional[str] = None,
        executor: Optional[EnhancedAgentExecutor] = None,
    ):
        self.loader = EnhancedAgentLoader(agents_dir)
        self.executor = executor or EnhancedAgentExecutor(agents_dir)
        self._dialogue_history: Dict[str, List[DialogueTurn]] = {}

    async def multi_agent_consultation(
        self,
        query: str,
        agents: List[str],
        patient_context: Optional[Dict[str, Any]] = None,
        rounds: int = 2,
    ) -> Dict[str, Any]:
        """
        多 Agent 会诊

        Args:
            query: 用户问题
            agents: 参与的 Agent 列表
            patient_context: 患者上下文
            rounds: 讨论轮数

        Returns:
            会诊结果
        """
        if patient_context is None:
            patient_context = {}

        responses = {}
        session_id = f"consultation_{'_'.join(agents)}"

        for agent_type in agents:
            result = await self.executor.execute(
                agent_type=agent_type,
                messages=[{"role": "user", "content": query}],
            )
            responses[agent_type] = {
                "response": result.response,
                "status": result.status.value,
                "quality_passed": result.quality_result.passed if result.quality_result else None,
            }

        consensus, disagreements = self._analyze_responses(list(responses.values()))

        return {
            "success": True,
            "query": query,
            "primary_agent": agents[0] if agents else "",
            "participating_agents": agents,
            "responses": responses,
            "consensus": consensus,
            "disagreements": disagreements,
            "recommendations": self._extract_recommendations(consensus, responses),
            "patient_context": patient_context,
        }

    async def debate(
        self,
        topic: str,
        agents: List[str],
        moderator_type: str = "general",
    ) -> Dict[str, Any]:
        """
        Agent 辩论模式

        Args:
            topic: 辩论主题
            agents: 辩论 Agent
            moderator_type: 主持人 Agent 类型

        Returns:
            辩论结果
        """
        turns = []
        current_stance = topic

        for i in range(len(agents)):
            agent = agents[i]
            result = await self.executor.execute(
                agent_type=agent,
                messages=[
                    {"role": "system", "content": f"请就以下话题发表观点：{current_stance}"},
                    {"role": "user", "content": f"请分享你的专业观点"},
                ],
            )

            turns.append(
                DialogueTurn(
                    turn_number=i + 1,
                    agent=agent,
                    message=current_stance,
                    response=result.response,
                )
            )

            current_stance = f"基于{agent}的观点：{result.response}"

        moderator_result = await self.executor.execute(
            agent_type=moderator_type,
            messages=[
                {
                    "role": "user",
                    "content": f"请总结以下辩论并给出结论：\n\n"
                    + "\n\n".join(f"Agent {t.agent}: {t.response}" for t in turns),
                }
            ],
        )

        return {
            "success": True,
            "topic": topic,
            "agents": agents,
            "turns": [{"agent": t.agent, "response": t.response} for t in turns],
            "moderator_summary": moderator_result.response,
        }

    async def collaboration(
        self,
        task: str,
        agents: List[str],
        task_type: str = "analysis",
    ) -> Dict[str, Any]:
        """
        Agent 协作模式

        Args:
            task: 协作任务
            agents: 参与 Agent
            task_type: 任务类型

        Returns:
            协作结果
        """
        context = {"task": task, "intermediate_results": []}
        current_task = task

        for i, agent in enumerate(agents):
            result = await self.executor.execute(
                agent_type=agent,
                messages=[
                    {
                        "role": "system",
                        "content": f"你是 {agent} Agent，负责完成协作任务的第 {i + 1} 步。",
                    },
                    {"role": "user", "content": current_task},
                ],
            )

            context["intermediate_results"].append({"agent": agent, "result": result.response})

            if i < len(agents) - 1:
                current_task = f"基于 {agent} 的输出 ({result.response})，请继续完成下一步任务。"

        return {
            "success": True,
            "task": task,
            "agents": agents,
            "final_output": context["intermediate_results"][-1]["result"]
            if context["intermediate_results"]
            else "",
            "intermediate_results": context["intermediate_results"],
        }

    async def multi_turn_dialogue(
        self,
        agent_type: str,
        user_message: str,
        session_id: str,
        history_limit: int = 10,
    ) -> Dict[str, Any]:
        """
        多轮对话

        Args:
            agent_type: Agent 类型
            user_message: 用户消息
            session_id: 会话 ID
            history_limit: 历史消息限制

        Returns:
            对话结果
        """
        if session_id not in self._dialogue_history:
            self._dialogue_history[session_id] = []

        history = self._dialogue_history[session_id][-history_limit:]

        messages = []
        for turn in history:
            messages.append({"role": "assistant", "content": turn.response})
        messages.append({"role": "user", "content": user_message})

        result = await self.executor.execute(
            agent_type=agent_type,
            messages=messages,
        )

        turn = DialogueTurn(
            turn_number=len(history) + 1,
            agent=agent_type,
            message=user_message,
            response=result.response,
        )
        self._dialogue_history[session_id].append(turn)

        return {
            "success": result.is_success(),
            "response": result.response,
            "turn_number": turn.turn_number,
            "history_length": len(self._dialogue_history[session_id]),
        }

    def _analyze_responses(self, responses: List[Dict[str, Any]]) -> tuple:
        """分析多个 Agent 响应的一致性和分歧"""
        if not responses:
            return "", []

        response_texts = [r.get("response", "") for r in responses]

        consensus = "\n\n".join(response_texts)

        return consensus, []

    def _extract_recommendations(self, consensus: str, responses: Dict[str, Dict]) -> List[str]:
        """从响应中提取建议"""
        recommendations = []

        for agent, data in responses.items():
            response = data.get("response", "")
            lines = response.split("\n")
            for line in lines:
                if "建议" in line or "推荐" in line or "可以考虑" in line:
                    recommendations.append(line.strip())

        return recommendations[:5]

    def clear_history(self, session_id: str):
        """清除会话历史"""
        if session_id in self._dialogue_history:
            del self._dialogue_history[session_id]

    def get_history(self, session_id: str) -> List[DialogueTurn]:
        """获取会话历史"""
        return self._dialogue_history.get(session_id, [])


class AgentCoordinator:
    """
    Agent 协调器
    负责 Agent 间的消息传递和状态同步
    """

    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._message_queue: Dict[str, List[AgentMessage]] = {}
        self._agent_states: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent: AgentDefinition, agent_type: str):
        """注册 Agent"""
        self._agents[agent_type] = agent
        self._agent_states[agent_type] = {"status": "idle", "context": {}}

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ):
        """发送消息"""
        message = AgentMessage(
            sender=from_agent,
            receiver=to_agent,
            content=content,
            metadata=metadata or {},
        )

        if to_agent not in self._message_queue:
            self._message_queue[to_agent] = []
        self._message_queue[to_agent].append(message)

    def get_messages(self, agent_type: str) -> List[AgentMessage]:
        """获取消息"""
        return self._message_queue.get(agent_type, [])

    def clear_messages(self, agent_type: str):
        """清除消息"""
        if agent_type in self._message_queue:
            self._message_queue[agent_type] = []

    def update_state(self, agent_type: str, state: Dict[str, Any]):
        """更新 Agent 状态"""
        if agent_type in self._agent_states:
            self._agent_states[agent_type].update(state)
        else:
            self._agent_states[agent_type] = state

    def get_state(self, agent_type: str) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return self._agent_states.get(agent_type, {})


# 全局对话管理器实例
_dialogue_manager: Optional[MultiAgentDialogueManager] = None


def get_dialogue_manager() -> MultiAgentDialogueManager:
    """获取对话管理器"""
    global _dialogue_manager
    if _dialogue_manager is None:
        _dialogue_manager = MultiAgentDialogueManager()
    return _dialogue_manager
