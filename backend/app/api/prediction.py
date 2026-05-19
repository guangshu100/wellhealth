"""
健康预测API
包括：血糖预测、并发症风险预测、干预效果预测
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models import VitalRecord, HealthAlert
from app.services.health_prediction_service import (
    HealthTrendAnalysisService,
    HealthRiskPredictionService,
    RiskLevel,
)

router = APIRouter(prefix="/api/v1/prediction", tags=["健康预测"])


# ========== 数据模型 ==========


class BloodSugarPredictionRequest(BaseModel):
    patient_id: str
    days: int = 7


class ComplicationPredictionRequest(BaseModel):
    patient_id: str
    complication_type: str  # retinopathy, nephropathy, neuropathy, cardiovascular, foot


class InterventionEffectRequest(BaseModel):
    patient_id: str
    intervention_type: str  # exercise, diet, medication, monitoring, comprehensive


# ========== 血糖预测API ==========


@router.post("/blood-sugar")
async def predict_blood_sugar(request: BloodSugarPredictionRequest, db: Session = Depends(get_db)):
    """预测未来血糖趋势"""
    try:
        # 获取历史数据
        days = request.days
        cutoff = datetime.utcnow() - timedelta(days=days + 7)  # 多获取7天用于趋势分析

        result = db.execute(
            select(VitalRecord)
            .where(
                and_(
                    VitalRecord.patient_id == request.patient_id,
                    VitalRecord.vital_type == "blood_sugar",
                    VitalRecord.recorded_at >= cutoff,
                )
            )
            .order_by(VitalRecord.recorded_at.asc())
        )
        records = result.scalars().all()

        # 提取数值
        values = []
        for r in records:
            val = r.value.get("value") if isinstance(r.value, dict) else r.value
            if isinstance(val, (int, float)):
                values.append(val)

        # 分析趋势并预测
        if len(values) < 3:
            return {
                "success": True,
                "prediction": {
                    "id": str(uuid.uuid4()),
                    "patient_id": request.patient_id,
                    "type": "blood_sugar",
                    "prediction_date": datetime.utcnow().isoformat(),
                    "prediction_result": {
                        "risk_level": "low",
                        "probability": 0.3,
                        "trend": "stable",
                        "factors": ["数据不足"],
                        "recommendations": ["建议记录更多血糖数据以便准确预测"],
                    },
                    "created_at": datetime.utcnow().isoformat(),
                },
            }

        avg = sum(values) / len(values)

        # 计算近期趋势
        recent_values = values[-7:] if len(values) >= 7 else values
        if len(values) >= 7:
            older_values = values[:7]
        elif len(values) > 3:
            older_values = values[:len(values) // 2]
        else:
            older_values = []

        if recent_values and older_values:
            recent_avg = sum(recent_values) / len(recent_values)
            older_avg = sum(older_values) / len(older_values)

            if recent_avg > older_avg * 1.1:
                trend = "rising"
                risk_level = "medium"
                probability = 0.5
            elif recent_avg < older_avg * 0.9:
                trend = "falling"
                risk_level = "low"
                probability = 0.2
            else:
                trend = "stable"
                risk_level = "low"
                probability = 0.25
        else:
            trend = "stable"
            risk_level = "low"
            probability = 0.3

        # 生成预测结果
        factors = []
        if avg > 7.0:
            factors.append("历史血糖平均值偏高")
        if avg > 10.0:
            factors.append("血糖控制不佳")
        if values[-1] > values[0] * 1.1:
            factors.append("近期呈上升趋势")

        if not factors:
            factors.append("血糖控制良好")

        recommendations = []
        if risk_level == "medium":
            recommendations.append("注意饮食控制")
            recommendations.append("适当增加运动")
        elif risk_level == "high":
            recommendations.append("建议及时就医调整用药")
            recommendations.append("密切监测血糖变化")
        else:
            recommendations.append("继续保持当前生活习惯")

        return {
            "success": True,
            "prediction": {
                "id": str(uuid.uuid4()),
                "patient_id": request.patient_id,
                "type": "blood_sugar",
                "prediction_date": datetime.utcnow().isoformat(),
                "prediction_result": {
                    "risk_level": risk_level,
                    "probability": probability,
                    "trend": trend,
                    "factors": factors,
                    "recommendations": recommendations,
                },
                "created_at": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 并发症风险预测API ==========


@router.post("/complication")
async def predict_complication(
    request: ComplicationPredictionRequest, db: Session = Depends(get_db)
):
    """预测并发症风险"""
    try:
        # 获取患者相关数据
        cutoff = datetime.utcnow() - timedelta(days=30)

        # 获取血糖记录
        sugar_result = db.execute(
            select(VitalRecord).where(
                and_(
                    VitalRecord.patient_id == request.patient_id,
                    VitalRecord.vital_type == "blood_sugar",
                    VitalRecord.recorded_at >= cutoff,
                )
            )
        )
        sugar_records = sugar_result.scalars().all()

        # 获取血压记录
        bp_result = db.execute(
            select(VitalRecord).where(
                and_(
                    VitalRecord.patient_id == request.patient_id,
                    VitalRecord.vital_type == "blood_pressure",
                    VitalRecord.recorded_at >= cutoff,
                )
            )
        )
        bp_records = bp_result.scalars().all()

        # 获取预警记录
        alert_result = db.execute(
            select(HealthAlert).where(
                and_(HealthAlert.patient_id == request.patient_id, HealthAlert.created_at >= cutoff)
            )
        )
        alerts = alert_result.scalars().all()

        # 计算风险
        risk_score = 0
        factors = []

        sugar_values = []
        for r in sugar_records:
            if isinstance(r.value, dict):
                val = r.value.get("value")
                if isinstance(val, (int, float)):
                    sugar_values.append(val)
        if sugar_values:
            avg_sugar = sum(sugar_values) / len(sugar_values)
            if avg_sugar > 7.0:
                risk_score += 2
                factors.append("血糖长期偏高")
            if avg_sugar > 10.0:
                risk_score += 3
                factors.append("血糖控制不佳")

        bp_values = []
        for r in bp_records:
            if isinstance(r.value, dict):
                val = r.value.get("systolic") or r.value.get("value")
                if isinstance(val, (int, float)):
                    bp_values.append(val)
        if bp_values:
            avg_bp = sum(bp_values) / len(bp_values)
            if avg_bp > 140:
                risk_score += 2
                factors.append("血压偏高")

        # 预警分析
        high_alerts = [a for a in alerts if a.severity in ["high", "urgent"]]
        if len(high_alerts) > 3:
            risk_score += 2
            factors.append("近期多次异常预警")

        # 根据并发症类型调整风险
        complication_risk = {
            "retinopathy": {"base": risk_score, "factors": ["血糖控制", "病程长短"]},
            "nephropathy": {"base": risk_score, "factors": ["血糖", "血压", "蛋白尿"]},
            "neuropathy": {"base": risk_score, "factors": ["血糖控制", "烟酒习惯"]},
            "cardiovascular": {"base": risk_score + 1, "factors": ["血压", "血脂", "吸烟"]},
            "foot": {"base": risk_score, "factors": ["血糖", "足部护理"]},
        }

        config = complication_risk.get(
            request.complication_type, {"base": risk_score, "factors": []}
        )
        final_score = min(config["base"] / 10, 1.0)  # 归一化到0-1

        if final_score < 0.2:
            risk_level = "low"
        elif final_score < 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"

        # 生成建议
        recommendations = []
        if request.complication_type == "retinopathy":
            recommendations.append("建议每年进行眼底检查")
            recommendations.append("控制血糖在目标范围内")
        elif request.complication_type == "nephropathy":
            recommendations.append("定期检测尿微量白蛋白")
            recommendations.append("控制血压")
        elif request.complication_type == "neuropathy":
            recommendations.append("注意足部护理")
            recommendations.append("戒烟限酒")
        elif request.complication_type == "cardiovascular":
            recommendations.append("控制血压血脂")
            recommendations.append("适当运动")
        elif request.complication_type == "foot":
            recommendations.append("每天检查足部")
            recommendations.append("选择合适的鞋袜")

        return {
            "success": True,
            "prediction": {
                "risk_level": risk_level,
                "probability": round(final_score, 2),
                "factors": factors if factors else ["无明显风险因素"],
                "recommendations": recommendations if recommendations else ["继续保持健康生活方式"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 干预效果预测API ==========


@router.post("/intervention-effect")
async def predict_intervention_effect(
    request: InterventionEffectRequest, db: Session = Depends(get_db)
):
    """预测干预方案效果"""
    try:
        # 获取当前数据
        cutoff = datetime.utcnow() - timedelta(days=7)

        result = db.execute(
            select(VitalRecord)
            .where(
                and_(
                    VitalRecord.patient_id == request.patient_id,
                    VitalRecord.vital_type == "blood_sugar",
                    VitalRecord.recorded_at >= cutoff,
                )
            )
            .order_by(VitalRecord.recorded_at.desc())
        )
        records = result.scalars().all()

        # 获取当前值
        current_value = 6.5  # 默认值
        if records:
            val = (
                records[0].value.get("value")
                if isinstance(records[0].value, dict)
                else records[0].value
            )
            if isinstance(val, (int, float)):
                current_value = val

        # 干预效果预测
        intervention_effects = {
            "exercise": {
                "name": "增加运动",
                "effect": -0.5,
                "confidence": 0.85,
                "timeline": [
                    {"day": 1, "predicted_value": current_value},
                    {"day": 7, "predicted_value": round(current_value - 0.3, 1)},
                    {"day": 14, "predicted_value": round(current_value - 0.5, 1)},
                    {"day": 30, "predicted_value": round(current_value - 0.8, 1)},
                ],
                "recommendations": [
                    "每周至少150分钟中等强度运动",
                    "运动前后监测血糖",
                    "注意运动后低血糖",
                ],
            },
            "diet": {
                "name": "调整饮食",
                "effect": -0.6,
                "confidence": 0.9,
                "timeline": [
                    {"day": 1, "predicted_value": current_value},
                    {"day": 7, "predicted_value": round(current_value - 0.2, 1)},
                    {"day": 14, "predicted_value": round(current_value - 0.4, 1)},
                    {"day": 30, "predicted_value": round(current_value - 0.6, 1)},
                ],
                "recommendations": ["控制每日碳水摄入", "增加膳食纤维", "少食多餐"],
            },
            "medication": {
                "name": "药物治疗调整",
                "effect": -0.8,
                "confidence": 0.95,
                "timeline": [
                    {"day": 1, "predicted_value": current_value},
                    {"day": 7, "predicted_value": round(current_value - 0.4, 1)},
                    {"day": 14, "predicted_value": round(current_value - 0.6, 1)},
                    {"day": 30, "predicted_value": round(current_value - 0.8, 1)},
                ],
                "recommendations": ["遵医嘱调整用药", "注意药物副作用", "定期复查"],
            },
            "monitoring": {
                "name": "血糖监测强化",
                "effect": -0.3,
                "confidence": 0.75,
                "timeline": [
                    {"day": 1, "predicted_value": current_value},
                    {"day": 7, "predicted_value": round(current_value - 0.1, 1)},
                    {"day": 14, "predicted_value": round(current_value - 0.2, 1)},
                    {"day": 30, "predicted_value": round(current_value - 0.3, 1)},
                ],
                "recommendations": ["每日监测血糖4-7次", "记录血糖日志", "分析血糖波动规律"],
            },
            "comprehensive": {
                "name": "综合管理",
                "effect": -1.0,
                "confidence": 0.92,
                "timeline": [
                    {"day": 1, "predicted_value": current_value},
                    {"day": 7, "predicted_value": round(current_value - 0.3, 1)},
                    {"day": 14, "predicted_value": round(current_value - 0.6, 1)},
                    {"day": 30, "predicted_value": round(current_value - 1.0, 1)},
                ],
                "recommendations": ["饮食+运动+监测综合干预", "定期复查", "保持健康生活方式"],
            },
        }

        effect = intervention_effects.get(
            request.intervention_type, intervention_effects["comprehensive"]
        )

        return {
            "success": True,
            "prediction": {
                "intervention_type": request.intervention_type,
                "intervention_name": effect["name"],
                "predicted_effect": {
                    "blood_sugar_change": effect["effect"],
                    "confidence": effect["confidence"],
                },
                "timeline": effect["timeline"],
                "recommendations": effect["recommendations"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 预测历史API ==========


@router.get("/history/{patient_id}")
async def get_prediction_history(
    patient_id: str, type: Optional[str] = None, limit: int = 10, db: Session = Depends(get_db)
):
    """获取预测历史"""
    try:
        # 目前预测结果存储在内存中，返回示例数据
        return {"success": True, "predictions": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
