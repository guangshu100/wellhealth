"""
健康预测服务
包括：健康趋势分析、风险评估、预警系统
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.models import VitalRecord, HealthAlert
from app.utils.database import get_db_session
from app.services.family_service import HealthAlertService

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class RiskPrediction:
    """风险预测结果"""

    risk_type: str
    risk_level: RiskLevel
    probability: float
    factors: List[str]
    recommendations: List[str]
    suggested_actions: List[str]


@dataclass
class TrendAnalysis:
    """趋势分析结果"""

    metric: str
    trend: str  # "rising", "falling", "stable", "fluctuating"
    change_rate: float
    avg_value: float
    min_value: float
    max_value: float
    prediction: Optional[str]
    alerts: List[str]


class HealthTrendAnalysisService:
    """健康趋势分析服务"""

    # 正常范围配置
    NORMAL_RANGES = {
        "blood_pressure_systolic": {"min": 90, "max": 140, "unit": "mmHg"},
        "blood_pressure_diastolic": {"min": 60, "max": 90, "unit": "mmHg"},
        "blood_sugar_fasting": {"min": 4.4, "max": 7.0, "unit": "mmol/L"},
        "blood_sugar_postprandial": {"min": 4.4, "max": 10.0, "unit": "mmol/L"},
        "heart_rate": {"min": 60, "max": 100, "unit": "bpm"},
        "temperature": {"min": 36.1, "max": 37.2, "unit": "°C"},
        "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"},
    }

    @staticmethod
    async def analyze_trend(patient_id: str, vital_type: str, days: int = 30) -> TrendAnalysis:
        """分析健康指标趋势"""
        # 从数据库查询真实数据
        with get_db_session() as session:
            from sqlalchemy import select, and_

            cutoff = datetime.utcnow() - timedelta(days=days)

            result = session.execute(
                select(VitalRecord)
                .where(
                    and_(
                        VitalRecord.patient_id == patient_id,
                        VitalRecord.vital_type == vital_type,
                        VitalRecord.recorded_at >= cutoff,
                    )
                )
                .order_by(VitalRecord.recorded_at.asc())
            )
            records = result.scalars().all()

            # 转换为数值列表
            values = []
            for r in records:
                val = r.value.get("value") if isinstance(r.value, dict) else r.value
                if isinstance(val, (int, float)):
                    values.append({"date": r.recorded_at, "value": val})

            # 如果没有数据，返回默认值
            if not values:
                return TrendAnalysis(
                    metric=vital_type,
                    trend="stable",
                    change_rate=0,
                    avg_value=0,
                    min_value=0,
                    max_value=0,
                    prediction="暂无数据",
                    alerts=["暂无数据，请先记录健康数据"],
                )

            if not values:
                return TrendAnalysis(
                    metric=vital_type,
                    trend="stable",
                    change_rate=0,
                    avg_value=0,
                    min_value=0,
                    max_value=0,
                    prediction="数据不足",
                    alerts=[],
                )

            # 计算统计数据
            value_list = [v["value"] for v in values]
            avg_value = sum(value_list) / len(value_list)
            min_value = min(value_list)
            max_value = max(value_list)

            # 计算趋势
            recent_avg = sum(value_list[-7:]) / 7
            older_avg = sum(value_list[:7]) / 7
            change_rate = (recent_avg - older_avg) / older_avg * 100 if older_avg != 0 else 0

            if abs(change_rate) < 5:
                trend = "stable"
            elif change_rate > 0:
                trend = "rising" if "pressure" in vital_type else "falling"
            else:
                trend = "falling" if "pressure" in vital_type else "rising"

            # 检测波动
            variance = sum((x - avg_value) ** 2 for x in value_list) / len(value_list)
            is_fluctuating = variance > (avg_value * 0.1) ** 2

            if is_fluctuating:
                trend = "fluctuating"

            # 生成预警
            alerts = []
            normal_range = HealthTrendAnalysisService.NORMAL_RANGES.get(vital_type)
            if normal_range:
                if recent_avg > normal_range["max"]:
                    alerts.append(f"近期平均值偏高")
                elif recent_avg < normal_range["min"]:
                    alerts.append(f"近期平均值偏低")

            if is_fluctuating:
                alerts.append("数据波动较大，建议关注")

            # 简单预测（基于线性趋势）
            if trend == "rising" and "pressure" in vital_type:
                prediction = "建议加强干预，控制进一步上升"
            elif trend == "falling" and "sugar" in vital_type:
                prediction = "控制良好继续保持"
            else:
                prediction = "趋势稳定"

            return TrendAnalysis(
                metric=vital_type,
                trend=trend,
                change_rate=round(change_rate, 1),
                avg_value=round(avg_value, 1),
                min_value=round(min_value, 1),
                max_value=round(max_value, 1),
                prediction=prediction,
                alerts=alerts,
            )


class HealthRiskPredictionService:
    """健康风险预测服务"""

    # 风险因素配置
    RISK_FACTORS = {
        "diabetes": {
            "age_above_60": {"weight": 2, "threshold": 60},
            "bmi_above_28": {"weight": 3, "threshold": 28},
            "family_history": {"weight": 3},
            "hypertension": {"weight": 2},
            "sedentary": {"weight": 1},
            "high_sugar_diet": {"weight": 2},
        },
        "hypertension": {
            "age_above_55": {"weight": 2, "threshold": 55},
            "bmi_above_28": {"weight": 2, "threshold": 28},
            "family_history": {"weight": 3},
            "high_salt_diet": {"weight": 2},
            "stress": {"weight": 2},
            "sedentary": {"weight": 1},
        },
        "heart_disease": {
            "age_above_65": {"weight": 2, "threshold": 65},
            "diabetes": {"weight": 3},
            "hypertension": {"weight": 3},
            "smoking": {"weight": 3},
            "high_cholesterol": {"weight": 2},
            "family_history": {"weight": 3},
        },
    }

    async def predict_risk(
        self, patient_data: Dict[str, Any], risk_type: str = "diabetes"
    ) -> RiskPrediction:
        """预测疾病风险"""
        risk_factors = self.RISK_FACTORS.get(risk_type, {})

        total_score = 0
        max_score = 0
        identified_factors = []

        for factor, config in risk_factors.items():
            weight = config.get("weight", 1)
            max_score += weight * 2  # 每个因素最高2分

            # 检查是否存在该风险因素
            if self._check_factor(factor, patient_data):
                # 根据阈值计算得分
                threshold = config.get("threshold")
                if threshold:
                    value = patient_data.get(factor, 0)
                    if value > threshold:
                        total_score += weight
                        identified_factors.append(self._factor_label(factor))
                else:
                    # 二元因素
                    if patient_data.get(factor):
                        total_score += weight
                        identified_factors.append(self._factor_label(factor))

        # 计算风险概率
        probability = (total_score / max_score) if max_score > 0 else 0

        # 确定风险等级
        if probability < 0.2:
            risk_level = RiskLevel.LOW
        elif probability < 0.5:
            risk_level = RiskLevel.MEDIUM
        elif probability < 0.8:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.URGENT

        # 生成建议
        recommendations = self._generate_recommendations(risk_type, risk_level, identified_factors)

        # 生成建议行动
        suggested_actions = self._generate_actions(risk_type, risk_level)

        return RiskPrediction(
            risk_type=risk_type,
            risk_level=risk_level,
            probability=round(probability, 2),
            factors=identified_factors,
            recommendations=recommendations,
            suggested_actions=suggested_actions,
        )

    def _check_factor(self, factor: str, patient_data: Dict) -> bool:
        """检查风险因素"""
        factor_mappings = {
            "age_above_60": "age",
            "age_above_55": "age",
            "age_above_65": "age",
            "bmi_above_28": "bmi",
            "family_history": "family_history",
            "diabetes": "has_diabetes",
            "hypertension": "has_hypertension",
            "smoking": "smoking",
            "high_cholesterol": "high_cholesterol",
            "high_salt_diet": "high_salt_diet",
            "high_sugar_diet": "high_sugar_diet",
            "sedentary": "sedentary_lifestyle",
            "stress": "high_stress",
        }

        data_key = factor_mappings.get(factor)
        if not data_key:
            return False

        return patient_data.get(data_key, False)

    def _factor_label(self, factor: str) -> str:
        """风险因素标签"""
        labels = {
            "age_above_60": "年龄超过60岁",
            "age_above_55": "年龄超过55岁",
            "age_above_65": "年龄超过65岁",
            "bmi_above_28": "BMI超过28",
            "family_history": "家族病史",
            "diabetes": "糖尿病",
            "hypertension": "高血压",
            "smoking": "吸烟",
            "high_cholesterol": "高胆固醇",
            "high_salt_diet": "高盐饮食",
            "high_sugar_diet": "高糖饮食",
            "sedentary": "久坐不动",
            "stress": "压力大",
        }
        return labels.get(factor, factor)

    def _generate_recommendations(
        self, risk_type: str, risk_level: RiskLevel, factors: List[str]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if risk_level == RiskLevel.LOW:
            recommendations.append("保持健康生活方式")
            recommendations.append("定期体检")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("建议调整饮食结构")
            recommendations.append("增加运动频率")
            recommendations.append("定期监测相关指标")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("建议尽快就医检查")
            recommendations.append("需要专业健康指导")
            recommendations.append("密切监测健康指标")
        else:
            recommendations.append("需要立即就医")
            recommendations.append("建议进行全面体检")

        return recommendations

    def _generate_actions(self, risk_type: str, risk_level: RiskLevel) -> List[str]:
        """生成建议行动"""
        actions = []

        if risk_type == "diabetes":
            if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.URGENT]:
                actions.append("预约内分泌科就诊")
                actions.append("开始血糖监测")
                actions.append("控制碳水化合物摄入")

        elif risk_type == "hypertension":
            if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.URGENT]:
                actions.append("预约心血管科就诊")
                actions.append("每日监测血压")
                actions.append("限制盐分摄入")

        elif risk_type == "heart_disease":
            if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.URGENT]:
                actions.append("预约心内科就诊")
                actions.append("进行心电图检查")
                actions.append("戒烟限酒")

        return actions


class ComplicationPredictionService:
    """并发症预测服务"""

    @staticmethod
    async def predict_complications(
        patient_id: str, disease_type: str, patient_data: Dict[str, Any]
    ) -> List[RiskPrediction]:
        """预测并发症风险"""
        predictions = []

        if disease_type == "diabetes":
            # 糖尿病并发症
            complications = [
                (
                    "diabetic_retinopathy",
                    "糖尿病视网膜病变",
                    {"duration_above_5": 5, "blood_sugar_control": "poor"},
                ),
                (
                    "diabetic_nephropathy",
                    "糖尿病肾病",
                    {"duration_above_5": 5, "hypertension": True},
                ),
                (
                    "diabetic_neuropathy",
                    "糖尿病神经病变",
                    {"duration_above_5": 5, "bmi_above_28": True},
                ),
                ("diabetic_foot", "糖尿病足", {"duration_above_5": 5, "smoking": True}),
            ]

            for comp_id, comp_name, factors in complications:
                risk = await HealthRiskPredictionService().predict_risk(patient_data, comp_id)
                predictions.append(risk)

        elif disease_type == "hypertension":
            # 高血压并发症
            complications = [
                ("stroke", "脑卒中", {"age_above_60": 60, "hypertension_duration_above_5": True}),
                ("heart_failure", "心力衰竭", {"age_above_65": 65, "has_diabetes": True}),
                ("kidney_damage", "肾功能损害", {"duration_above_5": 5, "high_salt_diet": True}),
            ]

            for comp_id, comp_name, factors in complications:
                risk = await HealthRiskPredictionService().predict_risk(patient_data, comp_id)
                predictions.append(risk)

        return predictions


class InterventionEffectPredictionService:
    """干预效果预测服务"""

    @staticmethod
    async def predict_effect(
        intervention_type: str, patient_data: Dict[str, Any], duration_days: int = 30
    ) -> Dict[str, Any]:
        """预测干预效果"""
        # 基于规则的简单预测
        effects = {
            "diet": {
                "blood_sugar": {"change": -0.15, "time": 30},
                "blood_pressure": {"change": -0.08, "time": 30},
                "bmi": {"change": -0.05, "time": 30},
            },
            "exercise": {
                "blood_sugar": {"change": -0.10, "time": 14},
                "blood_pressure": {"change": -0.12, "time": 21},
                "weight": {"change": -0.03, "time": 30},
            },
            "medication": {
                "blood_sugar": {"change": -0.25, "time": 7},
                "blood_pressure": {"change": -0.20, "time": 7},
            },
            "lifestyle": {
                "blood_sugar": {"change": -0.12, "time": 30},
                "blood_pressure": {"change": -0.10, "time": 30},
                "stress_level": {"change": -0.20, "time": 30},
            },
        }

        effect = effects.get(intervention_type, {})

        predicted_effects = {}
        for metric, data in effect.items():
            change_rate = data["change"]
            time_needed = data["time"]

            # 获取当前值
            current_value = patient_data.get(metric, 100)

            # 计算预测值
            progress = min(duration_days / time_needed, 1.0)
            predicted_value = current_value * (1 + change_rate * progress)

            predicted_effects[metric] = {
                "current": current_value,
                "predicted": round(predicted_value, 2),
                "change_rate": round(change_rate * 100, 1),
                "time_needed": time_needed,
                "confidence": "medium",
            }

        return {
            "intervention_type": intervention_type,
            "duration_days": duration_days,
            "predicted_effects": predicted_effects,
            "recommendations": InterventionEffectPredictionService._generate_recommendations(
                intervention_type, predicted_effects
            ),
        }

    @staticmethod
    def _generate_recommendations(intervention_type: str, effects: Dict) -> List[str]:
        """生成干预建议"""
        recommendations = []

        if intervention_type == "diet":
            recommendations.append("控制每日总热量摄入")
            recommendations.append("增加膳食纤维摄入")
            recommendations.append("减少精制糖摄入")

        elif intervention_type == "exercise":
            recommendations.append("每周至少150分钟中等强度运动")
            recommendations.append("餐后30-60分钟适度运动")
            recommendations.append("运动前后监测血糖")

        elif intervention_type == "medication":
            recommendations.append("按时按量服用药物")
            recommendations.append("定期复查")
            recommendations.append("关注药物副作用")

        return recommendations
