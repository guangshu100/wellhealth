"""
患者管理API
完整的患者CRUD、健康档案、体征管理
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 模型定义 ============

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DiseaseRecord(BaseModel):
    """疾病记录"""
    id: str
    patient_id: str
    disease_name: str
    disease_type: str
    icd_code: Optional[str] = None
    diagnosed_date: Optional[str] = None
    status: str
    severity: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MedicationRecord(BaseModel):
    """用药记录"""
    id: str
    patient_id: str
    drug_name: str
    specification: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    hospital: Optional[str] = None
    prescription_no: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VitalRecord(BaseModel):
    """体征记录"""
    id: str
    patient_id: str
    vital_type: str
    value: float
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: Optional[str] = None
    recorded_at: str
    source: Optional[str] = None
    device_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class HealthProfile(BaseModel):
    """健康档案"""
    patient_id: str
    diseases: List[DiseaseRecord]
    medications: List[MedicationRecord]
    vitals: List[VitalRecord]
    family_history: List[str]
    lifestyle: dict


# ============ 数据库辅助函数 ============
def get_patients_from_db(search: str = None, skip: int = 0, limit: int = 20) -> List[dict]:
    """从数据库获取患者列表"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            if search:
                result = db.execute(text("""
                    SELECT id, user_id, name, age, gender, phone, id_card, address,
                           emergency_contact, emergency_phone, blood_type, height, weight,
                           allergies, family_history, lifestyle, status,
                           created_at, updated_at
                    FROM patients 
                    WHERE name LIKE :search OR phone LIKE :search OR id_card LIKE :search
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :skip
                """), {"search": f"%{search}%", "limit": limit, "skip": skip})
            else:
                result = db.execute(text("""
                    SELECT id, user_id, name, age, gender, phone, id_card, address,
                           emergency_contact, emergency_phone, blood_type, height, weight,
                           allergies, family_history, lifestyle, status,
                           created_at, updated_at
                    FROM patients 
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :skip
                """), {"limit": limit, "skip": skip})
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get patients from database: {e}")
        return []


def get_patient_by_id_from_db(patient_id: str) -> dict:
    """从数据库获取单个患者"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, user_id, name, age, gender, phone, id_card, address,
                       emergency_contact, emergency_phone, blood_type, height, weight,
                       allergies, family_history, lifestyle, status,
                       created_at, updated_at
                FROM patients 
                WHERE id = :id
            """), {"id": patient_id})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get patient from database: {e}")
        return None


def count_patients_from_db(search: str = None) -> int:
    """统计患者数量"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            if search:
                result = db.execute(text("""
                    SELECT COUNT(*) as count FROM patients 
                    WHERE name LIKE :search OR phone LIKE :search OR id_card LIKE :search
                """), {"search": f"%{search}%"})
            else:
                result = db.execute(text("SELECT COUNT(*) as count FROM patients"))
            row = result.fetchone()
            return row[0] if row else 0
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to count patients: {e}")
        return 0


def create_patient_to_db(patient_data: dict) -> dict:
    """创建患者到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            patient_id = f"p{uuid.uuid4().hex[:8]}"
            now = datetime.now()
            
            db.execute(text("""
                INSERT INTO patients (id, name, age, gender, phone, id_card, address,
                                    emergency_contact, emergency_phone, created_at, updated_at)
                VALUES (:id, :name, :age, :gender, :phone, :id_card, :address,
                        :emergency_contact, :emergency_phone, :created_at, :updated_at)
            """), {
                "id": patient_id,
                "name": patient_data.get("name"),
                "age": patient_data.get("age"),
                "gender": patient_data.get("gender"),
                "phone": patient_data.get("phone"),
                "id_card": patient_data.get("id_card"),
                "address": patient_data.get("address"),
                "emergency_contact": patient_data.get("emergency_contact"),
                "emergency_phone": patient_data.get("emergency_phone"),
                "created_at": now,
                "updated_at": now
            })
            db.commit()
            return {**patient_data, "id": patient_id, "created_at": now, "updated_at": now}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to create patient: {e}")
        return None


def update_patient_to_db(patient_id: str, patient_data: dict) -> dict:
    """更新患者到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            now = datetime.now()
            db.execute(text("""
                UPDATE patients 
                SET name = :name, age = :age, gender = :gender, phone = :phone,
                    id_card = :id_card, address = :address,
                    emergency_contact = :emergency_contact, emergency_phone = :emergency_phone,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                "id": patient_id,
                "name": patient_data.get("name"),
                "age": patient_data.get("age"),
                "gender": patient_data.get("gender"),
                "phone": patient_data.get("phone"),
                "id_card": patient_data.get("id_card"),
                "address": patient_data.get("address"),
                "emergency_contact": patient_data.get("emergency_contact"),
                "emergency_phone": patient_data.get("emergency_phone"),
                "updated_at": now
            })
            db.commit()
            return get_patient_by_id_from_db(patient_id)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to update patient: {e}")
        return None


def delete_patient_from_db(patient_id: str) -> bool:
    """从数据库删除患者"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM patients WHERE id = :id"), {"id": patient_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to delete patient: {e}")
        return False


# ============ 疾病记录数据库函数 ============

def get_diseases_from_db(patient_id: str) -> List[dict]:
    """从数据库获取患者的疾病记录"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, patient_id, disease_name, disease_type, icd_code,
                       diagnosed_date, status, severity, notes, created_at, updated_at
                FROM disease_records 
                WHERE patient_id = :patient_id
                ORDER BY diagnosed_date DESC
            """), {"patient_id": patient_id})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get diseases from database: {e}")
        return []


def create_disease_to_db(disease_data: dict) -> dict:
    """创建疾病记录到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            disease_id = f"d{uuid.uuid4().hex[:8]}"
            now = datetime.now()
            
            db.execute(text("""
                INSERT INTO disease_records (id, patient_id, disease_name, disease_type,
                    icd_code, diagnosed_date, status, severity, notes, created_at, updated_at)
                VALUES (:id, :patient_id, :disease_name, :disease_type,
                    :icd_code, :diagnosed_date, :status, :severity, :notes, :created_at, :updated_at)
            """), {
                "id": disease_id,
                "patient_id": disease_data.get("patient_id"),
                "disease_name": disease_data.get("disease_name"),
                "disease_type": disease_data.get("disease_type", "chronic"),
                "icd_code": disease_data.get("icd_code"),
                "diagnosed_date": disease_data.get("diagnosed_date"),
                "status": disease_data.get("status", "active"),
                "severity": disease_data.get("severity", "moderate"),
                "notes": disease_data.get("notes"),
                "created_at": now,
                "updated_at": now
            })
            db.commit()
            return {**disease_data, "id": disease_id, "created_at": now, "updated_at": now}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to create disease: {e}")
        return None


def update_disease_to_db(disease_id: str, disease_data: dict) -> dict:
    """更新疾病记录到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            now = datetime.now()
            db.execute(text("""
                UPDATE disease_records 
                SET disease_name = :disease_name, disease_type = :disease_type,
                    icd_code = :icd_code, diagnosed_date = :diagnosed_date,
                    status = :status, severity = :severity, notes = :notes,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                "id": disease_id,
                "disease_name": disease_data.get("disease_name"),
                "disease_type": disease_data.get("disease_type"),
                "icd_code": disease_data.get("icd_code"),
                "diagnosed_date": disease_data.get("diagnosed_date"),
                "status": disease_data.get("status"),
                "severity": disease_data.get("severity"),
                "notes": disease_data.get("notes"),
                "updated_at": now
            })
            db.commit()
            result = db.execute(text("SELECT * FROM disease_records WHERE id = :id"), {"id": disease_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to update disease: {e}")
        return None


def delete_disease_from_db(disease_id: str) -> bool:
    """从数据库删除疾病记录"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM disease_records WHERE id = :id"), {"id": disease_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to delete disease: {e}")
        return False


# ============ 用药记录数据库函数 ============

def get_medications_from_db(patient_id: str) -> List[dict]:
    """从数据库获取患者的用药记录"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, patient_id, drug_name, specification, dosage, frequency,
                       route, start_date, end_date, prescribing_doctor, hospital,
                       prescription_no, status, notes, created_at, updated_at
                FROM medication_records 
                WHERE patient_id = :patient_id
                ORDER BY start_date DESC
            """), {"patient_id": patient_id})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get medications from database: {e}")
        return []


def create_medication_to_db(medication_data: dict) -> dict:
    """创建用药记录到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            medication_id = f"m{uuid.uuid4().hex[:8]}"
            now = datetime.now()
            
            db.execute(text("""
                INSERT INTO medication_records (id, patient_id, drug_name, specification,
                    dosage, frequency, route, start_date, end_date, prescribing_doctor,
                    hospital, prescription_no, status, notes, created_at, updated_at)
                VALUES (:id, :patient_id, :drug_name, :specification,
                    :dosage, :frequency, :route, :start_date, :end_date, :prescribing_doctor,
                    :hospital, :prescription_no, :status, :notes, :created_at, :updated_at)
            """), {
                "id": medication_id,
                "patient_id": medication_data.get("patient_id"),
                "drug_name": medication_data.get("drug_name"),
                "specification": medication_data.get("specification"),
                "dosage": medication_data.get("dosage"),
                "frequency": medication_data.get("frequency"),
                "route": medication_data.get("route"),
                "start_date": medication_data.get("start_date"),
                "end_date": medication_data.get("end_date"),
                "prescribing_doctor": medication_data.get("prescribing_doctor"),
                "hospital": medication_data.get("hospital"),
                "prescription_no": medication_data.get("prescription_no"),
                "status": medication_data.get("status", "active"),
                "notes": medication_data.get("notes"),
                "created_at": now,
                "updated_at": now
            })
            db.commit()
            return {**medication_data, "id": medication_id, "created_at": now, "updated_at": now}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to create medication: {e}")
        return None


def delete_medication_from_db(medication_id: str) -> bool:
    """从数据库删除用药记录"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM medication_records WHERE id = :id"), {"id": medication_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to delete medication: {e}")
        return False


# ============ 体征记录数据库函数 ============

def get_vitals_from_db(patient_id: str, vital_type: str = None, days: int = 30) -> List[dict]:
    """从数据库获取患者的体征记录"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        from datetime import timedelta
        db = SessionLocal()
        try:
            start_date = datetime.now() - timedelta(days=days)
            if vital_type:
                result = db.execute(text("""
                    SELECT id, patient_id, vital_type, value, unit, reference_min, reference_max,
                           status, recorded_at, source, device_id, notes, created_at
                    FROM vital_records 
                    WHERE patient_id = :patient_id AND vital_type = :vital_type AND recorded_at >= :start_date
                    ORDER BY recorded_at DESC
                """), {"patient_id": patient_id, "vital_type": vital_type, "start_date": start_date})
            else:
                result = db.execute(text("""
                    SELECT id, patient_id, vital_type, value, unit, reference_min, reference_max,
                           status, recorded_at, source, device_id, notes, created_at
                    FROM vital_records 
                    WHERE patient_id = :patient_id AND recorded_at >= :start_date
                    ORDER BY recorded_at DESC
                """), {"patient_id": patient_id, "start_date": start_date})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get vitals from database: {e}")
        return []


def create_vital_to_db(vital_data: dict) -> dict:
    """创建体征记录到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            vital_id = f"v{uuid.uuid4().hex[:8]}"
            now = datetime.now()
            
            db.execute(text("""
                INSERT INTO vital_records (id, patient_id, vital_type, value, unit,
                    reference_min, reference_max, status, recorded_at, source, device_id, notes, created_at)
                VALUES (:id, :patient_id, :vital_type, :value, :unit,
                    :reference_min, :reference_max, :status, :recorded_at, :source, :device_id, :notes, :created_at)
            """), {
                "id": vital_id,
                "patient_id": vital_data.get("patient_id"),
                "vital_type": vital_data.get("vital_type"),
                "value": vital_data.get("value"),
                "unit": vital_data.get("unit"),
                "reference_min": vital_data.get("reference_min"),
                "reference_max": vital_data.get("reference_max"),
                "status": vital_data.get("status", "normal"),
                "recorded_at": vital_data.get("recorded_at", now),
                "source": vital_data.get("source", "manual"),
                "device_id": vital_data.get("device_id"),
                "notes": vital_data.get("notes"),
                "created_at": now
            })
            db.commit()
            return {**vital_data, "id": vital_id, "created_at": now}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to create vital: {e}")
        return None


# 内存存储（作为Fallback）
_patients: dict = {}
_diseases: dict = {}
_medications: dict = {}
_vitals: dict = {}


def _init_sample_data():
    """初始化示例数据（仅当数据库不可用时使用）"""
    if _patients:
        return
    
    # 示例患者
    _patients["p1"] = {
        "id": "p1",
        "name": "张三",
        "age": 65,
        "gender": "male",
        "phone": "13800138001",
        "id_card": "110101196001011234",
        "address": "北京市东城区",
        "emergency_contact": "张妻",
        "emergency_phone": "13800138002",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-03-15T10:00:00"
    }
    _patients["p2"] = {
        "id": "p2",
        "name": "李四",
        "age": 58,
        "gender": "female",
        "phone": "13800138003",
        "id_card": "110101196601011234",
        "address": "北京市西城区",
        "emergency_contact": "李夫",
        "emergency_phone": "13800138004",
        "created_at": "2024-01-20T10:00:00",
        "updated_at": "2024-03-10T10:00:00"
    }
    
    # 疾病记录
    _diseases["d1"] = {
        "id": "d1",
        "patient_id": "p1",
        "disease_name": "2型糖尿病",
        "disease_type": "chronic",
        "diagnosed_date": "2020-03-15",
        "status": "active",
        "notes": "血糖控制良好"
    }
    _diseases["d2"] = {
        "id": "d2",
        "patient_id": "p1",
        "disease_name": "高血压2级",
        "disease_type": "chronic",
        "diagnosed_date": "2019-08-20",
        "status": "active",
        "notes": "间断服药"
    }
    _diseases["d3"] = {
        "id": "d3",
        "patient_id": "p2",
        "disease_name": "2型糖尿病",
        "disease_type": "chronic",
        "diagnosed_date": "2021-05-10",
        "status": "active",
        "notes": "新确诊"
    }
    
    # 用药记录
    _medications["m1"] = {
        "id": "m1",
        "patient_id": "p1",
        "drug_name": "二甲双胍片",
        "specification": "0.5g*20片",
        "dosage": "0.5g",
        "frequency": "每日2次",
        "start_date": "2020-03-15",
        "end_date": None,
        "prescribing_doctor": "李主任",
        "hospital": "北京协和医院"
    }
    _medications["m2"] = {
        "id": "m2",
        "patient_id": "p1",
        "drug_name": "厄贝沙坦片",
        "specification": "150mg*7片",
        "dosage": "150mg",
        "frequency": "每日1次",
        "start_date": "2019-08-20",
        "end_date": None,
        "prescribing_doctor": "王主任",
        "hospital": "北京宣武医院"
    }
    _medications["m3"] = {
        "id": "m3",
        "patient_id": "p2",
        "drug_name": "阿卡波糖片",
        "specification": "50mg*30片",
        "dosage": "50mg",
        "frequency": "每日3次",
        "start_date": "2021-05-10",
        "end_date": None,
        "prescribing_doctor": "赵主任",
        "hospital": "北京同仁医院"
    }
    
    # 体征记录
    _vitals["v1"] = {
        "id": "v1",
        "patient_id": "p1",
        "vital_type": "blood_sugar",
        "value": 6.5,
        "unit": "mmol/L",
        "recorded_at": "2024-03-15T08:00:00",
        "notes": "空腹血糖"
    }
    _vitals["v2"] = {
        "id": "v2",
        "patient_id": "p1",
        "vital_type": "blood_pressure_systolic",
        "value": 135,
        "unit": "mmHg",
        "recorded_at": "2024-03-15T08:30:00",
        "notes": "收缩压"
    }
    _vitals["v3"] = {
        "id": "v3",
        "patient_id": "p1",
        "vital_type": "blood_pressure_diastolic",
        "value": 85,
        "unit": "mmHg",
        "recorded_at": "2024-03-15T08:30:00",
        "notes": "舒张压"
    }
    _vitals["v4"] = {
        "id": "v4",
        "patient_id": "p2",
        "vital_type": "blood_sugar",
        "value": 7.2,
        "unit": "mmol/L",
        "recorded_at": "2024-03-14T08:00:00",
        "notes": "空腹血糖"
    }


_init_sample_data()


# ============ 患者CRUD ============

@router.post("/", response_model=PatientResponse)
async def create_patient(patient: PatientCreate):
    """创建患者"""
    # 尝试写入数据库
    patient_data = {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "id_card": patient.id_card,
        "address": patient.address,
        "emergency_contact": patient.emergency_contact,
        "emergency_phone": patient.emergency_phone
    }
    
    db_patient = create_patient_to_db(patient_data)
    if db_patient:
        return db_patient
    
    # Fallback到内存存储
    patient_id = f"p{len(_patients) + 1}"
    now = datetime.now().isoformat()
    new_patient = {
        "id": patient_id,
        **patient_data,
        "created_at": now,
        "updated_at": now
    }
    _patients[patient_id] = new_patient
    return new_patient


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0, 
    limit: int = 20, 
    search: Optional[str] = None,
    disease: Optional[str] = None
):
    """获取患者列表"""
    # 优先从数据库获取
    db_patients = get_patients_from_db(search, skip, limit)
    if db_patients:
        return db_patients
    
    # Fallback到内存存储
    patients = list(_patients.values())
    
    # 搜索过滤
    if search:
        patients = [p for p in patients if search.lower() in p["name"].lower()]
    
    # 按疾病过滤
    if disease:
        patient_ids = [d["patient_id"] for d in _diseases.values() 
                      if disease in d["disease_name"]]
        patients = [p for p in patients if p["id"] in patient_ids]
    
    return patients[skip:skip + limit]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """获取患者详情"""
    # 优先从数据库获取
    db_patient = get_patient_by_id_from_db(patient_id)
    if db_patient:
        return db_patient
    
    # Fallback到内存存储
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    return _patients[patient_id]


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, patient: PatientUpdate):
    """更新患者信息"""
    # 尝试更新数据库
    patient_data = {k: v for k, v in patient.dict().items() if v is not None}
    db_patient = update_patient_to_db(patient_id, patient_data)
    if db_patient:
        return db_patient
    
    # Fallback到内存存储
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    existing = _patients[patient_id]
    update_data = patient.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        existing[key] = value
    
    existing["updated_at"] = datetime.now().isoformat()
    _patients[patient_id] = existing
    
    return existing


@router.delete("/{patient_id}")
async def delete_patient(patient_id: str):
    """删除患者"""
    global _diseases, _medications, _vitals
    
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    del _patients[patient_id]
    
    # 删除相关记录
    _diseases = {k: v for k, v in _diseases.items() if v["patient_id"] != patient_id}
    _medications = {k: v for k, v in _medications.items() if v["patient_id"] != patient_id}
    _vitals = {k: v for k, v in _vitals.items() if v["patient_id"] != patient_id}
    
    return {"success": True, "message": "患者已删除"}


# ============ 健康档案 ============

@router.get("/{patient_id}/profile")
async def get_patient_profile(patient_id: str):
    """获取患者健康档案"""
    # 优先从数据库获取患者信息
    patient = get_patient_by_id_from_db(patient_id)
    if not patient:
        # Fallback到内存存储
        if patient_id not in _patients:
            raise HTTPException(status_code=404, detail="患者不存在")
        patient = _patients[patient_id]
    
    # 优先从数据库获取相关记录
    diseases = get_diseases_from_db(patient_id)
    medications = get_medications_from_db(patient_id)
    vitals = get_vitals_from_db(patient_id)
    
    # 如果数据库为空，使用内存存储
    if not diseases:
        diseases = [d for d in _diseases.values() if d["patient_id"] == patient_id]
    if not medications:
        medications = [m for m in _medications.values() if m["patient_id"] == patient_id]
    if not vitals:
        vitals = [v for v in _vitals.values() if v["patient_id"] == patient_id]
    
    return {
        "patient_id": patient_id,
        "basic_info": patient,
        "diseases": diseases,
        "medications": medications,
        "vitals": vitals,
        "allergies": patient.get("allergies", ["无"]),
        "family_history": patient.get("family_history", ["无"]),
        "lifestyle": patient.get("lifestyle", {"smoking": "无", "drinking": "偶尔", "exercise": "每周3次"})
    }


# ============ 疾病管理 ============

@router.get("/{patient_id}/diseases")
async def get_patient_diseases(patient_id: str):
    """获取患者疾病列表"""
    # 优先从数据库获取
    diseases = get_diseases_from_db(patient_id)
    if diseases:
        return diseases
    
    # Fallback到内存存储
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    diseases = [d for d in _diseases.values() if d["patient_id"] == patient_id]
    return diseases


@router.post("/{patient_id}/diseases")
async def add_disease(patient_id: str, disease: dict):
    """添加疾病记录"""
    # 验证患者存在
    patient = get_patient_by_id_from_db(patient_id)
    if not patient:
        if patient_id not in _patients:
            raise HTTPException(status_code=404, detail="患者不存在")
    
    # 尝试写入数据库
    disease_data = {
        "patient_id": patient_id,
        "disease_name": disease.get("disease_name", ""),
        "disease_type": disease.get("disease_type", "chronic"),
        "icd_code": disease.get("icd_code"),
        "diagnosed_date": disease.get("diagnosed_date"),
        "status": disease.get("status", "active"),
        "severity": disease.get("severity", "moderate"),
        "notes": disease.get("notes")
    }
    db_disease = create_disease_to_db(disease_data)
    if db_disease:
        return db_disease
    
    # Fallback到内存存储
    disease_id = f"d{len(_diseases) + 1}"
    new_disease = {
        "id": disease_id,
        **disease_data
    }
    _diseases[disease_id] = new_disease
    return new_disease


@router.put("/{patient_id}/diseases/{disease_id}")
async def update_disease(patient_id: str, disease_id: str, disease: dict):
    """更新疾病记录"""
    # 尝试更新数据库
    db_disease = update_disease_to_db(disease_id, disease)
    if db_disease:
        return db_disease
    
    # Fallback到内存存储
    if disease_id not in _diseases:
        raise HTTPException(status_code=404, detail="疾病记录不存在")
    
    existing = _diseases[disease_id]
    for key, value in disease.items():
        if value is not None:
            existing[key] = value
    
    _diseases[disease_id] = existing
    return existing


@router.delete("/{patient_id}/diseases/{disease_id}")
async def delete_disease(patient_id: str, disease_id: str):
    """删除疾病记录"""
    # 尝试从数据库删除
    if delete_disease_from_db(disease_id):
        return {"success": True}
    
    # Fallback到内存存储
    if disease_id in _diseases:
        del _diseases[disease_id]
    return {"success": True}


# ============ 用药管理 ============

@router.get("/{patient_id}/medications")
async def get_patient_medications(patient_id: str):
    """获取患者用药列表"""
    # 优先从数据库获取
    medications = get_medications_from_db(patient_id)
    if medications:
        return medications
    
    # Fallback到内存存储
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    medications = [m for m in _medications.values() if m["patient_id"] == patient_id]
    return medications


@router.post("/{patient_id}/medications")
async def add_medication(patient_id: str, medication: dict):
    """添加用药记录"""
    # 验证患者存在
    patient = get_patient_by_id_from_db(patient_id)
    if not patient:
        if patient_id not in _patients:
            raise HTTPException(status_code=404, detail="患者不存在")
    
    # 尝试写入数据库
    medication_data = {
        "patient_id": patient_id,
        "drug_name": medication.get("drug_name", ""),
        "specification": medication.get("specification"),
        "dosage": medication.get("dosage"),
        "frequency": medication.get("frequency"),
        "route": medication.get("route"),
        "start_date": medication.get("start_date", ""),
        "end_date": medication.get("end_date"),
        "prescribing_doctor": medication.get("prescribing_doctor"),
        "hospital": medication.get("hospital"),
        "prescription_no": medication.get("prescription_no"),
        "status": medication.get("status", "active"),
        "notes": medication.get("notes")
    }
    db_medication = create_medication_to_db(medication_data)
    if db_medication:
        return db_medication
    
    # Fallback到内存存储
    medication_id = f"m{len(_medications) + 1}"
    new_medication = {
        "id": medication_id,
        **medication_data
    }
    _medications[medication_id] = new_medication
    return new_medication


@router.delete("/{patient_id}/medications/{medication_id}")
async def delete_medication(patient_id: str, medication_id: str):
    """删除用药记录"""
    # 尝试从数据库删除
    if delete_medication_from_db(medication_id):
        return {"success": True}
    
    # Fallback到内存存储
    if medication_id in _medications:
        del _medications[medication_id]
    return {"success": True}


# ============ 体征管理 ============

@router.get("/{patient_id}/vitals")
async def get_patient_vitals(
    patient_id: str, 
    vital_type: Optional[str] = None,
    days: int = 30
):
    """获取患者体征记录"""
    # 优先从数据库获取
    vitals = get_vitals_from_db(patient_id, vital_type, days)
    if vitals:
        return {"records": vitals}
    
    # Fallback到内存存储
    if patient_id not in _patients:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    vitals = [v for v in _vitals.values() if v["patient_id"] == patient_id]
    
    if vital_type:
        vitals = [v for v in vitals if v["vital_type"] == vital_type]
    
    return {"records": vitals}


@router.post("/{patient_id}/vitals")
async def add_vital_record(patient_id: str, vital: dict):
    """添加体征记录"""
    # 验证患者存在
    patient = get_patient_by_id_from_db(patient_id)
    if not patient:
        if patient_id not in _patients:
            raise HTTPException(status_code=404, detail="患者不存在")
    
    # 尝试写入数据库
    vital_data = {
        "patient_id": patient_id,
        "vital_type": vital.get("vital_type", ""),
        "value": vital.get("value", 0),
        "unit": vital.get("unit"),
        "reference_min": vital.get("reference_min"),
        "reference_max": vital.get("reference_max"),
        "status": vital.get("status", "normal"),
        "recorded_at": vital.get("recorded_at", datetime.now().isoformat()),
        "source": vital.get("source", "manual"),
        "device_id": vital.get("device_id"),
        "notes": vital.get("notes")
    }
    db_vital = create_vital_to_db(vital_data)
    if db_vital:
        return db_vital
    
    # Fallback到内存存储
    vital_id = f"v{len(_vitals) + 1}"
    new_vital = {
        "id": vital_id,
        **vital_data
    }
    _vitals[vital_id] = new_vital
    return new_vital


@router.get("/{patient_id}/vitals/trend")
async def get_vitals_trend(
    patient_id: str,
    vital_type: str = Query(..., description="体征类型: blood_sugar, blood_pressure_systolic, blood_pressure_diastolic"),
    days: int = 30
):
    """获取体征趋势数据"""
    # 优先从数据库获取
    vitals = get_vitals_from_db(patient_id, vital_type, days)
    
    # Fallback到内存存储
    if not vitals:
        if patient_id not in _patients:
            raise HTTPException(status_code=404, detail="患者不存在")
        vitals = [v for v in _vitals.values() 
                  if v["patient_id"] == patient_id and v["vital_type"] == vital_type]
    
    # 按时间排序
    vitals.sort(key=lambda x: x["recorded_at"])
    
    # 计算统计
    if vitals:
        values = [v["value"] for v in vitals]
        stats = {
            "avg": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
            "latest": values[-1],
            "count": len(values)
        }
    else:
        stats = {"avg": 0, "max": 0, "min": 0, "latest": 0, "count": 0}
    
    return {
        "vital_type": vital_type,
        "records": vitals,
        "statistics": stats
    }


# ============ 我的患者 (当前登录患者) ============

@router.get("/my/detail")
async def get_my_patient():
    """获取当前绑定的患者信息 (模拟)"""
    # 返回第一个患者作为示例
    if _patients:
        first_patient = list(_patients.values())[0]
        return await get_patient_profile(first_patient["id"])
    return {"message": "未绑定患者"}
