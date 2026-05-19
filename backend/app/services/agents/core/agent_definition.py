"""
Agent 定义模块
融合 Agency-Agents 的设计理念：
- Identity & Memory
- Core Mission
- Critical Rules
- Workflow Process
- Success Metrics
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class AgentType(str, Enum):
    """Agent 类型"""

    GENERAL = "general"
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    NUTRITION = "nutrition"
    MEDICATION = "medication"
    PSYCHOLOGY = "psychology"
    REHABILITATION = "rehabilitation"
    COACH = "coach"
    COGNITIVE = "cognitive"


@dataclass
class AgentIdentity:
    """Agent 身份与记忆"""

    role: str  # 角色
    personality: str  # 人格特征
    communication_style: str  # 沟通风格
    experience: str = ""  # 经验描述
    memory_patterns: List[str] = field(default_factory=list)  # 记忆模式


@dataclass
class AgentCapability:
    """Agent 能力定义"""

    name: str
    description: str
    examples: List[str] = field(default_factory=list)


@dataclass
class AgentWorkflow:
    """Agent 工作流程"""

    steps: List[str] = field(default_factory=list)
    conditions: Dict[str, str] = field(default_factory=dict)  # 条件分支


@dataclass
class SuccessMetrics:
    """成功指标"""

    metrics: Dict[str, str] = field(default_factory=dict)
    quality_standards: List[str] = field(default_factory=list)


@dataclass
class AgentLLMConfig:
    """Agent 的 LLM 配置 - 支持每个 Agent 配置独立模型"""

    provider: str = "default"
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 120
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    api_key: Optional[str] = None
    config_source: str = "yaml"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentLLMConfig":
        if data is None:
            return cls()
        return cls(
            provider=data.get("provider", "default"),
            model=data.get("model", "default"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            timeout=data.get("timeout", 120),
            fallback_provider=data.get("fallback_provider"),
            fallback_model=data.get("fallback_model"),
            api_key=data.get("api_key"),
            config_source=data.get("config_source", "yaml"),
        )


@dataclass
class AgentMetadata:
    """Agent 元数据"""

    name: str
    description: str
    role: str
    specialty: List[str]
    personality: str
    color: str = "#409EFF"
    emoji: str = "🤖"
    vibe: str = ""  # 一句话描述（Agency-Agents 风格）
    division: str = ""  # 部门分类


@dataclass
class AgentDefinition:
    """Agent 定义 - 完整结构"""

    # 元数据
    metadata: AgentMetadata

    # 核心组件（Agency-Agents 风格）
    identity: AgentIdentity  # 身份与记忆
    core_mission: str  # 核心使命
    critical_rules: List[str]  # 关键规则
    capabilities: List[AgentCapability] = field(default_factory=list)  # 能力列表
    workflow: AgentWorkflow = None  # 工作流程
    success_metrics: SuccessMetrics = None  # 成功指标

    # 系统提示词（由 system_prompt.md 生成）
    system_prompt: str = ""

    # LLM 配置（支持不同 Agent 不同模型）
    llm_config: AgentLLMConfig = None

    # 工具配置
    tools: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.workflow is None:
            self.workflow = AgentWorkflow()
        if self.success_metrics is None:
            self.success_metrics = SuccessMetrics()
        if self.llm_config is None:
            self.llm_config = AgentLLMConfig()

    def to_markdown(self) -> str:
        """转换为 Markdown 格式（用于显示/调试）"""
        md = f"""# {self.metadata.name}

> {self.metadata.vibe}

## 🧠 Identity & Memory
- **Role**: {self.identity.role}
- **Personality**: {self.identity.personality}
- **Communication Style**: {self.identity.communication_style}
- **Experience**: {self.identity.experience}

## 🎯 Core Mission
{self.core_mission}

## 🚨 Critical Rules
"""
        for i, rule in enumerate(self.critical_rules, 1):
            md += f"\n{i}. {rule}"

        md += "\n\n## 📋 Capabilities"
        for cap in self.capabilities:
            md += f"\n### {cap.name}"
            md += f"\n{cap.description}"
            if cap.examples:
                md += "\nExamples:"
                for ex in cap.examples:
                    md += f"\n- {ex}"

        md += "\n\n## 🔄 Workflow Process"
        for i, step in enumerate(self.workflow.steps, 1):
            md += f"\n### Step {i}: {step}"

        md += "\n\n## 📊 Success Metrics"
        for metric, value in self.success_metrics.metrics.items():
            md += f"\n- **{metric}**: {value}"

        md += "\n\n## 🤖 LLM Configuration"
        md += f"\n- **Provider**: {self.llm_config.provider}"
        md += f"\n- **Model**: {self.llm_config.model}"
        md += f"\n- **Temperature**: {self.llm_config.temperature}"

        return md
