# 混合多 Agent 架构实现总结

## 概述

本项目实现了一个**混合多 Agent 架构**，融合了：
1. **Agency-Agents** 的设计理念（Markdown 模板、Agent 编排器、质量门控、个性化 Agent）
2. **WellHealth** 的代码实现（Python/FastAPI 后端、RAG 知识库、安全检查器）

## 核心功能

### 1. 每个 Agent 独立配置 LLM 模型

```yaml
# llm_config.yaml 示例
provider: siliconflow
model: Qwen/Qwen2.5-7B-Instruct
temperature: 0.7
max_tokens: 2000
timeout: 120

fallback_provider: openai
fallback_model: gpt-4o-mini
```

**支持的 Provider**:
- `openai` - GPT-4, GPT-4o-mini
- `anthropic` - Claude 系列
- `siliconflow` - 硅基流动（开源模型）
- `ollama` - 本地大模型
- `dashscope` - 阿里云通义

### 2. Agent 增强定义

```python
@dataclass
class AgentDefinition:
    metadata: AgentMetadata           # 元数据（名称、描述、颜色等）
    identity: AgentIdentity          # 身份与记忆
    core_mission: str               # 核心使命
    critical_rules: List[str]       # 关键规则
    capabilities: List[AgentCapability]  # 能力列表
    workflow: AgentWorkflow         # 工作流程
    success_metrics: SuccessMetrics # 成功指标
    system_prompt: str              # 系统提示词
    llm_config: AgentLLMConfig      # LLM 配置（核心新增）
    tools: List[str]                # 工具配置
```

### 3. 质量门控

```python
# 健康领域特定规则
ValidationRule(name="no_diagnosis", pattern=..., level=STRICT)
ValidationRule(name="urgency_warning", pattern=..., level=STRICT)
ValidationRule(name="medication_caution", pattern=..., level=STRICT)
```

### 4. Agent 编排器

支持多种模式：
- **单 Agent** - 单一 Agent 执行
- **多 Agent 会诊** - 多个 Agent 协作讨论
- **辩论模式** - Agent 之间辩论
- **协作模式** - Agent 顺序协作完成任务

## 目录结构

```
wellhealth/backend/app/services/agents/
├── __init__.py                    # 模块导出
├── core/                          # 核心模块
│   ├── __init__.py
│   ├── agent_definition.py        # Agent 定义数据结构
│   ├── agent_loader.py           # 增强的 Agent 加载器
│   ├── llm_router.py             # LLM 路由器（核心）
│   └── agent_executor.py         # 增强的执行器
├── orchestrator/                  # 编排器
│   ├── __init__.py
│   ├── workflow_orchestrator.py   # 工作流编排器
│   └── multi_agent_dialogue.py   # 多 Agent 对话管理器
└── quality/                       # 质量控制
    ├── __init__.py
    └── quality_gate.py            # 质量门控系统
```

## 使用示例

### 1. 单 Agent 执行

```python
from app.services.agents.core.agent_executor import EnhancedAgentExecutor

executor = EnhancedAgentExecutor(enable_quality_gate=True)
result = await executor.execute(
    agent_type="diabetes",
    messages=[{"role": "user", "content": "糖尿病饮食建议"}],
)
```

### 2. 多 Agent 会诊

```python
from app.services.agents.orchestrator.multi_agent_dialogue import MultiAgentDialogueManager

manager = MultiAgentDialogueManager()
result = await manager.multi_agent_consultation(
    query="血糖偏高怎么办",
    agents=["diabetes", "nutrition", "coach"],
    patient_context={"disease": "pre-diabetes"},
)
```

### 3. 工作流编排

```python
from app.services.agents.orchestrator.workflow_orchestrator import (
    WorkflowOrchestrator, PipelineConfig, PipelineStage
)

orchestrator = WorkflowOrchestrator()
config = PipelineConfig(
    stages=[PipelineStage.PM, PipelineStage.ARCHITECT, PipelineStage.DEV, PipelineStage.QA],
    max_iterations=2,
)
result = await orchestrator.execute_pipeline(task="设计血糖监测功能", config=config)
```

### 4. 质量门控验证

```python
from app.services.agents.quality.quality_gate import QualityGate

gate = QualityGate()
result = await gate.validate(agent, response)
if not result.passed:
    print(f"质量检查失败: {result.reasons}")
```

## Agent 定义文件结构

```
agents/definitions/diabetes/
├── metadata.yaml          # 元数据
├── system_prompt.md       # 系统提示词
├── llm_config.yaml        # LLM 配置（新增）
├── identity.md           # 身份定义（可选）
├── core_mission.md       # 核心使命（可选）
├── critical_rules.md     # 关键规则（可选）
├── capabilities.md       # 能力列表（可选）
├── workflow.md          # 工作流程（可选）
└── success_metrics.md    # 成功指标（可选）
```

## 测试

运行测试脚本：

```bash
cd wellhealth/backend
python -m app.services.agents.test_hybrid_agents
```

## 与现有系统集成

混合架构与现有 `agent_manager.py` 完全兼容：

```python
# 现有代码继续有效
from app.services.agent_manager import AgentSelector, agent_selector

agent_type = agent_selector.select(query, patient_context)

# 新架构可以替换/扩展现有功能
from app.services.agents import EnhancedAgentExecutor

executor = EnhancedAgentExecutor()
result = await executor.execute(agent_type, messages)
```

## 下一步计划

1. **添加更多 Agent 类型** - 高血压、心理健康等
2. **完善工作流模板** - 针对不同场景的预定义 Pipeline
3. **增强 RAG 集成** - Agent 知识库检索
4. **API 端点** - 暴露编排器功能到前端
5. **性能优化** - Agent 缓存、并行执行优化

## 相关文档

- [Agency-Agents 项目](agency-agents/)
- [WellHealth 主项目](wellhealth/)
- [前端聊天实现](../frontend/)
- [小程序实现](../miniapp/)
