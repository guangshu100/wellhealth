"""
用药提醒API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class MedicationReminder(BaseModel):
    """用药提醒"""
    id: str
    patient_id: str
    drug_name: str
    dosage: str
    frequency: str
    times: List[str]
    start_date: str
    end_date: Optional[str] = None
    enabled: bool = True


class MedicationRecord(BaseModel):
    """服药记录"""
    id: str
    drug_name: str
    dosage: str
    scheduled_time: str
    taken_time: Optional[str] = None
    status: str


# 模拟数据存储
_reminders: dict = {}
_records: dict = {}


@router.get("/{patient_id}/medication-reminders")
async def get_reminders(patient_id: str):
    """获取用药提醒列表"""
    reminders = [r for r in _reminders.values() if r.patient_id == patient_id]
    return reminders


@router.post("/{patient_id}/medication-reminders")
async def add_reminder(patient_id: str, reminder: dict):
    """添加用药提醒"""
    reminder_id = f"rem_{len(_reminders) + 1}"
    new_reminder = MedicationReminder(
        id=reminder_id,
        patient_id=patient_id,
        drug_name=reminder.get("drug_name", ""),
        dosage=reminder.get("dosage", ""),
        frequency=reminder.get("frequency", ""),
        times=reminder.get("times", []),
        start_date=reminder.get("start_date", ""),
        end_date=reminder.get("end_date"),
        enabled=True
    )
    _reminders[reminder_id] = new_reminder
    return new_reminder


@router.put("/{patient_id}/medication-reminders/{reminder_id}")
async def update_reminder(patient_id: str, reminder_id: str, reminder: dict):
    """更新用药提醒"""
    if reminder_id not in _reminders:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    existing = _reminders[reminder_id]
    for key, value in reminder.items():
        if hasattr(existing, key):
            setattr(existing, key, value)
    
    return existing


@router.delete("/{patient_id}/medication-reminders/{reminder_id}")
async def delete_reminder(patient_id: str, reminder_id: str):
    """删除用药提醒"""
    if reminder_id in _reminders:
        del _reminders[reminder_id]
    return {"success": True}


@router.post("/{patient_id}/medication-reminders/{reminder_id}/mark-taken")
async def mark_taken(patient_id: str, reminder_id: str, data: dict):
    """标记已服药"""
    record_id = f"record_{len(_records) + 1}"
    taken_time = data.get("taken_time", datetime.now().isoformat())
    
    if reminder_id in _reminders:
        reminder = _reminders[reminder_id]
        record = MedicationRecord(
            id=record_id,
            drug_name=reminder.drug_name,
            dosage=reminder.dosage,
            scheduled_time=data.get("scheduled_time", ""),
            taken_time=taken_time,
            status="taken"
        )
        _records[record_id] = record
        
    return {"success": True, "taken_time": taken_time}


@router.get("/{patient_id}/medication-history")
async def get_medication_history(patient_id: str, days: int = 7):
    """获取服药记录"""
    records = list(_records.values())
    return {"records": records[:days]}
