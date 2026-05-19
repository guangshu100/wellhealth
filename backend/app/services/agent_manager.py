"""
Agent系统核心模块
实现多Agent协作、意图识别、Agent选择与执行
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent类型"""

    GENERAL = "general"  # 通用问答
    DIABETES = "diabetes"  # 糖尿病专科
    HYPERTENSION = "hypertension"  # 高血压专科
    NUTRITION = "nutrition"  # 营养咨询
    COACH = "coach"  # 健康教练
    MEDICATION = "medication"  # 用药咨询
    PSYCHOLOGY = "psychology"  # 心理支持
    REHABILITATION = "rehabilitation"  # 康复指导
    COGNITIVE = "cognitive"  # 认知评估


@dataclass
class AgentMetadata:
    """Agent元数据"""

    name: str
    description: str
    role: str
    specialty: List[str]
    personality: str
    color: str = "#409EFF"
    emoji: str = "🤖"


@dataclass
class AgentLLMConfig:
    """Agent LLM配置"""

    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 120
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    api_key: Optional[str] = None
    config_source: str = "yaml"


@dataclass
class AgentDefinition:
    """Agent定义"""

    metadata: AgentMetadata
    system_prompt: str
    capabilities: List[str]
    tools: List[str]
    llm_config: AgentLLMConfig = field(default_factory=AgentLLMConfig)


class AgentLoader:
    """Agent加载器"""

    def __init__(self, agents_dir: str = None):
        if agents_dir is None:
            # 默认从项目agents目录加载
            base_dir = Path(__file__).parent.parent / "agents"
            self.agents_dir = base_dir / "definitions"
        else:
            self.agents_dir = Path(agents_dir)

    def load_all(self) -> Dict[str, AgentDefinition]:
        """加载所有Agent定义"""
        agents = {}
        if not self.agents_dir.exists():
            return agents

        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir():
                agent_type = agent_dir.name
                agent = self.load(agent_type)
                if agent:
                    agents[agent_type] = agent
        return agents

    def load(self, agent_type: str) -> Optional[AgentDefinition]:
        """加载单个Agent定义"""
        agent_dir = self.agents_dir / agent_type
        if not agent_dir.exists():
            return None

        # 加载metadata.yaml
        metadata_file = agent_dir / "metadata.yaml"
        if not metadata_file.exists():
            return None

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata_dict = yaml.safe_load(f)

        metadata = AgentMetadata(
            name=metadata_dict.get("name", ""),
            description=metadata_dict.get("description", ""),
            role=metadata_dict.get("role", ""),
            specialty=metadata_dict.get("specialty", []),
            personality=metadata_dict.get("personality", ""),
            color=metadata_dict.get("color", "#409EFF"),
            emoji=metadata_dict.get("emoji", "🤖"),
        )

        # 加载system prompt
        prompt_file = agent_dir / "system_prompt.md"
        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        else:
            system_prompt = ""

        # 加载capabilities和tools
        capabilities = metadata_dict.get("capabilities", [])
        tools = metadata_dict.get("tools", [])

        # 加载 LLM 配置
        llm_config = self._load_llm_config(agent_dir)

        return AgentDefinition(
            metadata=metadata,
            system_prompt=system_prompt,
            capabilities=capabilities,
            tools=tools,
            llm_config=llm_config,
        )

    def _load_llm_config(self, agent_dir: Path) -> AgentLLMConfig:
        agent_type = agent_dir.name
        db_config = self._load_llm_config_from_db(agent_type)
        if db_config:
            logger.info(f"[AgentManager] Using DB LLM config for {agent_type}: {db_config.provider}/{db_config.model}")
            return db_config

        llm_config_file = agent_dir / "llm_config.yaml"
        if not llm_config_file.exists():
            return AgentLLMConfig()

        try:
            with open(llm_config_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)

            return AgentLLMConfig(
                provider=config_dict.get("provider", "openai"),
                model=config_dict.get("model", "gpt-4o"),
                temperature=config_dict.get("temperature", 0.7),
                max_tokens=config_dict.get("max_tokens", 2000),
                timeout=config_dict.get("timeout", 120),
                fallback_provider=config_dict.get("fallback_provider"),
                fallback_model=config_dict.get("fallback_model"),
                config_source="yaml",
            )
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
                        config_source="database",
                    )
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"DB config lookup failed for {agent_type}: {e}")
        return None


class IntentClassifier:
    """意图分类器"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        AgentType.DIABETES: [
            "血糖",
            "糖尿病",
            "胰岛素",
            "降糖",
            "空腹血糖",
            "餐后血糖",
            "HbA1c",
            "糖化血红蛋白",
            "并发症",
            "眼底",
            "肾病",
        ],
        AgentType.HYPERTENSION: [
            "血压",
            "高血压",
            "降压",
            "收缩压",
            "舒张压",
            "低压",
            "高压",
            "心血管",
            "脑卒中",
        ],
        AgentType.NUTRITION: [
            "饮食",
            "食物",
            "营养",
            "吃",
            "食谱",
            "GI",
            "碳水",
            "蛋白质",
            "脂肪",
            "卡路里",
            "减肥",
        ],
        AgentType.COACH: ["运动", "锻炼", "跑步", "走路", "运动处方", "体力", "减肥", "健身"],
        AgentType.MEDICATION: [
            "药",
            "用药",
            "服药",
            "剂量",
            "副作用",
            "药物",
            "吃法",
            "禁忌",
            "相互作用",
        ],
        AgentType.PSYCHOLOGY: [
            "焦虑",
            "抑郁",
            "压力",
            "心情",
            "情绪",
            "失眠",
            "心理",
            "害怕",
            "担心",
        ],
        AgentType.REHABILITATION: [
            "康复",
            "恢复",
            "训练",
            "理疗",
            "按摩",
            "锻炼",
            "关节",
            "肌肉",
            "行动",
        ],
        AgentType.COGNITIVE: [
            "认知",
            "记忆力",
            "记忆",
            "健忘",
            "忘事",
            "脑子",
            "老年痴呆",
            "阿尔茨海默",
            "认知衰退",
            "认知评估",
            "注意力",
            "反应迟钝",
            "脑子不好使",
            "记不住",
        ],
    }

    def classify(self, query: str) -> AgentType:
        """意图分类"""
        query_lower = query.lower()

        # 统计各类型匹配数量
        matches = {}
        for agent_type, keywords in self.INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw.lower() in query_lower)
            if count > 0:
                matches[agent_type] = count

        # 返回匹配最多的类型
        if matches:
            return max(matches, key=matches.get)

        return AgentType.GENERAL


class AgentSelector:
    """Agent选择器"""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.loader = AgentLoader()
        self._agents_cache = None

    @property
    def agents(self) -> Dict[str, AgentDefinition]:
        """获取所有Agent(缓存)"""
        if self._agents_cache is None:
            self._agents_cache = self.load_all_agents()
        return self._agents_cache

    def load_all_agents(self) -> Dict[str, AgentDefinition]:
        """加载所有Agent"""
        return self.loader.load_all()

    def select(self, query: str, patient_context: Dict = None) -> str:
        """选择最合适的Agent类型"""
        # 如果有患者上下文，优先根据病种选择
        if patient_context and patient_context.get("diseases"):
            diseases = patient_context["diseases"]
            if "diabetes" in diseases or "糖尿病" in diseases:
                return AgentType.DIABETES.value
            elif "hypertension" in diseases or "高血压" in diseases:
                return AgentType.HYPERTENSION.value

        # 否则使用意图分类
        return self.classifier.classify(query).value

    def get_agent_definition(self, agent_type: str) -> Optional[AgentDefinition]:
        """获取Agent定义"""
        return self.agents.get(agent_type)

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有Agent列表"""
        return [
            {
                "type": agent_type,
                "name": agent.metadata.name,
                "description": agent.metadata.description,
                "color": agent.metadata.color,
                "emoji": agent.metadata.emoji,
            }
            for agent_type, agent in self.agents.items()
        ]


class IntelligentAgentSelector:
    """
    基于LLM的智能Agent选择器
    根据用户问题，智能判断需要调用哪些Agent
    """

    AGENT_PROFILES = """
你是一个医疗健康Agent智能路由专家。你的任务是根据用户的问题，判断需要哪些专业的Agent来回答。

## 可用Agent列表：

1. **diabetes** (糖尿病专家)
   - 专业领域：血糖管理、糖尿病用药、胰岛素、糖尿病饮食运动、并发症预防
   - 触发关键词：血糖、糖尿病、胰岛素、糖化血红蛋白、HbA1c

2. **hypertension** (高血压专家)
   - 专业领域：血压监测、降压药、高血压饮食、心血管健康
   - 触发关键词：血压、高血压、舒张压、收缩压、头晕头痛

3. **nutrition** (营养师)
   - 专业领域：糖尿病饮食、高血压饮食、食谱推荐、食物GI值、营养评估
   - 触发关键词：饮食、食物、营养、食谱、GI、热量、三餐

4. **coach** (健康教练)
   - 专业领域：运动处方、习惯养成、减重目标设定、日常锻炼
   - 触发关键词：运动、锻炼、跑步、走路、减肥、体力活动

5. **medication** (用药顾问)
   - 专业领域：药物咨询、用药安全、药物相互作用、用药时间
   - 触发关键词：药、用药、服用、副作用、药物相互作用、二甲双胍

6. **psychology** (心理支持)
   - 专业领域：情绪疏导、压力管理、焦虑抑郁、失眠放松
   - 触发关键词：焦虑、抑郁、失眠、情绪、心理、压力、不开心

7. **rehabilitation** (康复专家)
   - 专业领域：脑梗康复、中风康复、偏瘫训练、功能恢复
   - 触发关键词：康复、脑梗、中风、偏瘫、术后、功能恢复、训练

8. **cognitive** (认知评估师)
   - 专业领域：认知功能评估、记忆力检测、早期认知衰退筛查、认知训练建议
   - 触发关键词：认知、记忆力、健忘、忘事、老年痴呆、阿尔茨海默、记不住、注意力

9. **general** (健康助手)
   - 专业领域：通用健康咨询、就医指引、健康科普
   - 触发关键词：其他健康问题

## 判断规则：

1. **优先级规则**：
   - 问题涉及具体疾病 → 对应专科Agent优先
   - 问题涉及多个领域 → 必须包含所有相关Agent，不要遗漏
   - 问题涉及药物和疾病 → medication + 对应专科
   - 问题涉及饮食 + 具体疾病 → nutrition + 对应专科
   - 问题涉及运动 + 具体疾病 → coach + 对应专科
   - 慢病管理问题通常涉及多个维度（疾病+用药+饮食+运动），应选择3-5个相关Agent

2. **智能判断示例**：
   - "血糖高怎么办" → ["diabetes", "medication", "nutrition"]
   - "糖尿病饮食要注意什么" → ["diabetes", "nutrition", "coach"]
   - "高血压吃什么药" → ["hypertension", "medication", "nutrition"]
   - "空腹血糖8.5，服用二甲双胍，血糖控制不好" → ["diabetes", "medication", "nutrition", "coach"]
   - "最近失眠焦虑" → ["psychology", "nutrition", "coach"]
   - "脑梗康复怎么做" → ["rehabilitation", "coach", "nutrition"]
   - "你好" → ["general"]
"""

    def __init__(self):
        self.agent_profiles = self.AGENT_PROFILES

    async def select_agents(self, query: str, patient_context: Dict = None) -> List[str]:
        """
        智能选择需要调用的Agent

        Args:
            query: 用户问题
            patient_context: 患者上下文（可选）

        Returns:
            需要调用的Agent类型列表
        """
        from app.services.llm_client import LLMClient

        # 构建prompt
        prompt = f"""
## 用户问题：
{query}

"""

        # 如果有患者上下文，加入提示
        if patient_context:
            diseases = patient_context.get("diseases", [])
            medications = patient_context.get("medications", [])
            if diseases:
                prompt += f"\n## 患者已有疾病：{', '.join(diseases)}"
            if medications:
                prompt += f"\n## 患者正在服用：{', '.join(medications)}"

        prompt += """

## 请返回JSON格式的选择结果：
```json
{
  "selected_agents": ["agent1", "agent2", ...],
  "reasoning": "选择理由",
  "urgency": "normal|high|critical"
}
```

规则：
- selected_agents: 选择所有与问题相关的Agent，通常3-5个，确保覆盖疾病、用药、饮食、运动等所有相关维度
- reasoning: 简要说明为什么选择这些Agent
- urgency: 问题紧急程度（critical=危及生命需立即就医，high=重要需关注，normal=普通问题）
"""

        try:
            client = LLMClient()
            response = await client.chat(
                messages=[
                    {"role": "system", "content": self.agent_profiles},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            # 解析LLM返回的结果
            result = self._parse_llm_response(response)
            if result is None:
                logger.warning("[IntelligentAgentSelector] LLM response parse failed, using keyword fallback")
                return self._fallback_keyword_match(query)
            
            selected = result.get("selected_agents", [])
            if not selected or selected == ["general"]:
                logger.warning("[IntelligentAgentSelector] LLM selected only general, trying keyword fallback")
                keyword_agents = self._fallback_keyword_match(query)
                if keyword_agents != ["general"]:
                    return keyword_agents
            
            logger.info(
                f"[IntelligentAgentSelector] Query: {query[:30]}... -> Agents: {selected}"
            )
            return selected

        except Exception as e:
            logger.error(f"[IntelligentAgentSelector] Error: {e}")
            # 降级：使用关键词匹配
            return self._fallback_keyword_match(query)

    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM返回的JSON"""
        try:
            json_start = response.find("```json")
            if json_start != -1:
                json_end = response.find("```", json_start + 7)
                json_str = response[json_start + 7 : json_end].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            if "selected_agents" not in result or not result["selected_agents"]:
                raise ValueError("No agents selected")
            return result
        except:
            return None

    def _fallback_keyword_match(self, query: str) -> List[str]:
        """关键词匹配降级方案 - 匹配所有相关Agent并自动关联"""
        agents = []
        query_lower = query.lower()

        has_diabetes = any(kw in query_lower for kw in ["血糖", "糖尿病", "胰岛素", "HbA1c", "糖化", "空腹血糖", "餐后血糖", "二甲双胍", "格列美脲", "糖耐量"])
        has_hypertension = any(kw in query_lower for kw in ["血压", "高血压", "舒张压", "收缩压", "降压"])
        has_medication = any(kw in query_lower for kw in ["药", "用药", "服用", "二甲双胍", "阿司匹林", "副作用", "格列美脲", "胰岛素", "降压药", "剂量", "调整方案"])
        has_nutrition = any(kw in query_lower for kw in ["饮食", "食物", "营养", "食谱", "GI", "热量", "三餐", "吃什么", "少吃"])
        has_coach = any(kw in query_lower for kw in ["运动", "锻炼", "跑步", "走路", "减重", "减肥", "体力活动", "控制不好"])
        has_psychology = any(kw in query_lower for kw in ["焦虑", "抑郁", "失眠", "情绪", "心理", "压力", "不开心", "烦躁"])
        has_rehabilitation = any(kw in query_lower for kw in ["康复", "脑梗", "中风", "偏瘫", "术后", "功能恢复"])
        has_cognitive = any(kw in query_lower for kw in ["认知", "记忆力", "健忘", "忘事", "老年痴呆", "阿尔茨海默", "记不住", "注意力", "脑子不好使", "反应迟钝"])

        if has_diabetes:
            agents.append("diabetes")
        if has_hypertension:
            agents.append("hypertension")
        if has_medication:
            agents.append("medication")
        if has_nutrition:
            agents.append("nutrition")
        if has_coach:
            agents.append("coach")
        if has_psychology:
            agents.append("psychology")
        if has_rehabilitation:
            agents.append("rehabilitation")
        if has_cognitive:
            agents.append("cognitive")

        # 智能关联：慢病管理问题自动补充相关Agent
        if has_diabetes and "medication" not in agents:
            agents.append("medication")
        if has_diabetes and "nutrition" not in agents:
            agents.append("nutrition")
        if has_hypertension and "medication" not in agents:
            agents.append("medication")
        if has_hypertension and "nutrition" not in agents:
            agents.append("nutrition")
        if has_medication and not has_diabetes and not has_hypertension:
            if "diabetes" not in agents and any(kw in query_lower for kw in ["血糖", "胰岛素", "糖"]):
                agents.append("diabetes")

        if not agents:
            agents.append("general")

        return agents


# 全局单例
agent_selector = AgentSelector()
intelligent_selector = IntelligentAgentSelector()
