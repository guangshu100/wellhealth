"""
融合架构 Agent 核心模块
结合 Agency-Agents 的设计理念 + 康伴健康的代码实现
"""

from app.services.agents.core.agent_definition import AgentDefinition, AgentMetadata, AgentLLMConfig
from app.services.agents.core.agent_loader import EnhancedAgentLoader
from app.services.agents.core.llm_router import LLMRouter, get_llm_router
from app.services.agents.core.agent_executor import (
    EnhancedAgentExecutor,
    ExecutionResult,
    ExecutionStatus,
    get_executor,
)
from app.services.agents.orchestrator.workflow_orchestrator import (
    WorkflowOrchestrator,
    HealthConsultationPipeline,
    get_health_pipeline,
)
from app.services.agents.orchestrator.multi_agent_dialogue import (
    MultiAgentDialogueManager,
    DialogueMode,
    get_dialogue_manager,
)
from app.services.agents.quality.quality_gate import (
    QualityGate,
    ValidationResult,
    ValidationLevel,
    ValidationRule,
    Evidence,
    EvidenceType,
    EvidenceCollector,
    EvidenceQA,
    HealthSpecificQualityGate,
    ResponseImprover,
    AgentSpawner,
)

__all__ = [
    # Core
    "AgentDefinition",
    "AgentMetadata",
    "AgentLLMConfig",
    "EnhancedAgentLoader",
    "LLMRouter",
    "get_llm_router",
    "EnhancedAgentExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "get_executor",
    # Orchestrator
    "WorkflowOrchestrator",
    "HealthConsultationPipeline",
    "get_health_pipeline",
    "MultiAgentDialogueManager",
    "DialogueMode",
    "get_dialogue_manager",
    # Quality
    "QualityGate",
    "ValidationResult",
    "ValidationLevel",
    "ValidationRule",
    "Evidence",
    "EvidenceType",
    "EvidenceCollector",
    "EvidenceQA",
    "HealthSpecificQualityGate",
    "ResponseImprover",
    "AgentSpawner",
]
