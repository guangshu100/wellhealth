"""
处方数据API
支持通过姓名+身份证号码查询处方信息
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter()


class PrescriptionStatus(str, Enum):
    """处方状态"""
    VALID = "valid"           # 有效
    EXPIRED = "expired"       # 已过期
    USED = "used"            # 已使用
    CANCELLED = "cancelled"  # 已取消


class PrescriptionType(str, Enum):
    """处方类型"""
    WESTERN = "western"        # 西药
    CHINESE = "chinese"       # 中药
    MIXED = "mixed"           # 中西药结合


class MedicationItem(BaseModel):
    """药品项目"""
    name: str
    specification: str
    quantity: str
    dosage: str
    usage: str


class Prescription(BaseModel):
    """处方"""
    id: str
    patient_name: str
    id_card: str
    prescription_no: str
    hospital: str
    department: str
    doctor: str
    prescription_date: str
    valid_until: str
    prescription_type: str
    diagnosis: str
    medications: List[MedicationItem]
    status: str
    total_amount: Optional[float] = None
    created_at: str


class PrescriptionQuery(BaseModel):
    """处方查询请求"""
    name: str
    id_card: str
    prescription_no: Optional[str] = None
    hospital: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# 模拟数据存储
_prescriptions: dict = {}


@router.post("/query")
async def query_prescriptions(query: PrescriptionQuery):
    """
    通过姓名+身份证号码查询处方列表
    """
    results = []
    
    # 模拟数据 - 实际项目中应从数据库或第三方接口查询
    if not _prescriptions:
        _prescriptions["1"] = {
            "id": "RX001",
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "prescription_no": "P202403150001",
            "hospital": "北京协和医院",
            "department": "内分泌科",
            "doctor": "李主任",
            "prescription_date": "2024-03-15",
            "valid_until": "2024-04-15",
            "prescription_type": "western",
            "diagnosis": "2型糖尿病",
            "medications": [
                {
                    "name": "二甲双胍片",
                    "specification": "0.5g*20片",
                    "quantity": "2",
                    "dosage": "0.5g",
                    "usage": "口服，每日2次，餐后服用"
                },
                {
                    "name": "阿卡波糖片",
                    "specification": "50mg*30片",
                    "quantity": "1",
                    "dosage": "50mg",
                    "usage": "口服，每日3次，与第一口饭同服"
                }
            ],
            "status": "valid",
            "total_amount": 156.80,
            "created_at": "2024-03-15 10:30:00"
        }
        _prescriptions["2"] = {
            "id": "RX002",
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "prescription_no": "P202403200002",
            "hospital": "北京协和医院",
            "department": "心内科",
            "doctor": "王主任",
            "prescription_date": "2024-03-20",
            "valid_until": "2024-04-20",
            "prescription_type": "western",
            "diagnosis": "高血压2级",
            "medications": [
                {
                    "name": "厄贝沙坦片",
                    "specification": "150mg*7片",
                    "quantity": "4",
                    "dosage": "150mg",
                    "usage": "口服，每日1次"
                },
                {
                    "name": "苯磺酸氨氯地平片",
                    "specification": "5mg*7片",
                    "quantity": "4",
                    "dosage": "5mg",
                    "usage": "口服，每日1次"
                }
            ],
            "status": "valid",
            "total_amount": 289.60,
            "created_at": "2024-03-20 14:20:00"
        }
        _prescriptions["3"] = {
            "id": "RX003",
            "patient_name": "李四",
            "id_card": "110101197001011234",
            "prescription_no": "P202402100003",
            "hospital": "北京宣武医院",
            "department": "内分泌科",
            "doctor": "赵主任",
            "prescription_date": "2024-02-10",
            "valid_until": "2024-03-10",
            "prescription_type": "western",
            "diagnosis": "糖尿病视网膜病变",
            "medications": [
                {
                    "name": "羟苯磺酸钙胶囊",
                    "specification": "0.5g*24粒",
                    "quantity": "2",
                    "dosage": "0.5g",
                    "usage": "口服，每日3次"
                }
            ],
            "status": "expired",
            "total_amount": 168.00,
            "created_at": "2024-02-10 09:15:00"
        }
    
    # 查询匹配的数据
    for p in _prescriptions.values():
        # 姓名+身份证必填
        if p["patient_name"] != query.name or p["id_card"] != query.id_card:
            continue
        
        # 可选条件过滤
        if query.prescription_no and p["prescription_no"] != query.prescription_no:
            continue
        if query.hospital and query.hospital not in p["hospital"]:
            continue
        if query.start_date and p["prescription_date"] < query.start_date:
            continue
        if query.end_date and p["prescription_date"] > query.end_date:
            continue
        
        results.append(p)
    
    return {
        "success": True,
        "count": len(results),
        "data": results
    }


@router.get("/detail/{prescription_id}")
async def get_prescription_detail(prescription_id: str):
    """获取处方详情"""
    if prescription_id in _prescriptions:
        return {
            "success": True,
            "data": _prescriptions[prescription_id]
        }
    
    # 模拟数据
    return {
        "success": True,
        "data": {
            "id": prescription_id,
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "prescription_no": "P202403150001",
            "hospital": "北京协和医院",
            "department": "内分泌科",
            "doctor": "李主任",
            "prescription_date": "2024-03-15",
            "valid_until": "2024-04-15",
            "prescription_type": "western",
            "diagnosis": "2型糖尿病",
            "medications": [
                {
                    "name": "二甲双胍片",
                    "specification": "0.5g*20片",
                    "quantity": "2",
                    "dosage": "0.5g",
                    "usage": "口服，每日2次，餐后服用"
                }
            ],
            "status": "valid",
            "total_amount": 156.80,
            "created_at": "2024-03-15 10:30:00"
        }
    }


@router.get("/types")
async def get_prescription_types():
    """获取处方类型列表"""
    return {
        "types": [
            {"value": "western", "label": "西药"},
            {"value": "chinese", "label": "中药"},
            {"value": "mixed", "label": "中西药结合"}
        ]
    }


@router.get("/status-list")
async def get_prescription_status_list():
    """获取处方状态列表"""
    return {
        "status": [
            {"value": "valid", "label": "有效"},
            {"value": "expired", "label": "已过期"},
            {"value": "used", "label": "已使用"},
            {"value": "cancelled", "label": "已取消"}
        ]
    }
