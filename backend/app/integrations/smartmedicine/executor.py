"""Adapter to existing AgentExecutor. Legacy routes and chat tables are never used."""
import asyncio
import json


class RealEngine:
    _prepared = False
    _prepare_lock = asyncio.Lock()
    ASYNC_PROVIDERS = {"openai", "anthropic", "ollama", "siliconflow"}

    async def prepare(self):
        async with self._prepare_lock:
            if not type(self)._prepared:
                from app.services.knowledge_base import knowledge_manager
                await knowledge_manager.initialize()
                type(self)._prepared = True

    def __init__(self):
        self.executor = None
        self.checker = None

    @staticmethod
    def _load_dependencies():
        # Module imports and AgentLoader perform synchronous config/database work.
        # Keep them off the ASGI loop so auth, polling and cancellation stay responsive.
        from app.services.agent_executor import AgentExecutor
        from app.services.safety_checker import SafetyChecker
        return AgentExecutor(), SafetyChecker()

    async def load(self):
        if self.executor is None:
            self.executor, self.checker = await asyncio.to_thread(self._load_dependencies)

    async def opinion(self, agent, question, history, context, previous, round_number):
        await self.load()
        from app.services.agent_executor import AgentContext, Message
        definition = self.executor.selector.get_agent_definition(agent)
        if definition is None:
            raise RuntimeError("Requested agent is unavailable")
        cfg = definition.llm_config
        providers = {cfg.provider, cfg.fallback_provider} - {None, ""}
        if not providers.issubset(self.ASYNC_PROVIDERS):
            raise RuntimeError("Blocking SDK provider requires a dedicated queue worker")
        await self.prepare()
        prompt = "本轮用户问题：\n" + question
        prompt += "\n用户自述资料（未经核实，不是诊断）：\n" + json.dumps(context, ensure_ascii=False)
        if previous:
            snapshot = [{"agent":p["agent_name"], "opinion":p["content"][:2000]} for p in previous]
            prompt += "\n上一轮已通过输出检查的专家观点：\n" + json.dumps(snapshot, ensure_ascii=False)
            prompt += "\n请回应相关观点，明确补充信息和不确定性，不把其他专家推测当成患者事实。"
        prompt += "\n仅提供一般健康信息，不确诊、不提供具体药物剂量、不替代医生治疗。"
        # Independent mutable context for every expert, never the global SessionManager.
        ctx = AgentContext(patient_context=dict(context),
                           messages=[Message(role=m["role"], content=m["content"]) for m in history])
        result = await self.executor.execute(prompt, ctx, agent)
        if not result.success or self.executor._is_error_response(result.response):
            raise RuntimeError("Expert provider unavailable")
        checked = self.checker.check(result.response)
        return {"content":result.response, "sources":result.sources,
                "blocked":not checked.safe or checked.level.value == "danger"}

    async def summary(self, question, opinions):
        from app.services.llm_client import LLMClient
        evidence = [{"expert":p["agent_name"], "round":p["round"], "opinion":p["content"][:2400]}
                    for p in opinions]
        prompt = "用户问题：" + question + "\n专家观点：" + json.dumps(evidence, ensure_ascii=False)
        prompt += "\n按生活方式、监测随访、需咨询医生事项归纳；指出分歧，不编造共识或事实。"
        client = LLMClient()
        if client.provider_name not in self.ASYNC_PROVIDERS:
            raise RuntimeError("Blocking summary provider is unsupported by the demo runner")
        text = await client.chat_with_system(
            system_prompt="你是健康信息整理助手。只总结给出的安全意见，不确诊、不提供剂量、不替代医生治疗。",
            user_message=prompt, temperature=0.3, max_tokens=1500)
        if self.executor._is_error_response(text):
            raise RuntimeError("Summary provider unavailable")
        checked = self.checker.check(text)
        return {"content":text, "blocked":not checked.safe or checked.level.value == "danger"}
