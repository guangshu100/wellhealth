"""工作流编排API"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ Request/Response Models ============

class PipelineRequest(BaseModel):
    """Pipeline执行请求"""
    task: str
    stages: Optional[List[str]] = ["pm", "architect", "dev", "qa", "integration", "delivery"]
    max_iterations: Optional[int] = 3
    quality_threshold: Optional[float] = 0.7
    context: Optional[Dict[str, Any]] = None


class ConsultationRequest(BaseModel):
    """健康咨询请求"""
    query: str
    patient_context: Optional[Dict[str, Any]] = None
    enable_consultation: Optional[bool] = False


class PipelineResponse(BaseModel):
    """Pipeline执行响应"""
    success: bool
    results: Optional[Dict[str, Any]] = None
    final_output: Optional[str] = None
    iterations: Optional[int] = None
    error: Optional[str] = None


class ConsultationResponse(BaseModel):
    """健康咨询响应"""
    success: bool
    agent_type: Optional[str] = None
    response: Optional[str] = None
    consultation: Optional[Dict[str, Any]] = None
    quality_passed: Optional[bool] = None


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    status: str
    available_stages: List[str]
    available_agents: List[str]
    version: str


# ============ API Endpoints ============

@router.get("/status", response_model=WorkflowStatusResponse)
async def get_workflow_status():
    """获取工作流状态"""
    try:
        from app.services.agents.orchestrator.workflow_orchestrator import PipelineStage
        from app.services.agents.core.agent_loader import EnhancedAgentLoader

        loader = EnhancedAgentLoader()
        agents = loader.load_all()

        return WorkflowStatusResponse(
            status="active",
            available_stages=[s.value for s in PipelineStage],
            available_agents=list(agents.keys()),
            version="2.0.0"
        )
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline", response_model=PipelineResponse)
async def execute_pipeline(request: PipelineRequest):
    """执行Pipeline工作流"""
    try:
        from app.services.agents.orchestrator.workflow_orchestrator import (
            WorkflowOrchestrator,
            PipelineStage,
            PipelineConfig,
        )

        # 转换阶段字符串为枚举
        stage_map = {s.value: s for s in PipelineStage}
        stages = [stage_map[s] for s in request.stages if s in stage_map]

        if not stages:
            stages = list(PipelineStage)

        config = PipelineConfig(
            stages=stages,
            max_iterations=request.max_iterations,
            quality_threshold=request.quality_threshold,
        )

        orchestrator = WorkflowOrchestrator()
        result = await orchestrator.execute_pipeline(
            task=request.task,
            config=config,
            context=request.context,
        )

        return PipelineResponse(**result)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return PipelineResponse(success=False, error=str(e))


@router.post("/consult", response_model=ConsultationResponse)
async def health_consultation(request: ConsultationRequest):
    """健康咨询（单Agent或多Agent会诊）"""
    try:
        from app.services.agents.orchestrator.workflow_orchestrator import get_health_pipeline

        pipeline = get_health_pipeline()
        result = await pipeline.consult(
            user_query=request.query,
            patient_context=request.patient_context,
            enable_consultation=request.enable_consultation,
        )

        return ConsultationResponse(**result)
    except Exception as e:
        logger.error(f"Consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_workflow_agents():
    """列出所有可用Agent"""
    try:
        from app.services.agents.core.agent_loader import EnhancedAgentLoader

        loader = EnhancedAgentLoader()
        agents = loader.load_all()

        return {
            "total": len(agents),
            "agents": [
                {
                    "type": agent_type,
                    "name": agent.metadata.name,
                    "role": agent.metadata.role,
                    "specialty": agent.metadata.specialty,
                    "emoji": agent.metadata.emoji,
                    "color": agent.metadata.color,
                    "llm_provider": agent.llm_config.provider,
                    "llm_model": agent.llm_config.model,
                }
                for agent_type, agent in agents.items()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
