"""
医生管理API
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 数据库辅助函数 ============

def get_doctors_from_db(department: str = None, search: str = None) -> List[dict]:
    """从数据库获取医生列表"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            if department:
                result = db.execute(text("""
                    SELECT id, user_id, name, department, title, hospital, specialty, 
                           avatar_url, bio, status, created_at, updated_at
                    FROM doctors 
                    WHERE department = :dept AND status = 'active'
                """), {"dept": department})
            elif search:
                result = db.execute(text("""
                    SELECT id, user_id, name, department, title, hospital, specialty, 
                           avatar_url, bio, status, created_at, updated_at
                    FROM doctors 
                    WHERE (name LIKE :search OR hospital LIKE :search) AND status = 'active'
                """), {"search": f"%{search}%"})
            else:
                result = db.execute(text("""
                    SELECT id, user_id, name, department, title, hospital, specialty, 
                           avatar_url, bio, status, created_at, updated_at
                    FROM doctors 
                    WHERE status = 'active'
                """))
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get doctors from database: {e}")
        return []


def get_doctor_by_id_from_db(doctor_id: str) -> dict:
    """从数据库获取单个医生"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, user_id, name, department, title, hospital, specialty, 
                       avatar_url, bio, status, created_at, updated_at
                FROM doctors 
                WHERE id = :id
            """), {"id": doctor_id})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get doctor from database: {e}")
        return None


# ============ Pydantic 模型 ============

class DoctorResponse(BaseModel):
    id: str
    name: str
    department: str
    title: str
    hospital: str
    specialty: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    status: str


# 内存存储（作为Fallback）
_doctors = {}


def _init_doctors():
    """初始化医生数据"""
    if _doctors:
        return
    
    _doctors["d001"] = {
        "id": "d001",
        "name": "李主任",
        "department": "内分泌科",
        "title": "主任医师",
        "hospital": "北京协和医院",
        "specialty": "糖尿病、甲状腺疾病",
        "avatar_url": None,
        "bio": "从事内分泌科临床工作30余年，擅长糖尿病及其并发症的诊治。",
        "status": "active"
    }
    _doctors["d002"] = {
        "id": "d002",
        "name": "王主任",
        "department": "心内科",
        "title": "主任医师",
        "hospital": "北京宣武医院",
        "specialty": "高血压、冠心病",
        "avatar_url": None,
        "bio": "擅长高血压、冠心病、心律失常等心血管疾病的诊治。",
        "status": "active"
    }
    _doctors["d003"] = {
        "id": "d003",
        "name": "赵主任",
        "department": "内分泌科",
        "title": "副主任医师",
        "hospital": "北京同仁医院",
        "specialty": "糖尿病、骨质疏松",
        "avatar_url": None,
        "bio": "专注于糖尿病及其慢性并发症的防治。",
        "status": "active"
    }


_init_doctors()


@router.get("/")
async def list_doctors(
    department: Optional[str] = None,
    hospital: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取医生列表"""
    # 优先从数据库获取
    db_doctors = get_doctors_from_db(department, search)
    if db_doctors:
        doctors = db_doctors
        if hospital:
            doctors = [d for d in doctors if hospital in d.get("hospital", "")]
        return {
            "items": doctors[skip:skip + limit],
            "total": len(doctors)
        }
    
    # Fallback到内存存储
    doctors = list(_doctors.values())
    
    if department:
        doctors = [d for d in doctors if d["department"] == department]
    if hospital:
        doctors = [d for d in doctors if hospital in d["hospital"]]
    if search:
        doctors = [d for d in doctors if search.lower() in d["name"].lower() or search in d["specialty"]]
    
    return {
        "items": doctors[skip:skip + limit],
        "total": len(doctors)
    }


@router.get("/{doctor_id}")
async def get_doctor(doctor_id: str):
    """获取医生详情"""
    # 优先从数据库获取
    db_doctor = get_doctor_by_id_from_db(doctor_id)
    if db_doctor:
        return db_doctor
    
    # Fallback到内存存储
    if doctor_id not in _doctors:
        raise HTTPException(status_code=404, detail="医生不存在")
    return _doctors[doctor_id]


@router.get("/{doctor_id}/patients")
async def get_doctor_patients(doctor_id: str):
    """获取医生管理的患者列表"""
    if doctor_id not in _doctors:
        raise HTTPException(status_code=404, detail="医生不存在")
    
    # 模拟数据
    patients = [
        {"id": "p001", "name": "张三", "disease": "2型糖尿病", "last_visit": "2024-03-15"},
        {"id": "p002", "name": "李四", "disease": "2型糖尿病", "last_visit": "2024-03-10"}
    ]
    
    return {
        "items": patients,
        "total": len(patients)
    }


@router.get("/departments/list")
async def list_departments():
    """获取科室列表"""
    departments = [
        {"value": "内分泌科", "label": "内分泌科"},
        {"value": "心内科", "label": "心内科"},
        {"value": "神经内科", "label": "神经内科"},
        {"value": "消化内科", "label": "消化内科"},
        {"value": "呼吸内科", "label": "呼吸内科"},
        {"value": "肾内科", "label": "肾内科"},
    ]
    return {"departments": departments}
