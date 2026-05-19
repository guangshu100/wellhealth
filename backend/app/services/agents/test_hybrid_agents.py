"""
测试脚本 - 验证混合多 Agent 架构
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_agent_loader():
    """测试 Agent 加载器"""
    print("\n=== 测试 EnhancedAgentLoader ===")
    from app.services.agents.core.agent_loader import EnhancedAgentLoader

    loader = EnhancedAgentLoader()
    agents = loader.load_all()
    print(f"加载了 {len(agents)} 个 Agent:")
    for agent_type, agent in agents.items():
        print(f"  - {agent_type}: {agent.metadata.name}")
        print(f"    LLM配置: {agent.llm_config.provider}/{agent.llm_config.model}")

    diabetes_agent = loader.load("diabetes")
    if diabetes_agent:
        print(f"\n糖尿病 Agent 系统提示词长度: {len(diabetes_agent.system_prompt)} 字符")
        print(f"Agent 定义 Markdown:\n{diabetes_agent.to_markdown()[:500]}...")
    else:
        print("警告: 糖尿病 Agent 未找到")


async def test_llm_router():
    """测试 LLM 路由器"""
    print("\n=== 测试 LLMRouter ===")
    from app.services.agents.core.agent_loader import EnhancedAgentLoader
    from app.services.agents.core.llm_router import LLMRouter

    loader = EnhancedAgentLoader()
    router = LLMRouter()

    diabetes_agent = loader.load("diabetes")
    if diabetes_agent:
        client = router.get_client_for_agent(diabetes_agent)
        print(f"糖尿病 Agent 使用 Provider: {client.get_provider_name()}")


async def test_evidence_system():
    """测试证据系统 - Agency-Agents EvidenceCollector 模式"""
    print("\n=== 测试 EvidenceCollector & EvidenceQA ===")
    from app.services.agents.quality.quality_gate import (
        EvidenceCollector,
        EvidenceQA,
        EvidenceType,
    )

    collector = EvidenceCollector()

    collector.add_text_evidence("这是糖尿病饮食建议", "Agent 响应")
    collector.add_text_evidence("空腹血糖正常范围: 4.4-7.0 mmol/L", "医学参考")
    collector.add_code_evidence("```python\nprint('hello')\n```", "python", "代码示例")

    evidence = collector.get_evidence()
    print(f"收集了 {len(evidence)} 条证据:")
    for e in evidence:
        print(f"  - {e.type.value}: {e.description}")

    evidence_qa = EvidenceQA(collector)
    print("\n证据导出:")
    for e in collector.export():
        print(f"  {e['type']}: {e['description']}")


async def test_quality_gate():
    """测试质量门控"""
    print("\n=== 测试 QualityGate ===")
    from app.services.agents.core.agent_loader import EnhancedAgentLoader
    from app.services.agents.quality.quality_gate import QualityGate

    loader = EnhancedAgentLoader()
    quality_gate = QualityGate()

    diabetes_agent = loader.load("diabetes")

    test_responses = [
        "建议您每天监测血糖，保持健康饮食。",
        "你得了糖尿病，应该自己停药。",  # 危险响应
        "您的HbA1c指标正常，建议继续保持。",
    ]

    for response in test_responses:
        result = await quality_gate.validate(diabetes_agent, response)
        print(f"\n响应: {response[:50]}...")
        print(f"通过: {result.passed}, 分数: {result.score:.2f}")
        if result.reasons:
            print(f"原因: {result.reasons}")
        if result.evidence:
            print(f"证据数量: {len(result.evidence)}")


async def test_agent_spawner():
    """测试 Agent Spawner - Agency-Agents spawn 机制"""
    print("\n=== 测试 AgentSpawner ===")
    from app.services.agents.quality.quality_gate import AgentSpawner
    from app.services.agents.core.agent_executor import get_executor

    executor = get_executor()
    spawner = AgentSpawner(executor=executor.execute)

    tasks = [
        {"agent_type": "diabetes", "task": "分析血糖管理建议"},
        {"agent_type": "nutrition", "task": "提供营养饮食计划"},
    ]

    print(f"并行执行 {len(tasks)} 个 Agent...")
    results = await spawner.spawn_parallel(tasks)

    for i, result in enumerate(results):
        print(f"\nAgent {i + 1} 结果:")
        print(f"  Agent ID: {result.get('agent_id', 'N/A')}")
        if error := result.get("error"):
            print(f"  错误: {error}")
        elif agent_result := result.get("result"):
            print(f"  响应长度: {len(str(agent_result.response))} 字符")


async def test_enhanced_executor():
    """测试增强执行器"""
    print("\n=== 测试 EnhancedAgentExecutor ===")
    from app.services.agents.core.agent_executor import EnhancedAgentExecutor

    executor = EnhancedAgentExecutor(enable_quality_gate=True, max_retries=2)

    test_message = [{"role": "user", "content": "你好，糖尿病患者饮食应该注意什么？"}]

    try:
        result = await executor.execute(
            agent_type="diabetes",
            messages=test_message,
            enable_quality_check=True,
        )
        print(f"执行状态: {result.status.value}")
        print(f"响应长度: {len(result.response)} 字符")
        print(f"响应前200字: {result.response[:200]}...")
        if result.quality_result:
            print(f"质量检查: {result.quality_result.passed}")
            print(
                f"证据数量: {len(result.quality_result.evidence) if result.quality_result.evidence else 0}"
            )
    except Exception as e:
        print(f"执行失败: {e}")


async def test_multi_agent_dialogue():
    """测试多 Agent 对话"""
    print("\n=== 测试 MultiAgentDialogueManager ===")
    from app.services.agents.orchestrator.multi_agent_dialogue import MultiAgentDialogueManager

    dialogue_manager = MultiAgentDialogueManager()

    query = "我血糖偏高，饮食和运动有什么建议？"
    agents = ["diabetes", "nutrition", "coach"]

    try:
        result = await dialogue_manager.multi_agent_consultation(
            query=query,
            agents=agents,
            patient_context={"disease": "pre-diabetes"},
        )
        print(f"会诊成功: {result['success']}")
        print(f"参与 Agent: {result['participating_agents']}")
        print(f"共识内容: {result['consensus'][:200]}...")
        print(f"建议数量: {len(result['recommendations'])}")
    except Exception as e:
        print(f"会诊失败: {e}")


async def test_workflow_orchestrator():
    """测试工作流编排器"""
    print("\n=== 测试 WorkflowOrchestrator ===")
    from app.services.agents.orchestrator.workflow_orchestrator import (
        WorkflowOrchestrator,
        PipelineConfig,
        PipelineStage,
    )

    orchestrator = WorkflowOrchestrator()

    config = PipelineConfig(
        stages=[
            PipelineStage.PM,
            PipelineStage.ARCHITECT,
            PipelineStage.DEV,
            PipelineStage.QA,
            PipelineStage.DELIVERY,
        ],
        max_iterations=1,
        quality_threshold=0.5,
    )

    try:
        result = await orchestrator.execute_pipeline(
            task="设计一个血糖监测提醒功能",
            config=config,
            context={"user": "test_user"},
        )
        print(f"Pipeline 执行: {'成功' if result['success'] else '失败'}")
        print(f"迭代次数: {result.get('iterations', 0)}")
        if result.get("final_output"):
            print(f"最终输出: {result['final_output'][:200]}...")
    except Exception as e:
        print(f"Pipeline 失败: {e}")


async def test_health_pipeline():
    """测试健康咨询 Pipeline"""
    print("\n=== 测试 HealthConsultationPipeline ===")
    from app.services.agents.orchestrator.workflow_orchestrator import get_health_pipeline

    pipeline = get_health_pipeline()

    query = "我空腹血糖7.0，应该怎么调整饮食？"

    print("单 Agent 咨询:")
    result = await pipeline.consult(query, {"disease": "pre-diabetes"}, enable_consultation=False)
    print(f"  成功: {result['success']}")
    print(f"  Agent: {result.get('agent_type')}")

    print("\n多 Agent 会诊:")
    result = await pipeline.consult(query, {"disease": "pre-diabetes"}, enable_consultation=True)
    print(f"  成功: {result['success']}")
    print(f"  Agent数: {len(result.get('participating_agents', []))}")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("混合多 Agent 架构测试 (Agency-Agents 风格)")
    print("=" * 60)

    await test_agent_loader()
    await test_llm_router()
    await test_evidence_system()
    await test_quality_gate()
    await test_agent_spawner()
    await test_enhanced_executor()
    await test_multi_agent_dialogue()
    await test_workflow_orchestrator()
    await test_health_pipeline()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
