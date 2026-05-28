"""管理视角报表API"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from app.utils.database import get_db
from app.models.models import Patient
from app.models.family_models import MedicationRecordEnhanced

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/macro-stats")
async def get_macro_stats(db: Session = Depends(get_db)):
    """获取宏观统计数据"""
    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    cutoff = datetime.utcnow() - timedelta(days=30)
    new_this_month = db.query(func.count(Patient.id)).filter(
        Patient.created_at >= cutoff
    ).scalar() or 0

    active_patients = db.execute(text(
        "SELECT COUNT(DISTINCT patient_id) FROM glucose_records "
        "WHERE measurement_time >= :cutoff"
    ), {"cutoff": cutoff}).scalar() or 0

    active_rate = active_patients / total_patients if total_patients > 0 else 0

    return {
        "total_patients": total_patients,
        "new_this_month": new_this_month,
        "active_patients": active_patients,
        "active_rate": round(active_rate, 3),
    }


@router.get("/disease-distribution")
async def get_disease_distribution(db: Session = Depends(get_db)):
    """获取疾病分布数据"""
    rows = db.execute(text(
        "SELECT disease_name, COUNT(*) AS cnt FROM disease_records "
        "GROUP BY disease_name ORDER BY cnt DESC LIMIT 10"
    )).mappings().all()

    return {
        "by_disease": [{"disease": row["disease_name"], "count": row["cnt"]} for row in rows],
    }


@router.get("/adherence-stats")
async def get_adherence_stats(db: Session = Depends(get_db)):
    """获取依从性统计"""
    total_records = db.query(func.count(MedicationRecordEnhanced.id)).scalar() or 0
    taken_records = db.query(func.count(MedicationRecordEnhanced.id)).filter(
        MedicationRecordEnhanced.status == "taken"
    ).scalar() or 0

    overall_rate = taken_records / total_records if total_records > 0 else 0

    return {
        "overall_rate": round(overall_rate, 3),
        "total_records": total_records,
        "taken_records": taken_records,
    }


@router.get("/resource-utilization")
async def get_resource_utilization(db: Session = Depends(get_db)):
    """获取资源利用数据"""
    total_medications = db.execute(text(
        "SELECT COUNT(*) FROM medication_records"
    )).scalar() or 0

    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    avg_medications = total_medications / total_patients if total_patients > 0 else 0

    return {
        "total_prescriptions": total_medications,
        "avg_medications_per_patient": round(avg_medications, 2),
    }


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """获取Dashboard概览"""
    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    cutoff = datetime.utcnow() - timedelta(days=30)
    active_patients = db.execute(text(
        "SELECT COUNT(DISTINCT patient_id) FROM glucose_records "
        "WHERE measurement_time >= :cutoff"
    ), {"cutoff": cutoff}).scalar() or 0

    rows = db.execute(text(
        "SELECT disease_name, COUNT(*) AS cnt FROM disease_records "
        "GROUP BY disease_name ORDER BY cnt DESC LIMIT 5"
    )).mappings().all()

    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "top_diseases": [{"disease": row["disease_name"], "count": row["cnt"]} for row in rows],
    }
