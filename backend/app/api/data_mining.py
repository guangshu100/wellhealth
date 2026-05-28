"""数据挖掘API"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.services.data_mining_service import get_data_mining_service

logger = logging.getLogger(__name__)
router = APIRouter()


class MiningRequest(BaseModel):
    """挖掘请求基类"""
    patient_id: Optional[str] = None
    time_range: Optional[str] = "6m"


class DiseaseTrajectoryRequest(MiningRequest):
    """疾病轨迹请求"""
    pass


class IndicatorPatternRequest(BaseModel):
    """指标规律请求"""
    patient_id: str
    indicators: List[str] = ["blood_sugar", "blood_pressure"]


class WhatIfRequest(BaseModel):
    """仿真推演请求"""
    patient_id: str
    intervention: Dict[str, Any]


class ComorbidityRequest(BaseModel):
    """共病网络请求"""
    patient_ids: Optional[List[str]] = None
    min_support: Optional[float] = 0.05


class EpidemiologyRequest(BaseModel):
    """流行病学请求"""
    region: Optional[str] = "all"
    indicator: Optional[str] = "blood_sugar"
    threshold: Optional[float] = 2.0


@router.post("/disease-trajectory")
async def mine_disease_trajectory(
    request: DiseaseTrajectoryRequest,
    db: Session = Depends(get_db),
):
    """挖掘疾病轨迹"""
    try:
        service = get_data_mining_service()
        result = service.disease_trajectory(db, request.patient_id, request.time_range)
        return result
    except Exception as e:
        logger.error(f"Disease trajectory mining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicator-pattern")
async def mine_indicator_pattern(
    request: IndicatorPatternRequest,
    db: Session = Depends(get_db),
):
    """挖掘指标规律"""
    try:
        service = get_data_mining_service()
        result = service.indicator_pattern(db, request.patient_id, request.indicators)
        return result
    except Exception as e:
        logger.error(f"Indicator pattern mining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatif-simulation")
async def run_whatif_simulation(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
):
    """运行What-If仿真"""
    try:
        service = get_data_mining_service()
        result = service.whatif_simulation(db, request.patient_id, request.intervention)
        return result
    except Exception as e:
        logger.error(f"What-If simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comorbidity-network")
async def mine_comorbidity_network(
    request: ComorbidityRequest,
    db: Session = Depends(get_db),
):
    """挖掘共病网络"""
    try:
        service = get_data_mining_service()
        result = service.comorbidity_network(db, request.patient_ids, request.min_support)
        return result
    except Exception as e:
        logger.error(f"Comorbidity network mining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/epidemiology-alert")
async def epidemiology_alert(
    request: EpidemiologyRequest,
    db: Session = Depends(get_db),
):
    """流行病学预警"""
    try:
        service = get_data_mining_service()
        result = service.epidemiology_alert(db, request.region, request.indicator, request.threshold)
        return result
    except Exception as e:
        logger.error(f"Epidemiology alert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{task_id}")
async def get_mining_result(task_id: str, db: Session = Depends(get_db)):
    """查询挖掘结果"""
    try:
        from app.models.extension_models import MiningResultCache

        result = db.query(MiningResultCache).filter(MiningResultCache.id == task_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="结果不存在")
        return {
            "task_id": result.id,
            "query_type": result.query_type,
            "result": result.result,
            "computed_at": result.computed_at.isoformat() if result.computed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mining result: {e}")
        raise HTTPException(status_code=500, detail=str(e))
