"""健康计划API"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class GoalInput(BaseModel):
    description: str
    target: Optional[str] = None
    achieved: bool = False


class MilestoneInput(BaseModel):
    description: str
    target_date: Optional[str] = None
    completed: bool = False


class CreatePlanRequest(BaseModel):
    patient_id: str
    plan_type: str
    goals: List[GoalInput] = []
    milestones: List[MilestoneInput] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class UpdatePlanRequest(BaseModel):
    status: Optional[str] = None
    goals: Optional[List[GoalInput]] = None
    milestones: Optional[List[MilestoneInput]] = None


@router.get("/patient/{patient_id}")
async def get_patient_plans(
    patient_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取患者的健康计划列表"""
    try:
        from app.models.extension_models import HealthPlan
        query = db.query(HealthPlan).filter(HealthPlan.patient_id == patient_id)
        if status:
            query = query.filter(HealthPlan.status == status)
        plans = query.order_by(HealthPlan.created_at.desc()).all()

        return {
            "plans": [
                {
                    "id": p.id,
                    "patient_id": p.patient_id,
                    "plan_type": p.plan_type,
                    "goals": p.goals or [],
                    "milestones": p.milestones or [],
                    "status": p.status,
                    "start_date": p.start_date.isoformat() if p.start_date else None,
                    "end_date": p.end_date.isoformat() if p.end_date else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in plans
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get patient plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_plan(
    request: CreatePlanRequest,
    db: Session = Depends(get_db),
):
    """创建健康计划"""
    try:
        from app.models.extension_models import HealthPlan
        plan = HealthPlan(
            id=str(uuid.uuid4()),
            patient_id=request.patient_id,
            plan_type=request.plan_type,
            goals=[g.model_dump() for g in request.goals],
            milestones=[m.model_dump() for m in request.milestones],
            status="active",
            start_date=datetime.fromisoformat(request.start_date) if request.start_date else None,
            end_date=datetime.fromisoformat(request.end_date) if request.end_date else None,
            created_at=datetime.utcnow(),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        return {
            "id": plan.id,
            "patient_id": plan.patient_id,
            "plan_type": plan.plan_type,
            "goals": plan.goals,
            "milestones": plan.milestones,
            "status": plan.status,
            "start_date": plan.start_date.isoformat() if plan.start_date else None,
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to create plan: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plan_id}")
async def update_plan(
    plan_id: str,
    request: UpdatePlanRequest,
    db: Session = Depends(get_db),
):
    """更新健康计划"""
    try:
        from app.models.extension_models import HealthPlan
        plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if request.status is not None:
            plan.status = request.status
        if request.goals is not None:
            plan.goals = [g.model_dump() for g in request.goals]
        if request.milestones is not None:
            plan.milestones = [m.model_dump() for m in request.milestones]

        db.commit()
        db.refresh(plan)

        return {
            "id": plan.id,
            "status": plan.status,
            "goals": plan.goals,
            "milestones": plan.milestones,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update plan: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
):
    """删除健康计划"""
    try:
        from app.models.extension_models import HealthPlan
        plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        db.delete(plan)
        db.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
