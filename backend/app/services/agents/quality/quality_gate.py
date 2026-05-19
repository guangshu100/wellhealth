"""
质量门控系统
基于证据的验证和重试逻辑
参考 Agency-Agents 的 EvidenceQA 模式
"""

import re
import logging
import base64
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from app.services.agents.core.agent_definition import AgentDefinition

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """验证级别"""

    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


class EvidenceType(str, Enum):
    """证据类型 - 参考 Agency-Agents"""

    TEXT = "text"
    SCREENSHOT = "screenshot"
    CODE_SNIPPET = "code_snippet"
    API_RESPONSE = "api_response"
    USER_FEEDBACK = "user_feedback"
    AUTOMATED_TEST = "automated_test"
    LOG_OUTPUT = "log_output"


@dataclass
class ValidationRule:
    """验证规则"""

    name: str
    pattern: str
    message: str
    level: ValidationLevel = ValidationLevel.NORMAL
    enabled: bool = True
    evidence_type: EvidenceType = EvidenceType.TEXT


@dataclass
class ValidationResult:
    """验证结果"""

    passed: bool
    score: float
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: List["Evidence"] = field(default_factory=list)

    @classmethod
    def pass_result(
        cls, score: float = 1.0, metadata: Dict = None, evidence: List = None
    ) -> "ValidationResult":
        return cls(passed=True, score=score, metadata=metadata or {}, evidence=evidence or [])

    @classmethod
    def fail_result(
        cls, reasons: List[str], score: float = 0.0, evidence: List = None
    ) -> "ValidationResult":
        return cls(passed=False, score=score, reasons=reasons, evidence=evidence or [])


@dataclass
class Evidence:
    """
    证据 - 参考 Agency-Agents EvidenceCollector
    支持多种证据类型：截图、代码片段、日志等
    """

    type: EvidenceType
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content[:500] if len(self.content) > 500 else self.content,
            "timestamp": self.timestamp,
            "description": self.description,
            "metadata": self.metadata,
        }


class EvidenceCollector:
    """
    证据收集器 - Agency-Agents EvidenceCollector 模式
    收集验证所需的各类证据
    """

    def __init__(self):
        self.evidence: List[Evidence] = []

    def add_text_evidence(self, content: str, description: str = "") -> Evidence:
        """添加文本证据"""
        evidence = Evidence(
            type=EvidenceType.TEXT,
            content=content,
            description=description,
        )
        self.evidence.append(evidence)
        return evidence

    def add_screenshot_evidence(self, image_data: bytes, description: str = "") -> Evidence:
        """添加截图证据"""
        b64_data = base64.b64encode(image_data).decode("utf-8")
        evidence = Evidence(
            type=EvidenceType.SCREENSHOT,
            content=b64_data,
            description=description,
            metadata={"format": "base64", "size": len(image_data)},
        )
        self.evidence.append(evidence)
        return evidence

    def add_code_evidence(self, code: str, language: str = "", description: str = "") -> Evidence:
        """添加代码证据"""
        evidence = Evidence(
            type=EvidenceType.CODE_SNIPPET,
            content=code,
            description=description,
            metadata={"language": language},
        )
        self.evidence.append(evidence)
        return evidence

    def add_api_evidence(self, response: Dict, description: str = "") -> Evidence:
        """添加 API 响应证据"""
        evidence = Evidence(
            type=EvidenceType.API_RESPONSE,
            content=str(response)[:1000],
            description=description,
            metadata={"keys": list(response.keys()) if isinstance(response, dict) else []},
        )
        self.evidence.append(evidence)
        return evidence

    def add_test_evidence(self, test_result: Dict, description: str = "") -> Evidence:
        """添加测试结果证据"""
        evidence = Evidence(
            type=EvidenceType.AUTOMATED_TEST,
            content=str(test_result),
            description=description,
            metadata={"passed": test_result.get("passed", False)},
        )
        self.evidence.append(evidence)
        return evidence

    def clear(self):
        """清空证据"""
        self.evidence = []

    def get_evidence(self) -> List[Evidence]:
        """获取所有证据"""
        return self.evidence

    def export(self) -> List[Dict[str, Any]]:
        """导出证据为字典"""
        return [e.to_dict() for e in self.evidence]


class EvidenceQA:
    """
    证据质量保证 - Agency-Agents EvidenceQA 模式
    基于证据的 QA 验证
    """

    def __init__(self, collector: EvidenceCollector = None):
        self.collector = collector or EvidenceCollector()

    async def validate_with_evidence(
        self,
        agent: AgentDefinition,
        response: str,
        task_context: Dict[str, Any] = None,
    ) -> ValidationResult:
        """
        基于证据的验证

        Args:
            agent: Agent 定义
            response: 响应内容
            task_context: 任务上下文（包含预期输出、标准等）

        Returns:
            ValidationResult with evidence
        """
        evidence = []

        self.collector.add_text_evidence(response, "Agent response")

        if task_context:
            if expected := task_context.get("expected_output"):
                self.collector.add_text_evidence(expected, "Expected output")
            if task_spec := task_context.get("task_spec"):
                self.collector.add_code_evidence(task_spec, "yaml", "Task specification")

        validation_result = await self._validate(agent, response, task_context)
        validation_result.evidence = self.collector.export()

        return validation_result

    async def _validate(
        self,
        agent: AgentDefinition,
        response: str,
        task_context: Dict[str, Any] = None,
    ) -> ValidationResult:
        """内部验证逻辑"""
        violations = []
        score = 1.0

        if len(response) < 20:
            violations.append("回答内容过短")
            score -= 0.3

        if any(word in response for word in ["诊断", "确诊", "患有"]):
            if "建议" not in response and "咨询" not in response:
                violations.append("不应做出医学诊断")
                score -= 0.3

        if any(word in response for word in ["停药", "自行", "随便"]):
            if "医" in response:
                violations.append("用药建议应谨慎")
                score -= 0.2

        score = max(0.0, min(1.0, score))

        if not violations:
            return ValidationResult.pass_result(score=score)
        else:
            return ValidationResult.fail_result(reasons=violations, score=score)

    async def screenshot_validation(
        self,
        screenshot: bytes,
        expected_elements: List[str],
    ) -> ValidationResult:
        """
        截图验证（需要 OCR 或视觉模型）
        这是一个占位实现
        """
        evidence = Evidence(
            type=EvidenceType.SCREENSHOT,
            content=base64.b64encode(screenshot).decode("utf-8")[:200],
            description="Screenshot for validation",
            metadata={"expected_elements": expected_elements},
        )

        return ValidationResult.pass_result(
            score=0.8,
            metadata={"validation_type": "screenshot"},
            evidence=[evidence],
        )


class QualityGate:
    """
    质量门控
    验证 Agent 响应是否符合质量标准
    """

    DEFAULT_RULES = [
        ValidationRule(
            name="safety_check",
            pattern=r"(?<!\w)(kill|suicide|die|murder|harm)(?!\w)",
            message="内容包含不安全词汇",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="no_medical_claim",
            pattern=r"(?<!\w)(诊断|确诊|患有)(?!\w)",
            message="不应做出医学诊断",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="recommendation_present",
            pattern=r"(建议|推荐|考虑)",
            message="缺少建议内容",
            level=ValidationLevel.NORMAL,
        ),
        ValidationRule(
            name="medical_term_explained",
            pattern=r"(HbA1c|血糖|血压|BMI)",
            message="医学术语可能需要解释",
            level=ValidationLevel.LENIENT,
        ),
        ValidationRule(
            name="min_length",
            pattern=r".{20,}",
            message="回答内容过短",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="no_harmful_advice",
            pattern=r"(停药|减量|自行)(?=.{0,20}(药|胰岛素|治疗))",
            message="可能包含不安全建议",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="professional_tone",
            pattern=r"(你.*?(得|是|有)|赶紧|马上|立刻).{0,10}(死|完|了)",
            message="语气不够专业",
            level=ValidationLevel.NORMAL,
        ),
    ]

    def __init__(
        self,
        rules: List[ValidationRule] = None,
        level: ValidationLevel = ValidationLevel.NORMAL,
        evidence_collector: EvidenceCollector = None,
    ):
        self.rules = rules or self.DEFAULT_RULES
        self.level = level
        self.evidence_collector = evidence_collector or EvidenceCollector()
        self._setup_rules_for_level()

    def _setup_rules_for_level(self):
        """根据验证级别启用/禁用规则"""
        for rule in self.rules:
            if self.level == ValidationLevel.LENIENT:
                rule.enabled = rule.level != ValidationLevel.STRICT
            elif self.level == ValidationLevel.STRICT:
                rule.enabled = True
            else:
                rule.enabled = rule.level in (ValidationLevel.NORMAL, ValidationLevel.STRICT)

    async def validate(
        self,
        agent: AgentDefinition,
        response: str,
        context: Any = None,
    ) -> ValidationResult:
        """
        验证响应质量

        Args:
            agent: Agent 定义
            response: 响应内容
            context: 执行上下文

        Returns:
            ValidationResult
        """
        violations = []
        suggestions = []
        score = 1.0

        self.evidence_collector.add_text_evidence(response, "Agent response")

        for rule in self.rules:
            if not rule.enabled:
                continue

            if not self._check_rule(response, rule):
                violations.append(rule.message)
                if rule.level == ValidationLevel.STRICT:
                    score -= 0.3
                elif rule.level == ValidationLevel.NORMAL:
                    score -= 0.15
                else:
                    score -= 0.05
            elif rule.name == "medical_term_explained" and self._contains_unexplained_terms(
                response
            ):
                suggestions.append("建议解释医学术语以提高可读性")

        score = max(0.0, min(1.0, score))

        result = ValidationResult(
            passed=len(violations) == 0,
            score=score,
            reasons=violations,
            suggestions=suggestions,
            evidence=self.evidence_collector.export(),
        )

        return result

    def _check_rule(self, text: str, rule: ValidationRule) -> bool:
        """检查单条规则"""
        try:
            pattern = re.compile(rule.pattern, re.IGNORECASE)
            match = pattern.search(text)
            return match is None
        except re.error as e:
            logger.warning(f"Invalid regex pattern in rule {rule.name}: {e}")
            return True

    def _contains_unexplained_terms(self, text: str) -> bool:
        """检查是否包含未解释的医学术语"""
        medical_terms = ["HbA1c", "BMI", "LDL", "HDL", "TG", "TC"]
        unexplained = []

        for term in medical_terms:
            if term in text:
                explained_pattern = re.compile(
                    rf"{term}.{0, 50}(即|是|称为|的意思|是指)", re.IGNORECASE
                )
                if not explained_pattern.search(text):
                    unexplained.append(term)

        return len(unexplained) > 0

    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules.append(rule)

    def remove_rule(self, name: str):
        """移除验证规则"""
        self.rules = [r for r in self.rules if r.name != name]

    def get_enabled_rules(self) -> List[str]:
        """获取启用的规则列表"""
        return [r.name for r in self.rules if r.enabled]


class HealthSpecificQualityGate(QualityGate):
    """健康领域特定的质量门控"""

    HEALTH_RULES = [
        ValidationRule(
            name="no_diagnosis",
            pattern=r"(?<!\w)(诊断|确诊|患有|得了)(?!.{0,5}(建议|咨询|检查))",
            message="不应做出医学诊断",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="urgency_warning",
            pattern=r"(胸痛|呼吸困难|昏迷|酮症)",
            message="涉及急症时应建议就医",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="medication_caution",
            pattern=r"(自行|自己|随便)(停|减|加)",
            message="用药建议应谨慎",
            level=ValidationLevel.STRICT,
        ),
        ValidationRule(
            name="reference_standards",
            pattern=r"(正常范围|参考值|标准)",
            message="应提供参考标准",
            level=ValidationLevel.NORMAL,
        ),
        ValidationRule(
            name="lifestyle_recommendation",
            pattern=r"(运动|饮食|作息)",
            message="应包含生活方式建议",
            level=ValidationLevel.NORMAL,
        ),
        ValidationRule(
            name="follow_up_reminder",
            pattern=r"(复查|复诊|监测)",
            message="应包含复查提醒",
            level=ValidationLevel.LENIENT,
        ),
    ]

    def __init__(self):
        super().__init__(rules=self.HEALTH_RULES + self.DEFAULT_RULES)


class ResponseImprover:
    """响应改进器"""

    IMPROVEMENT_TEMPLATES = {
        "safety": "请确保以下内容安全无害，不包含任何可能伤害用户的建议。",
        "diagnosis": "请移除任何诊断性陈述，改为建议性表达。",
        "completeness": "请补充以下内容使回答更完整：",
        "clarity": "请使用更通俗易懂的语言解释医学概念。",
        "tone": "请使用更专业、友善的语气。",
    }

    async def improve(
        self,
        response: str,
        quality_result: ValidationResult,
        agent: AgentDefinition,
    ) -> str:
        """根据质量反馈改进响应"""
        improvements = []

        for reason in quality_result.reasons:
            if "诊断" in reason:
                improvements.append(self.IMPROVEMENT_TEMPLATES["diagnosis"])
            elif "安全" in reason:
                improvements.append(self.IMPROVEMENT_TEMPLATES["safety"])
            elif "建议" in reason or "建议" in response:
                improvements.append(self.IMPROVEMENT_TEMPLATES["completeness"])
            elif "通俗" in reason or "解释" in reason:
                improvements.append(self.IMPROVEMENT_TEMPLATES["clarity"])

        return "\n".join(improvements) + f"\n\n原始回答:\n{response}"


class AgentSpawner:
    """
    Agent 生成器 - Agency-Agents spawn 机制
    支持动态创建和调用不同类型的 Agent
    """

    def __init__(
        self,
        executor: Callable = None,
        max_parallel: int = 5,
    ):
        self.executor = executor
        self.max_parallel = max_parallel
        self._active_agents: Dict[str, Any] = {}

    async def spawn(
        self,
        agent_type: str,
        task: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        生成并执行一个 Agent

        Args:
            agent_type: Agent 类型
            task: 任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        agent_id = f"{agent_type}_{datetime.now().timestamp()}"

        spawn_instruction = f"""请作为 {agent_type} Agent 完成以下任务：

任务：{task}

上下文信息：
{context if context else "无"}

请按照你的专业能力完成任务，并提供详细的执行证据。"""

        if self.executor:
            result = await self.executor(
                agent_type=agent_type,
                messages=[{"role": "user", "content": spawn_instruction}],
            )
            self._active_agents[agent_id] = result
            return {"agent_id": agent_id, "result": result}

        return {"agent_id": agent_id, "error": "No executor configured"}

    async def spawn_parallel(
        self,
        tasks: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        并行生成多个 Agent

        Args:
            tasks: 任务列表 [{"agent_type": "...", "task": "..."}, ...]

        Returns:
            执行结果列表
        """
        import asyncio

        async def spawn_single(task: Dict[str, str]) -> Dict[str, Any]:
            return await self.spawn(
                agent_type=task["agent_type"],
                task=task["task"],
                context=task.get("context"),
            )

        tasks_to_run = tasks[: self.max_parallel]
        results = await asyncio.gather(*[spawn_single(t) for t in tasks_to_run])

        return list(results)

    def get_active_agents(self) -> Dict[str, Any]:
        """获取活跃的 Agent"""
        return self._active_agents

    def terminate_agent(self, agent_id: str):
        """终止指定的 Agent"""
        if agent_id in self._active_agents:
            del self._active_agents[agent_id]
