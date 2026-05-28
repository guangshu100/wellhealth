"""健康监控定时任务"""
import logging
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="check_vital_signs")
def check_vital_signs():
    """定时检查患者体征数据，检测异常"""
    logger.info("Starting vital signs check...")
    try:
        from app.utils.database import get_db_session
        from app.models.models import VitalRecord
        from sqlalchemy import desc

        with get_db_session() as db:
            # 查询最近30分钟内的体征记录
            cutoff = datetime.utcnow() - timedelta(minutes=30)
            recent_vitals = db.query(VitalRecord).filter(
                VitalRecord.recorded_at >= cutoff
            ).all()

            alerts = []
            for vital in recent_vitals:
                alert = _analyze_vital_record(vital)
                if alert:
                    alerts.append(alert)

            logger.info(f"Vital signs check complete. Found {len(alerts)} alerts.")
            return {"checked": len(recent_vitals), "alerts": len(alerts)}
    except Exception as e:
        logger.error(f"Vital signs check failed: {e}")
        return {"error": str(e)}


@celery_app.task(name="check_medication_adherence")
def check_medication_adherence():
    """检查用药依从性"""
    logger.info("Starting medication adherence check...")
    try:
        from app.utils.database import get_db_session
        from app.models.family_models import MedicationRecordEnhanced

        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(hours=6)
            records = db.query(MedicationRecordEnhanced).filter(
                MedicationRecordEnhanced.scheduled_time >= cutoff,
                MedicationRecordEnhanced.status == "missed"
            ).all()

            missed_count = len(records)
            logger.info(f"Adherence check complete. Found {missed_count} missed doses.")
            return {"missed_doses": missed_count}
    except Exception as e:
        logger.error(f"Adherence check failed: {e}")
        return {"error": str(e)}


@celery_app.task(name="scan_data_quality")
def scan_data_quality():
    """扫描数据质量，检测指标缺失"""
    logger.info("Starting data quality scan...")
    try:
        from app.utils.database import get_db_session
        from app.models.models import Patient, VitalRecord
        from sqlalchemy import func

        with get_db_session() as db:
            # 检测缺失关键指标的患者
            cutoff = datetime.utcnow() - timedelta(days=30)

            # 获取活跃患者
            active_patients = db.query(Patient).all()

            missing_reports = []
            for patient in active_patients:
                vitals = db.query(VitalRecord).filter(
                    VitalRecord.patient_id == patient.id,
                    VitalRecord.recorded_at >= cutoff
                ).all()

                if not vitals:
                    missing_reports.append({
                        "patient_id": patient.id,
                        "patient_name": patient.name,
                        "missing_type": "all_vitals",
                        "missing_days": 30
                    })

            logger.info(f"Data quality scan complete. Found {len(missing_reports)} patients with missing data.")
            return {"patients_with_missing_data": len(missing_reports)}
    except Exception as e:
        logger.error(f"Data quality scan failed: {e}")
        return {"error": str(e)}


def _analyze_vital_record(vital) -> dict:
    """分析单条体征记录，返回异常信息"""
    if not vital or not vital.value:
        return None

    values = vital.value if isinstance(vital.value, dict) else {}
    alerts = []

    # 血糖检查
    blood_sugar = values.get("blood_sugar") or values.get("血糖")
    if blood_sugar:
        try:
            bs_val = float(blood_sugar)
            if bs_val > 11.1:
                alerts.append({"type": "high_blood_sugar", "value": bs_val, "severity": "high"})
            elif bs_val > 9.0:
                alerts.append({"type": "elevated_blood_sugar", "value": bs_val, "severity": "medium"})
        except (ValueError, TypeError):
            pass

    # 血压检查
    blood_pressure = values.get("blood_pressure") or values.get("血压")
    if blood_pressure and isinstance(blood_pressure, str):
        try:
            parts = blood_pressure.replace("/", " ").split()
            if len(parts) >= 2:
                systolic = int(parts[0])
                diastolic = int(parts[1])
                if systolic > 180 or diastolic > 110:
                    alerts.append({"type": "critical_blood_pressure", "value": blood_pressure, "severity": "critical"})
                elif systolic > 140 or diastolic > 90:
                    alerts.append({"type": "high_blood_pressure", "value": blood_pressure, "severity": "medium"})
        except (ValueError, TypeError):
            pass

    if alerts:
        return {"patient_id": vital.patient_id, "alerts": alerts}
    return None
