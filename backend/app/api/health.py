"""
健康数据管理API
包括：健康数据录入、趋势查看、预警管理
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models import VitalRecord, Patient, HealthAlert

router = APIRouter(prefix="/api/v1/health", tags=["健康数据"])


# ========== 数据模型 ==========


class HealthDataRecord(BaseModel):
    patient_id: str
    vital_type: str
    value: Dict[str, Any]
    recorded_at: Optional[str] = None
    notes: Optional[str] = None


class HealthDataRecordAdd(BaseModel):
    patient_id: str
    type: str
    value: float
    unit: str = ""
    notes: Optional[str] = None
    recorded_at: Optional[str] = None


class AlertResolve(BaseModel):
    alert_id: str
    resolution: str


# ========== 健康数据API ==========


@router.post("/record/add")
async def record_health_data(data: HealthDataRecordAdd, db: Session = Depends(get_db)):
    """记录健康数据"""
    try:
        record_id = str(uuid.uuid4())
        recorded_at = (
            datetime.fromisoformat(data.recorded_at) if data.recorded_at else datetime.utcnow()
        )

        # 统一存储格式
        if data.type == "blood_pressure":
            # 血压存储格式: {"systolic": 120, "diastolic": 80}
            value_dict = {"value": data.value, "unit": data.unit}
        else:
            value_dict = {"value": data.value, "unit": data.unit}

        record = VitalRecord(
            id=record_id,
            patient_id=data.patient_id,
            vital_type=data.type,
            value=value_dict,
            recorded_at=recorded_at,
            notes=data.notes,
        )
        db.add(record)
        db.commit()

        # 检查是否需要生成预警
        await _check_and_create_alert(db, data.patient_id, data.type, data.value)

        return {"success": True, "record_id": record_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{patient_id}")
async def get_health_records(
    patient_id: str, vital_type: Optional[str] = None, days: int = 30, db: Session = Depends(get_db)
):
    """获取健康记录"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(VitalRecord).where(
            and_(VitalRecord.patient_id == patient_id, VitalRecord.recorded_at >= cutoff)
        )

        if vital_type:
            query = query.where(VitalRecord.vital_type == vital_type)

        query = query.order_by(VitalRecord.recorded_at.desc())

        result = db.execute(query)
        records = result.scalars().all()

        return {
            "success": True,
            "records": [
                {
                    "id": r.id,
                    "patient_id": r.patient_id,
                    "type": r.vital_type,
                    "value": r.value.get("value") if isinstance(r.value, dict) else r.value,
                    "unit": r.value.get("unit", "") if isinstance(r.value, dict) else "",
                    "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
                    "notes": r.notes,
                }
                for r in records
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{patient_id}")
async def get_health_trends(
    patient_id: str, type: str = "blood_sugar", db: Session = Depends(get_db)
):
    """获取健康趋势"""
    try:
        days = 30
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = db.execute(
            select(VitalRecord)
            .where(
                and_(
                    VitalRecord.patient_id == patient_id,
                    VitalRecord.vital_type == type,
                    VitalRecord.recorded_at >= cutoff,
                )
            )
            .order_by(VitalRecord.recorded_at.asc())
        )
        records = result.scalars().all()

        if not records:
            return {
                "success": True,
                "trend": {"data": [], "avg": 0, "min": 0, "max": 0, "trend": "stable"},
            }

        # 提取数值并计算统计
        values = []
        data_points = []
        for r in records:
            val = r.value.get("value") if isinstance(r.value, dict) else r.value
            if isinstance(val, (int, float)):
                values.append(val)
                data_points.append(
                    {"date": r.recorded_at.strftime("%m/%d") if r.recorded_at else "", "value": val}
                )

        if not values:
            return {
                "success": True,
                "trend": {"data": [], "avg": 0, "min": 0, "max": 0, "trend": "stable"},
            }

        avg = sum(values) / len(values)

        # 计算趋势
        if len(values) >= 7:
            first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
            second_half = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)
            if second_half > first_half * 1.05:
                trend = "rising"
            elif second_half < first_half * 0.95:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "success": True,
            "trend": {
                "data": data_points,
                "avg": round(avg, 1),
                "min": min(values),
                "max": max(values),
                "trend": trend,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/summary")
async def get_health_summary(patient_id: str, days: int = 7, db: Session = Depends(get_db)):
    """获取健康数据摘要"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = db.execute(
            select(VitalRecord).where(
                and_(VitalRecord.patient_id == patient_id, VitalRecord.recorded_at >= cutoff)
            )
        )
        records = result.scalars().all()

        # 按类型分组
        by_type = {}
        for r in records:
            if r.vital_type not in by_type:
                by_type[r.vital_type] = []
            val = r.value.get("value") if isinstance(r.value, dict) else r.value
            if isinstance(val, (int, float)):
                by_type[r.vital_type].append(val)

        # 计算统计
        summary = {}
        for vital_type, vals in by_type.items():
            if vals:
                summary[vital_type] = {
                    "count": len(vals),
                    "avg": round(sum(vals) / len(vals), 1),
                    "min": min(vals),
                    "max": max(vals),
                }

        return {"success": True, "summary": summary, "period_days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 预警API ==========


@router.get("/alerts/{patient_id}")
async def get_patient_alerts(patient_id: str, days: int = 30, db: Session = Depends(get_db)):
    """获取健康预警"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = db.execute(
            select(HealthAlert)
            .where(and_(HealthAlert.patient_id == patient_id, HealthAlert.created_at >= cutoff))
            .order_by(HealthAlert.created_at.desc())
        )
        alerts = result.scalars().all()

        return {
            "success": True,
            "alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "title": a.title,
                    "content": a.content,
                    "severity": a.severity,
                    "is_resolved": a.is_resolved,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert/resolve")
async def resolve_alert(request: AlertResolve, db: Session = Depends(get_db)):
    """处理预警"""
    try:
        result = db.execute(select(HealthAlert).where(HealthAlert.id == request.alert_id))
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail="预警不存在")

        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.commit()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ========== 内部函数 ==========


async def _check_and_create_alert(db: Session, patient_id: str, vital_type: str, value: float):
    """检查并创建预警"""
    # 阈值配置
    thresholds = {
        "blood_pressure": {"high": 140, "low": 90},
        "blood_sugar_fasting": {"high": 7.0, "low": 4.4},
        "heart_rate": {"high": 100, "low": 60},
    }

    # 获取当前类型对应的阈值
    threshold = None
    for key, t in thresholds.items():
        if key in vital_type or vital_type in key:
            threshold = t
            break

    if not threshold:
        return

    alert_triggered = False
    alert_content = ""

    if value > threshold.get("high", float("inf")):
        alert_triggered = True
        alert_content = f"{vital_type}偏高: {value}"
    elif value < threshold.get("low", float("-inf")):
        alert_triggered = True
        alert_content = f"{vital_type}偏低: {value}"

    if alert_triggered:
        alert = HealthAlert(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            alert_type="data_abnormal",
            title="健康数据异常",
            content=alert_content,
            severity="medium",
            vital_type=vital_type,
            vital_value={"value": value},
        )
        db.add(alert)
        db.commit()
