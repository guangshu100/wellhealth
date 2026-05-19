"""
体检报告API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random

router = APIRouter()


class ReportItem(BaseModel):
    """体检项目"""
    name: str
    value: float
    unit: str
    reference_min: float
    reference_max: float
    status: str


class Report(BaseModel):
    """体检报告"""
    id: str
    patient_id: str
    title: str
    report_type: str
    hospital: Optional[str] = None
    exam_date: str
    status: str
    items: List[ReportItem] = []


class ReportAnalysis(BaseModel):
    """AI分析结果"""
    analysis: str
    recommendations: List[str]
    risk_alerts: List[str]


# 模拟数据存储
_reports: dict = {}


@router.get("/{patient_id}/reports")
async def get_reports(patient_id: str):
    """获取体检报告列表"""
    reports = [r for r in _reports.values() if r.patient_id == patient_id]
    if not reports:
        # 返回模拟数据
        reports = [
            {
                "id": "1",
                "patient_id": patient_id,
                "title": "年度体检报告",
                "report_type": "annual",
                "hospital": "市第一医院",
                "exam_date": "2024-03-15",
                "status": "analyzed",
                "items": []
            },
            {
                "id": "2", 
                "patient_id": patient_id,
                "title": "糖尿病专项检查",
                "report_type": "special",
                "hospital": "市第一医院",
                "exam_date": "2024-01-20",
                "status": "analyzed",
                "items": []
            }
        ]
    return reports


@router.get("/{patient_id}/reports/{report_id}")
async def get_report_detail(patient_id: str, report_id: str):
    """获取体检报告详情"""
    if report_id in _reports:
        return _reports[report_id]
    
    # 模拟数据
    return {
        "id": report_id,
        "patient_id": patient_id,
        "title": "年度体检报告",
        "report_type": "annual",
        "hospital": "市第一医院",
        "exam_date": "2024-03-15",
        "status": "analyzed",
        "items": [
            {"name": "空腹血糖", "value": 6.8, "unit": "mmol/L", "reference_min": 3.9, "reference_max": 6.1, "status": "high"},
            {"name": "糖化血红蛋白", "value": 6.5, "unit": "%", "reference_min": 4.0, "reference_max": 6.0, "status": "high"},
            {"name": "总胆固醇", "value": 5.8, "unit": "mmol/L", "reference_min": 3.1, "reference_max": 5.7, "status": "high"},
            {"name": "甘油三酯", "value": 1.9, "unit": "mmol/L", "reference_min": 0.4, "reference_max": 1.7, "status": "high"},
            {"name": "血压收缩压", "value": 135, "unit": "mmHg", "reference_min": 90, "reference_max": 120, "status": "high"},
            {"name": "血压舒张压", "value": 85, "unit": "mmHg", "reference_min": 60, "reference_max": 80, "status": "high"},
            {"name": "体重指数", "value": 26.5, "unit": "BMI", "reference_min": 18.5, "reference_max": 24.0, "status": "high"}
        ]
    }


@router.post("/{patient_id}/reports")
async def upload_report(patient_id: str, report: dict):
    """上传体检报告"""
    report_id = f"report_{len(_reports) + 1}"
    new_report = Report(
        id=report_id,
        patient_id=patient_id,
        title=report.get("title", ""),
        report_type=report.get("report_type", ""),
        hospital=report.get("hospital"),
        exam_date=report.get("exam_date", ""),
        status="pending",
        items=[]
    )
    _reports[report_id] = new_report
    return new_report


@router.post("/{patient_id}/reports/{report_id}/analyze")
async def analyze_report(patient_id: str, report_id: str):
    """AI分析体检报告"""
    # 获取报告详情
    report = await get_report_detail(patient_id, report_id)
    
    # 生成AI分析
    high_items = [item for item in report.get("items", []) if item.get("status") == "high"]
    risk_alerts = []
    recommendations = []
    
    for item in high_items:
        name = item.get("name", "")
        if "血糖" in name or "糖化" in name:
            risk_alerts.append(f"{name}偏高，需关注糖尿病风险")
            recommendations.append("建议内分泌科就诊复查")
            recommendations.append("减少高糖高脂饮食")
        elif "血压" in name:
            risk_alerts.append(f"{name}偏高，需关注高血压风险")
            recommendations.append("建议心血管内科就诊")
            recommendations.append("限制钠盐摄入")
        elif "胆固醇" in name or "甘油三酯" in name:
            risk_alerts.append(f"{name}偏高，需关注心脑血管风险")
            recommendations.append("建议清淡饮食")
            recommendations.append("增加运动")
        elif "BMI" in name:
            risk_alerts.append("体重超标，需关注")
            recommendations.append("建议减重")
    
    if not high_items:
        analysis = "您的各项指标均在正常范围内，继续保持健康的生活方式！"
        risk_alerts = []
        recommendations = ["继续保持规律作息", "适量运动", "均衡饮食"]
    else:
        analysis = f"本次体检发现{len(high_items)}项指标异常，建议尽快就医复查。同时注意调整生活方式。"
    
    return {
        "analysis": analysis,
        "recommendations": recommendations[:5],
        "risk_alerts": risk_alerts
    }


@router.post("/{patient_id}/reports/{report_id}/manual-input")
async def manual_input(patient_id: str, report_id: str, data: dict):
    """手动录入体检数据"""
    items = data.get("items", [])
    
    # 更新报告状态
    if report_id not in _reports:
        _reports[report_id] = Report(
            id=report_id,
            patient_id=patient_id,
            title="手动录入报告",
            report_type="manual",
            exam_date=datetime.now().strftime("%Y-%m-%d"),
            status="pending",
            items=[]
        )
    
    report_items = []
    for item in items:
        value = item.get("value", 0)
        name = item.get("name", "")
        unit = item.get("unit", "")
        
        # 判断状态
        status = "normal"
        ref_min, ref_max = 0, 100
        
        if "血糖" in name:
            ref_min, ref_max = 3.9, 6.1
        elif "血压" in name and "收缩" in name:
            ref_min, ref_max = 90, 120
        elif "血压" in name and "舒张" in name:
            ref_min, ref_max = 60, 80
        elif "胆固醇" in name:
            ref_min, ref_max = 3.1, 5.7
            
        if value < ref_min or value > ref_max:
            status = "high" if value > ref_max else "low"
            
        report_items.append(ReportItem(
            name=name,
            value=value,
            unit=unit,
            reference_min=ref_min,
            reference_max=ref_max,
            status=status
        ))
    
    _reports[report_id].items = report_items
    _reports[report_id].status = "pending"
    
    return {"success": True, "items": report_items}
