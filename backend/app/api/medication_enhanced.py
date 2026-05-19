"""
用药提醒增强API
包括：定时提醒、依从性统计、智能提醒
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.services.family_service import MedicationComplianceService, HealthAlertService
from app.models.family_models import MedicationReminderEnhanced, MedicationRecordEnhanced
from app.utils.database import get_db

router = APIRouter(prefix="/api/v1/medication-enhanced", tags=["用药提醒增强"])


# ========== 数据模型 ==========


class MedicationReminderRequest(BaseModel):
    patient_id: str
    drug_name: str
    dosage: str
    frequency: str
    times: List[str]  # ["08:00", "12:00", "20:00"]
    start_date: str
    end_date: Optional[str] = None
    notify_children: bool = True


class MedicationRecordRequest(BaseModel):
    patient_id: str
    reminder_id: str
    drug_name: str
    dosage: str
    scheduled_time: str
    taken_time: Optional[str] = None
    status: str  # taken, missed, skipped
    skip_reason: Optional[str] = None


class ComplianceQuery(BaseModel):
    patient_id: str
    days: int = 30


class CheckMissedMedication(BaseModel):
    patient_id: str


# ========== 用药提醒API ==========


@router.post("/reminder/create")
async def create_medication_reminder(
    request: MedicationReminderRequest, db: Session = Depends(get_db)
):
    """创建用药提醒"""
    try:
        reminder = MedicationReminderEnhanced(
            id=str(uuid.uuid4()),
            patient_id=request.patient_id,
            drug_name=request.drug_name,
            dosage=request.dosage,
            frequency=request.frequency,
            times=request.times,
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date) if request.end_date else None,
            notify_children=request.notify_children,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        return {
            "success": True,
            "reminder_id": reminder.id,
            "created_at": reminder.created_at.isoformat()
            if reminder.created_at
            else datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminder/{patient_id}/list")
async def get_medication_reminders(patient_id: str):
    """获取用药提醒列表"""
    try:
        from app.utils.database import get_db_session
        from sqlalchemy import select

        async with get_db_session() as session:
            result = await session.execute(
                select(MedicationReminderEnhanced)
                .where(MedicationReminderEnhanced.patient_id == patient_id)
                .where(MedicationReminderEnhanced.enabled == True)
            )
            reminders = result.scalars().all()

            return {
                "success": True,
                "reminders": [
                    {
                        "id": r.id,
                        "drug_name": r.drug_name,
                        "dosage": r.dosage,
                        "frequency": r.frequency,
                        "times": r.times,
                        "start_date": r.start_date.isoformat() if r.start_date else None,
                        "notify_children": r.notify_children,
                    }
                    for r in reminders
                ],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/reminder/{reminder_id}/toggle")
async def toggle_reminder(reminder_id: str, enabled: bool):
    """启用/禁用用药提醒"""
    try:
        from app.utils.database import get_db_session
        from sqlalchemy import select

        async with get_db_session() as session:
            result = await session.execute(
                select(MedicationReminderEnhanced).where(
                    MedicationReminderEnhanced.id == reminder_id
                )
            )
            reminder = result.scalars().first()

            if not reminder:
                raise HTTPException(status_code=404, detail="提醒不存在")

            reminder.enabled = enabled
            await session.commit()

            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 服药记录API ==========


@router.post("/record")
async def record_medication(request: MedicationRecordRequest):
    """记录服药"""
    try:
        from app.utils.database import get_db_session

        async with get_db_session() as session:
            taken_time = None
            if request.taken_time:
                taken_time = datetime.fromisoformat(request.taken_time)

            record = MedicationRecordEnhanced(
                id=str(uuid.uuid4()),
                patient_id=request.patient_id,
                reminder_id=request.reminder_id,
                drug_name=request.drug_name,
                dosage=request.dosage,
                scheduled_time=datetime.fromisoformat(request.scheduled_time),
                taken_time=taken_time,
                status=request.status,
                skip_reason=request.skip_reason,
            )
            session.add(record)
            await session.commit()

            # 检查是否漏服，需要触发预警
            if request.status == "missed":
                await MedicationComplianceService.check_and_alert_missed_medication(
                    request.patient_id
                )

            return {
                "success": True,
                "record_id": record.id,
                "created_at": record.created_at.isoformat(),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/record/{patient_id}/history")
async def get_medication_history(patient_id: str, days: int = 7):
    """获取服药历史"""
    try:
        from app.utils.database import get_db_session
        from sqlalchemy import select, and_

        async with get_db_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)

            result = await session.execute(
                select(MedicationRecordEnhanced)
                .where(
                    and_(
                        MedicationRecordEnhanced.patient_id == patient_id,
                        MedicationRecordEnhanced.scheduled_time >= cutoff,
                    )
                )
                .order_by(MedicationRecordEnhanced.scheduled_time.desc())
            )
            records = result.scalars().all()

            return {
                "success": True,
                "records": [
                    {
                        "id": r.id,
                        "drug_name": r.drug_name,
                        "dosage": r.dosage,
                        "scheduled_time": r.scheduled_time.isoformat(),
                        "taken_time": r.taken_time.isoformat() if r.taken_time else None,
                        "status": r.status,
                        "skip_reason": r.skip_reason,
                    }
                    for r in records
                ],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/record/{patient_id}/today")
async def get_today_medication(patient_id: str):
    """获取今日用药计划"""
    try:
        from app.utils.database import get_db_session
        from sqlalchemy import select, and_

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        async with get_db_session() as session:
            # 获取今日提醒
            result = await session.execute(
                select(MedicationReminderEnhanced).where(
                    and_(
                        MedicationReminderEnhanced.patient_id == patient_id,
                        MedicationReminderEnhanced.enabled == True,
                    )
                )
            )
            reminders = result.scalars().all()

            # 获取今日记录
            record_result = await session.execute(
                select(MedicationRecordEnhanced).where(
                    and_(
                        MedicationRecordEnhanced.patient_id == patient_id,
                        MedicationRecordEnhanced.scheduled_time >= today_start,
                        MedicationRecordEnhanced.scheduled_time < today_end,
                    )
                )
            )
            records = record_result.scalars().all()

            # 合并
            today_meds = []
            for reminder in reminders:
                for time_str in reminder.times:
                    # 检查是否有记录
                    record = next((r for r in records if r.drug_name == reminder.drug_name), None)

                    today_meds.append(
                        {
                            "reminder_id": reminder.id,
                            "drug_name": reminder.drug_name,
                            "dosage": reminder.dosage,
                            "scheduled_time": time_str,
                            "status": record.status if record else "pending",
                        }
                    )

            return {
                "success": True,
                "medications": today_meds,
                "taken_count": sum(1 for r in records if r.status == "taken"),
                "total_count": len(today_meds),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 依从性统计API ==========


@router.post("/compliance")
async def get_medication_compliance(request: ComplianceQuery):
    """获取用药依从性统计"""
    try:
        compliance = await MedicationComplianceService.calculate_compliance(
            request.patient_id, request.days
        )

        # 生成评估建议
        advice = []
        if compliance["compliance_rate"] >= 90:
            advice.append("用药依从性优秀，继续保持！")
        elif compliance["compliance_rate"] >= 70:
            advice.append("用药依从性良好，请继续坚持")
        elif compliance["compliance_rate"] >= 50:
            advice.append("用药依从性一般，建议设置更多提醒")
        else:
            advice.append("用药依从性较差，建议咨询医生调整用药方案")

        return {"success": True, "compliance": compliance, "advice": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-missed")
async def check_missed_medication(request: CheckMissedMedication):
    """检查漏服药物并预警"""
    try:
        alert = await MedicationComplianceService.check_and_alert_missed_medication(
            request.patient_id
        )

        if alert:
            return {
                "success": True,
                "alert_triggered": True,
                "alert": {
                    "title": alert.title,
                    "content": alert.content,
                    "severity": alert.severity,
                },
            }

        return {"success": True, "alert_triggered": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 智能提醒API ==========


@router.get("/reminder/{patient_id}/next")
async def get_next_medication(patient_id: str):
    """获取下次用药提醒"""
    try:
        from app.utils.database import get_db_session
        from sqlalchemy import select

        async with get_db_session() as session:
            result = await session.execute(
                select(MedicationReminderEnhanced).where(
                    MedicationReminderEnhanced.patient_id == patient_id,
                    MedicationReminderEnhanced.enabled == True,
                )
            )
            reminders = result.scalars().all()

            if not reminders:
                return {"success": True, "next_reminder": None}

            # 计算下次用药时间
            now = datetime.now()
            next_reminder = None
            min_diff = float("inf")

            for reminder in reminders:
                for time_str in reminder.times:
                    hour, minute = map(int, time_str.split(":"))
                    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # 如果今天已过，则计算明天
                    if scheduled <= now:
                        scheduled += timedelta(days=1)

                    diff = (scheduled - now).total_seconds()
                    if diff < min_diff:
                        min_diff = diff
                        next_reminder = {
                            "drug_name": reminder.drug_name,
                            "dosage": reminder.dosage,
                            "scheduled_time": scheduled.isoformat(),
                            "minutes_until": int(diff / 60),
                        }

            return {"success": True, "next_reminder": next_reminder}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家人提醒API ==========


@router.get("/family/{patient_id}/child-summary")
async def get_child_medication_summary(patient_id: str):
    """获取子女端的用药摘要"""
    try:
        # 获取今日用药
        from app.utils.database import get_db_session
        from sqlalchemy import select, and_

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        async with get_db_session() as session:
            # 获取今日记录
            result = await session.execute(
                select(MedicationRecordEnhanced).where(
                    and_(
                        MedicationRecordEnhanced.patient_id == patient_id,
                        MedicationRecordEnhanced.scheduled_time >= today_start,
                    )
                )
            )
            records = result.scalars().all()

            taken = sum(1 for r in records if r.status == "taken")
            missed = sum(1 for r in records if r.status == "missed")
            total = len(records)

            # 获取依从性
            compliance = await MedicationComplianceService.calculate_compliance(patient_id, 30)

            return {
                "success": True,
                "summary": {
                    "today": {
                        "taken": taken,
                        "missed": missed,
                        "total": total,
                        "completion_rate": round(taken / total * 100, 1) if total > 0 else 0,
                    },
                    "monthly_compliance": compliance,
                    "needs_attention": missed > 0 or compliance["compliance_rate"] < 70,
                },
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
