"""
增强的 Agent 加载器
支持 YAML 元数据 + Markdown 系统提示词 + LLM 配置
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, List
from app.services.agents.core.agent_definition import (
    AgentDefinition,
    AgentMetadata,
    AgentIdentity,
    AgentCapability,
    AgentWorkflow,
    SuccessMetrics,
    AgentLLMConfig,
    AgentType,
)

logger = logging.getLogger(__name__)


class EnhancedAgentLoader:
    """
    增强的 Agent 加载器
    从 YAML + Markdown 格式加载 Agent 定义
    """

    def __init__(self, definitions_dir: str = None):
        if definitions_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent / "agents" / "definitions"
            self.definitions_dir = base_dir
        else:
            self.definitions_dir = Path(definitions_dir)
        self._cache: Dict[str, AgentDefinition] = {}

    def load_all(self) -> Dict[str, AgentDefinition]:
        """加载所有 Agent 定义"""
        agents = {}
        if not self.definitions_dir.exists():
            logger.warning(f"Definitions dir not found: {self.definitions_dir}")
            return agents

        for agent_dir in self.definitions_dir.iterdir():
            if agent_dir.is_dir():
                agent_type = agent_dir.name
                try:
                    agent = self.load(agent_type)
                    if agent:
                        agents[agent_type] = agent
                except Exception as e:
                    logger.error(f"Failed to load agent {agent_type}: {e}")

        logger.info(f"Loaded {len(agents)} agents")
        return agents

    def load(self, agent_type: str) -> Optional[AgentDefinition]:
        """加载单个 Agent 定义"""
        if agent_type in self._cache:
            return self._cache[agent_type]

        agent_dir = self.definitions_dir / agent_type
        if not agent_dir.exists():
            logger.warning(f"Agent directory not found: {agent_dir}")
            return None

        metadata = self._load_metadata(agent_dir)
        if not metadata:
            return None

        identity = self._load_identity(agent_dir, metadata)
        core_mission = self._load_core_mission(agent_dir)
        critical_rules = self._load_critical_rules(agent_dir)
        capabilities = self._load_capabilities(agent_dir)
        workflow = self._load_workflow(agent_dir)
        success_metrics = self._load_success_metrics(agent_dir)
        system_prompt = self._load_system_prompt(agent_dir)
        llm_config = self._load_llm_config(agent_dir)
        tools = metadata.get("tools", [])

        agent = AgentDefinition(
            metadata=metadata,
            identity=identity,
            core_mission=core_mission,
            critical_rules=critical_rules,
            capabilities=capabilities,
            workflow=workflow,
            success_metrics=success_metrics,
            system_prompt=system_prompt,
            llm_config=llm_config,
            tools=tools,
        )

        self._cache[agent_type] = agent
        return agent

    def _load_metadata(self, agent_dir: Path) -> Optional[AgentMetadata]:
        """加载元数据"""
        metadata_file = agent_dir / "metadata.yaml"
        if not metadata_file.exists():
            logger.warning(f"Metadata file not found: {metadata_file}")
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return AgentMetadata(
                name=data.get("name", ""),
                description=data.get("description", ""),
                role=data.get("role", ""),
                specialty=data.get("specialty", []),
                personality=data.get("personality", ""),
                color=data.get("color", "#409EFF"),
                emoji=data.get("emoji", "🤖"),
                vibe=data.get("vibe", ""),
                division=data.get("division", ""),
            )
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None

    def _load_identity(self, agent_dir: Path, metadata: AgentMetadata) -> AgentIdentity:
        """加载身份信息"""
        identity_file = agent_dir / "identity.md"
        if identity_file.exists():
            try:
                content = identity_file.read_text(encoding="utf-8")
                return self._parse_identity_from_markdown(content, metadata)
            except Exception as e:
                logger.warning(f"Failed to load identity: {e}")

        return AgentIdentity(
            role=metadata.role,
            personality=metadata.personality,
            communication_style="专业、友好",
            experience="",
            memory_patterns=[],
        )

    def _parse_identity_from_markdown(self, content: str, metadata: AgentMetadata) -> AgentIdentity:
        """从 Markdown 解析身份信息"""
        role = metadata.role
        personality = metadata.personality
        communication_style = "专业、友好"
        experience = ""
        memory_patterns: List[str] = []

        lines = content.split("\n")
        current_section = ""
        section_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("##"):
                if current_section == "角色" and section_content:
                    role = "\n".join(section_content).strip()
                elif current_section == "人格" and section_content:
                    personality = "\n".join(section_content).strip()
                elif current_section == "沟通风格" and section_content:
                    communication_style = "\n".join(section_content).strip()
                elif current_section == "经验" and section_content:
                    experience = "\n".join(section_content).strip()
                elif current_section == "记忆模式" and section_content:
                    memory_patterns = [p.strip() for p in section_content if p.strip()]

                current_section = line.replace("##", "").strip()
                section_content = []
            elif line.startswith("#"):
                continue
            elif current_section:
                section_content.append(line)

        return AgentIdentity(
            role=role,
            personality=personality,
            communication_style=communication_style,
            experience=experience,
            memory_patterns=memory_patterns,
        )

    def _load_core_mission(self, agent_dir: Path) -> str:
        """加载核心使命"""
        mission_file = agent_dir / "core_mission.md"
        if mission_file.exists():
            try:
                return mission_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning(f"Failed to load core mission: {e}")
        return ""

    def _load_critical_rules(self, agent_dir: Path) -> List[str]:
        """加载关键规则"""
        rules_file = agent_dir / "critical_rules.md"
        if rules_file.exists():
            try:
                content = rules_file.read_text(encoding="utf-8")
                return self._parse_rules(content)
            except Exception as e:
                logger.warning(f"Failed to load critical rules: {e}")
        return []

    def _parse_rules(self, content: str) -> List[str]:
        """解析规则列表"""
        rules = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("- "):
                rules.append(line[2:])
            elif line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                parts = line.split(".", 1)
                if len(parts) > 1:
                    rules.append(parts[1].strip())
            elif line.startswith("* ") or line.startswith("**"):
                cleaned = line.lstrip("* ").lstrip("**").rstrip("**").strip()
                if cleaned:
                    rules.append(cleaned)
        return rules

    def _load_capabilities(self, agent_dir: Path) -> List[AgentCapability]:
        """加载能力列表"""
        cap_file = agent_dir / "capabilities.md"
        if cap_file.exists():
            try:
                content = cap_file.read_text(encoding="utf-8")
                return self._parse_capabilities(content)
            except Exception as e:
                logger.warning(f"Failed to load capabilities: {e}")
        return []

    def _parse_capabilities(self, content: str) -> List[AgentCapability]:
        """解析能力"""
        capabilities = []
        current_cap = None
        current_desc = []
        current_examples = []
        in_examples = False

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("### ") or line.startswith("## "):
                if current_cap:
                    capabilities.append(
                        AgentCapability(
                            name=current_cap,
                            description="\n".join(current_desc).strip(),
                            examples=[e.strip() for e in current_examples if e.strip()],
                        )
                    )
                header = line.replace("### ", "").replace("## ", "").strip()
                current_cap = header
                current_desc = []
                current_examples = []
                in_examples = False
            elif line.lower().startswith("example"):
                in_examples = True
            elif in_examples and line.startswith("-"):
                current_examples.append(line[1:].strip())
            elif current_cap and not in_examples:
                current_desc.append(line)

        if current_cap:
            capabilities.append(
                AgentCapability(
                    name=current_cap,
                    description="\n".join(current_desc).strip(),
                    examples=[e.strip() for e in current_examples if e.strip()],
                )
            )

        return capabilities

    def _load_workflow(self, agent_dir: Path) -> AgentWorkflow:
        """加载工作流程"""
        workflow_file = agent_dir / "workflow.md"
        if workflow_file.exists():
            try:
                content = workflow_file.read_text(encoding="utf-8")
                return self._parse_workflow(content)
            except Exception as e:
                logger.warning(f"Failed to load workflow: {e}")
        return AgentWorkflow()

    def _parse_workflow(self, content: str) -> AgentWorkflow:
        """解析工作流程"""
        steps = []
        conditions = {}
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("### ") or line.startswith("## "):
                step_name = line.replace("### Step ", "").replace("## ", "").strip()
                if "step" in step_name.lower() or any(c.isdigit() for c in step_name):
                    steps.append(step_name)
            elif line.startswith("**条件:**") or line.startswith("条件:"):
                condition_line = line.replace("**条件:**", "").replace("条件:", "").strip()
                parts = condition_line.split("->")
                if len(parts) == 2:
                    conditions[parts[0].strip()] = parts[1].strip()

        return AgentWorkflow(steps=steps, conditions=conditions)

    def _load_success_metrics(self, agent_dir: Path) -> SuccessMetrics:
        """加载成功指标"""
        metrics_file = agent_dir / "success_metrics.md"
        if metrics_file.exists():
            try:
                content = metrics_file.read_text(encoding="utf-8")
                return self._parse_success_metrics(content)
            except Exception as e:
                logger.warning(f"Failed to load success metrics: {e}")
        return SuccessMetrics()

    def _parse_success_metrics(self, content: str) -> SuccessMetrics:
        """解析成功指标"""
        metrics = {}
        quality_standards = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("- **") or line.startswith("* **"):
                parts = line.replace("* **", "").replace("- **", "").split(":**")
                if len(parts) == 2:
                    metrics[parts[0].strip()] = parts[1].strip()
            elif line.startswith("- "):
                quality_standards.append(line[2:].strip())

        return SuccessMetrics(metrics=metrics, quality_standards=quality_standards)

    def _load_system_prompt(self, agent_dir: Path) -> str:
        """加载系统提示词"""
        prompt_file = agent_dir / "system_prompt.md"
        if prompt_file.exists():
            try:
                return prompt_file.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning(f"Failed to load system prompt: {e}")
        return ""

    def _load_llm_config(self, agent_dir: Path) -> AgentLLMConfig:
        agent_type = agent_dir.name
        db_config = self._load_llm_config_from_db(agent_type)
        if db_config:
            logger.info(f"[AgentLoader] Using DB LLM config for {agent_type}: {db_config.provider}/{db_config.model}")
            return db_config

        config_file = agent_dir / "llm_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                yaml_config = AgentLLMConfig.from_dict(data)
                yaml_config.config_source = "yaml"
                logger.info(f"[AgentLoader] Using YAML LLM config for {agent_type}: {yaml_config.provider}/{yaml_config.model}")
                return yaml_config
            except Exception as e:
                logger.warning(f"Failed to load LLM config: {e}")
        return AgentLLMConfig()

    def _load_llm_config_from_db(self, agent_type: str) -> Optional[AgentLLMConfig]:
        try:
            from app.utils.database import SessionLocal
            db = SessionLocal()
            try:
                from app.models.models import AgentLLMConfigModel
                row = db.query(AgentLLMConfigModel).filter(
                    AgentLLMConfigModel.agent_type == agent_type,
                    AgentLLMConfigModel.is_active == True
                ).first()
                if row:
                    return AgentLLMConfig(
                        provider=row.provider,
                        model=row.model,
                        temperature=row.temperature,
                        max_tokens=row.max_tokens,
                        timeout=row.timeout,
                        fallback_provider=row.fallback_provider,
                        fallback_model=row.fallback_model,
                        api_key=row.api_key,
                    )
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"DB config lookup failed for {agent_type}: {e}")
        return None

    def reload(self, agent_type: str) -> Optional[AgentDefinition]:
        if agent_type in self._cache:
            del self._cache[agent_type]
        return self.load(agent_type)

    def clear_cache(self):
        self._cache.clear()
