"""
工作流编排器
基于 Agency-Agents 的 Pipeline 管理器
PM → Architect → Dev ↔ QA Loop → Integration
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from app.services.agents.core.agent_definition import AgentDefinition, AgentType
from app.services.agents.core.agent_loader import EnhancedAgentLoader
from app.services.agents.core.agent_executor import (
    EnhancedAgentExecutor,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline 阶段"""

    PM = "pm"  # 项目管理
    ARCHITECT = "architect"  # 架构设计
    DEV = "dev"  # 开发
    QA = "qa"  # 质量保证
    INTEGRATION = "integration"  # 集成
    DELIVERY = "delivery"  # 交付


@dataclass
class StageResult:
    """阶段结果"""

    stage: PipelineStage
    status: ExecutionStatus
    output: str
    agent_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Pipeline 配置"""

    stages: List[PipelineStage]
    max_iterations: int = 3
    quality_threshold: float = 0.7
    parallel_execution: bool = False


class WorkflowOrchestrator:
    """
    工作流编排器
    支持多阶段 Pipeline、循环迭代、并行执行
    """

    STAGE_AGENT_MAP = {
        PipelineStage.PM: "general",
        PipelineStage.ARCHITECT: "general",
        PipelineStage.DEV: "general",
        PipelineStage.QA: "general",
        PipelineStage.INTEGRATION: "general",
        PipelineStage.DELIVERY: "general",
    }

    def __init__(
        self,
        agents_dir: Optional[str] = None,
        executor: Optional[EnhancedAgentExecutor] = None,
    ):
        self.loader = EnhancedAgentLoader(agents_dir)
        self.executor = executor or EnhancedAgentExecutor(agents_dir)

    async def execute_pipeline(
        self,
        task: str,
        config: PipelineConfig,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行 Pipeline

        Args:
            task: 任务描述
            config: Pipeline 配置
            context: 上下文信息

        Returns:
            Pipeline 执行结果
        """
        if context is None:
            context = {}

        results = {}
        current_output = task
        iteration = 0

        while iteration < config.max_iterations:
            logger.info(f"Pipeline iteration {iteration + 1}/{config.max_iterations}")

            for stage in config.stages:
                result = await self._execute_stage(
                    stage=stage,
                    input_data=current_output,
                    context=context,
                )
                results[stage.value] = result

                if result.status == ExecutionStatus.FAILED:
                    logger.error(f"Stage {stage.value} failed")
                    return {
                        "success": False,
                        "results": results,
                        "error": f"Stage {stage.value} failed: {result.output}",
                    }

                if stage == PipelineStage.QA:
                    quality_score = self._extract_quality_score(result.output)
                    if quality_score < config.quality_threshold:
                        if iteration < config.max_iterations - 1:
                            logger.info(f"Quality below threshold, re-iterating")
                            current_output = self._extract_dev_output(results)
                            break
                        else:
                            logger.warning(f"Quality below threshold after max iterations")

                current_output = result.output

            iteration += 1

        return {
            "success": True,
            "results": results,
            "final_output": current_output,
            "iterations": iteration,
        }

    async def _execute_stage(
        self,
        stage: PipelineStage,
        input_data: str,
        context: Dict[str, Any],
    ) -> StageResult:
        """执行单个阶段"""
        agent_type = self.STAGE_AGENT_MAP.get(stage, "general")

        prompt = self._build_stage_prompt(stage, input_data, context)
        messages = [{"role": "user", "content": prompt}]

        try:
            execution_result = await self.executor.execute(
                agent_type=agent_type,
                messages=messages,
                enable_quality_check=False,
            )

            return StageResult(
                stage=stage,
                status=execution_result.status,
                output=execution_result.response,
                agent_type=agent_type,
                metadata={"execution_time": execution_result.execution_time},
            )
        except Exception as e:
            logger.error(f"Stage {stage.value} error: {e}")
            return StageResult(
                stage=stage,
                status=ExecutionStatus.FAILED,
                output=str(e),
            )

    def _build_stage_prompt(
        self,
        stage: PipelineStage,
        input_data: str,
        context: Dict[str, Any],
    ) -> str:
        """构建阶段提示词"""
        stage_prompts = {
            PipelineStage.PM: f"""作为项目经理，请分析以下任务并制定执行计划：

任务：{input_data}

请输出：
1. 任务分解
2. 执行顺序
3. 风险评估
4. 预期成果""",
            PipelineStage.ARCHITECT: f"""作为架构师，请设计解决方案：

任务：{input_data}

上下文：{context}

请输出：
1. 架构设计
2. 技术选型
3. 数据流程
4. 接口设计""",
            PipelineStage.DEV: f"""作为开发工程师，请实现解决方案：

任务：{input_data}

请输出：
1. 实现代码或步骤
2. 关键实现细节
3. 测试方案
4. 潜在问题""",
            PipelineStage.QA: f"""作为质量工程师，请验证解决方案：

任务：{input_data}

请验证：
1. 功能完整性
2. 代码质量
3. 安全性
4. 性能考虑

并给出质量评分 (0-1)""",
            PipelineStage.INTEGRATION: f"""作为集成工程师，请整合解决方案：

请整合之前的输出并确保一致性。""",
            PipelineStage.DELIVERY: f"""作为交付经理，请准备最终交付物：

请输出：
1. 最终方案
2. 使用说明
3. 维护建议
4. 后续跟进""",
        }

        return stage_prompts.get(stage, input_data)

    def _extract_quality_score(self, output: str) -> float:
        """从 QA 输出中提取质量分数"""
        import re

        patterns = [
            r"质量评分[:：]?\s*([0-9.]+)",
            r"评分[:：]?\s*([0-9.]+)",
            r"score[:：]?\s*([0-9.]+)",
            r"([0-9.]+)\s*/\s*1",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return 0.5

    def _extract_dev_output(self, results: Dict[str, StageResult]) -> str:
        """从结果中提取开发输出"""
        dev_result = results.get(PipelineStage.DEV.value)
        if dev_result:
            return dev_result.output
        return ""


class HealthConsultationPipeline:
    """
    健康咨询专用 Pipeline
    """

    async def consult(
        self,
        user_query: str,
        patient_context: Dict[str, Any] = None,
        enable_consultation: bool = False,
    ) -> Dict[str, Any]:
        """
        健康咨询流程

        Args:
            user_query: 用户问题
            patient_context: 患者上下文
            enable_consultation: 是否启用多 Agent 会诊

        Returns:
            咨询结果
        """
        if enable_consultation:
            return await self._multi_agent_consult(user_query, patient_context)
        else:
            return await self._single_agent_consult(user_query, patient_context)

    async def _single_agent_consult(
        self,
        user_query: str,
        patient_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """单 Agent 咨询"""
        from app.services.agent_manager import AgentSelector

        selector = AgentSelector()
        agent_type = selector.select(user_query, patient_context)

        executor = self._create_executor()
        result = await executor.execute(
            agent_type=agent_type,
            messages=[{"role": "user", "content": user_query}],
        )

        return {
            "success": result.is_success(),
            "agent_type": agent_type,
            "response": result.response,
            "quality_passed": result.quality_result.passed if result.quality_result else None,
        }

    async def _multi_agent_consult(
        self,
        user_query: str,
        patient_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """多 Agent 会诊"""
        from app.services.agents.orchestrator.multi_agent_dialogue import MultiAgentDialogueManager

        dialogue_manager = MultiAgentDialogueManager()

        agents = ["diabetes", "nutrition", "coach"]

        result = await dialogue_manager.multi_agent_consultation(
            query=user_query,
            agents=agents,
            patient_context=patient_context,
        )

        return {
            "success": result.get("success", False),
            "consultation": result,
        }

    def _create_executor(self) -> EnhancedAgentExecutor:
        """创建执行器"""
        return EnhancedAgentExecutor(enable_quality_gate=True, max_retries=2)


# 全局 Pipeline 实例
_health_pipeline: Optional[HealthConsultationPipeline] = None


def get_health_pipeline() -> HealthConsultationPipeline:
    """获取健康咨询 Pipeline"""
    global _health_pipeline
    if _health_pipeline is None:
        _health_pipeline = HealthConsultationPipeline()
    return _health_pipeline
