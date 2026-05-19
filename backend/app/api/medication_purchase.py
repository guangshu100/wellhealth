"""
购药记录API
支持通过姓名+身份证号码查询购药记录
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class MedicationPurchase(BaseModel):
    """购药记录"""
    id: str
    patient_name: str
    id_card: str
    pharmacy: str
    pharmacy_address: Optional[str] = None
    drug_name: str
    drug_specification: str
    manufacturer: Optional[str] = None
    quantity: int
    unit_price: float
    total_amount: float
    purchase_date: str
    prescription_no: Optional[str] = None
    payment_method: Optional[str] = None
    invoice_no: Optional[str] = None
    pharmacist: Optional[str] = None
    created_at: str


class MedicationPurchaseQuery(BaseModel):
    """购药记录查询请求"""
    name: str
    id_card: str
    pharmacy: Optional[str] = None
    drug_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# 模拟数据存储
_purchases: dict = {}


@router.post("/query")
async def query_medication_purchases(query: MedicationPurchaseQuery):
    """
    通过姓名+身份证号码查询购药记录列表
    """
    results = []
    
    # 模拟数据 - 实际项目中应从数据库或第三方接口查询
    if not _purchases:
        _purchases["1"] = {
            "id": "MP001",
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "pharmacy": "国大药房(北京旗舰店)",
            "pharmacy_address": "北京市东城区和平里街道和平里东街18号",
            "drug_name": "二甲双胍片",
            "drug_specification": "0.5g*20片/盒",
            "manufacturer": "中美上海施贵宝制药有限公司",
            "quantity": 2,
            "unit_price": 28.50,
            "total_amount": 57.00,
            "purchase_date": "2024-03-16",
            "prescription_no": "P202403150001",
            "payment_method": "医保卡",
            "invoice_no": "INV20240316001",
            "pharmacist": "王药师",
            "created_at": "2024-03-16 10:30:00"
        }
        _purchases["2"] = {
            "id": "MP002",
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "pharmacy": "国大药房(北京旗舰店)",
            "pharmacy_address": "北京市东城区和平里街道和平里东街18号",
            "drug_name": "阿卡波糖片",
            "drug_specification": "50mg*30片/盒",
            "manufacturer": "拜耳医药保健有限公司",
            "quantity": 1,
            "unit_price": 65.80,
            "total_amount": 65.80,
            "purchase_date": "2024-03-16",
            "prescription_no": "P202403150001",
            "payment_method": "医保卡",
            "invoice_no": "INV20240316002",
            "pharmacist": "王药师",
            "created_at": "2024-03-16 10:35:00"
        }
        _purchases["3"] = {
            "id": "MP003",
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "pharmacy": "华润医药连锁(和平里店)",
            "pharmacy_address": "北京市东城区和平里西街1号",
            "drug_name": "厄贝沙坦片",
            "drug_specification": "150mg*7片/盒",
            "manufacturer": "赛诺菲(杭州)制药有限公司",
            "quantity": 4,
            "unit_price": 32.40,
            "total_amount": 129.60,
            "purchase_date": "2024-03-21",
            "prescription_no": "P202403200002",
            "payment_method": "医保卡",
            "invoice_no": "INV20240321001",
            "pharmacist": "李药师",
            "created_at": "2024-03-21 15:20:00"
        }
        _purchases["4"] = {
            "id": "MP004",
            "patient_name": "李四",
            "id_card": "110101197001011234",
            "pharmacy": "老百姓大药房(北京店)",
            "pharmacy_address": "北京市西城区西单北大街120号",
            "drug_name": "羟苯磺酸钙胶囊",
            "drug_specification": "0.5g*24粒/盒",
            "manufacturer": "上海朝晖药业有限公司",
            "quantity": 2,
            "unit_price": 42.00,
            "total_amount": 84.00,
            "purchase_date": "2024-02-12",
            "prescription_no": "P202402100003",
            "payment_method": "自费",
            "invoice_no": "INV20240212001",
            "pharmacist": "张药师",
            "created_at": "2024-02-12 11:10:00"
        }
    
    # 查询匹配的数据
    for p in _purchases.values():
        # 姓名+身份证必填
        if p["patient_name"] != query.name or p["id_card"] != query.id_card:
            continue
        
        # 可选条件过滤
        if query.pharmacy and query.pharmacy not in p["pharmacy"]:
            continue
        if query.drug_name and query.drug_name not in p["drug_name"]:
            continue
        if query.start_date and p["purchase_date"] < query.start_date:
            continue
        if query.end_date and p["purchase_date"] > query.end_date:
            continue
        
        results.append(p)
    
    return {
        "success": True,
        "count": len(results),
        "data": results
    }


@router.get("/detail/{purchase_id}")
async def get_medication_purchase_detail(purchase_id: str):
    """获取购药记录详情"""
    if purchase_id in _purchases:
        return {
            "success": True,
            "data": _purchases[purchase_id]
        }
    
    # 默认返回
    return {
        "success": True,
        "data": {
            "id": purchase_id,
            "patient_name": "张三",
            "id_card": "110101196001011234",
            "pharmacy": "国大药房(北京旗舰店)",
            "pharmacy_address": "北京市东城区和平里街道和平里东街18号",
            "drug_name": "二甲双胍片",
            "drug_specification": "0.5g*20片/盒",
            "manufacturer": "中美上海施贵宝制药有限公司",
            "quantity": 2,
            "unit_price": 28.50,
            "total_amount": 57.00,
            "purchase_date": "2024-03-16",
            "prescription_no": "P202403150001",
            "payment_method": "医保卡",
            "invoice_no": "INV20240316001",
            "pharmacist": "王药师",
            "created_at": "2024-03-16 10:30:00"
        }
    }


@router.get("/pharmacies")
async def get_pharmacies():
    """获取药店列表"""
    pharmacies = list(set(p["pharmacy"] for p in _purchases.values()))
    return {
        "pharmacies": [
            {"value": p, "label": p} for p in pharmacies
        ]
    }


@router.get("/statistics")
async def get_purchase_statistics(name: str = Query(...), id_card: str = Query(...)):
    """获取购药统计信息"""
    purchases = [p for p in _purchases.values() 
                 if p["patient_name"] == name and p["id_card"] == id_card]
    
    total_amount = sum(p["total_amount"] for p in purchases)
    total_times = len(purchases)
    pharmacies = list(set(p["pharmacy"] for p in purchases))
    
    # 药品统计
    drug_stats = {}
    for p in purchases:
        drug_name = p["drug_name"]
        if drug_name not in drug_stats:
            drug_stats[drug_name] = {"count": 0, "amount": 0}
        drug_stats[drug_name]["count"] += p["quantity"]
        drug_stats[drug_name]["amount"] += p["total_amount"]
    
    return {
        "success": True,
        "data": {
            "total_amount": total_amount,
            "total_times": total_times,
            "pharmacies": pharmacies,
            "drug_statistics": drug_stats
        }
    }
