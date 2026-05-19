"""
干预效果模拟模块
基于MiroFish理念，模拟不同干预方案的效果
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """干预类型"""

    DIET = "diet"  # 饮食干预
    EXERCISE = "exercise"  # 运动干预
    MEDICATION = "medication"  # 药物调整
    LIFESTYLE = "lifestyle"  # 生活方式
    COMBINED = "combined"  # 综合干预


class SimulationStatus(str, Enum):
    """模拟状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VitalTrend:
    """生命体征趋势"""

    date: datetime
    value: float
    unit: str


@dataclass
class Intervention:
    """干预方案"""

    type: InterventionType
    name: str
    description: str
    duration_days: int
    parameters: Dict = field(default_factory=dict)


@dataclass
class SimulationResult:
    """模拟结果"""

    intervention: Intervention
    status: SimulationStatus
    baseline_values: Dict
    predicted_values: Dict
    timeline: List[Dict]
    effectiveness: float
    risk_level: str
    recommendations: List[str]


class InterventionSimulator:
    """
    干预效果模拟器
    基于患者当前状态，模拟不同干预方案的效果
    """

    def __init__(self):
        self.models = {}
        self._init_models()

    def _init_models(self):
        """初始化模拟模型，优先从数据库加载"""
        self.models = self._get_default_models()

        db_models = self._load_models_from_db()
        if db_models:
            self._merge_models(db_models)
            logger.info("Merged models from database")

    def _get_default_models(self) -> dict:
        """获取默认模型参数"""
        return {
            "diabetes": {
                "血糖": {
                    "diet": {"effect": -0.15, "time": 30, "risk": "low"},
                    "exercise": {"effect": -0.10, "time": 14, "risk": "low"},
                    "medication": {"effect": -0.25, "time": 7, "risk": "medium"},
                    "combined": {"effect": -0.35, "time": 30, "risk": "medium"},
                },
                "HbA1c": {
                    "diet": {"effect": -0.10, "time": 90, "risk": "low"},
                    "exercise": {"effect": -0.08, "time": 60, "risk": "low"},
                    "medication": {"effect": -0.20, "time": 30, "risk": "medium"},
                    "combined": {"effect": -0.25, "time": 90, "risk": "medium"},
                },
            },
            "hypertension": {
                "收缩压": {
                    "diet": {"effect": -0.05, "time": 30, "risk": "low"},
                    "exercise": {"effect": -0.04, "time": 30, "risk": "low"},
                    "medication": {"effect": -0.10, "time": 14, "risk": "medium"},
                    "combined": {"effect": -0.12, "time": 30, "risk": "medium"},
                },
                "舒张压": {
                    "diet": {"effect": -0.03, "time": 30, "risk": "low"},
                    "exercise": {"effect": -0.02, "time": 30, "risk": "low"},
                    "medication": {"effect": -0.05, "time": 14, "risk": "medium"},
                    "combined": {"effect": -0.08, "time": 30, "risk": "medium"},
                },
            },
        }

    def _merge_models(self, db_models: dict):
        """合并数据库模型到默认模型"""
        for disease, vitals in db_models.items():
            if disease not in self.models:
                self.models[disease] = vitals
            else:
                for vital, interventions in vitals.items():
                    if vital not in self.models[disease]:
                        self.models[disease][vital] = interventions
                    else:
                        self.models[disease][vital].update(interventions)

    def _load_models_from_db(self) -> dict:
        """从数据库加载干预模型参数"""
        disease_map = {
            "2型糖尿病": "diabetes",
            "糖尿病": "diabetes",
            "高血压": "hypertension",
            "高血压病": "hypertension",
        }

        try:
            from sqlalchemy import text
            from app.utils.database import SessionLocal

            db = SessionLocal()
            try:
                result = db.execute(
                    text("""
                    SELECT target_disease, type, name, description, 
                           duration_days, effectiveness, risk_level
                    FROM interventions 
                    WHERE status = 'active'
                """)
                )
                rows = result.fetchall()

                if not rows:
                    return {}

                models = {}
                for row in rows:
                    disease_cn = row[0]
                    int_type = row[1]

                    disease = disease_map.get(disease_cn, disease_cn.lower())
                    if disease not in models:
                        models[disease] = {}

                    vital = "血糖" if "diabetes" in disease or "糖尿病" in disease_cn else "收缩压"
                    if vital not in models[disease]:
                        models[disease][vital] = {}

                    # effectiveness 是有效率(0-100)，转换为效果比例时需要缩小
                    # 75%有效率对应约15%的指标下降，所以除以500
                    models[disease][vital][int_type] = {
                        "effect": -float(row[5]) / 500 if row[5] else 0,
                        "time": row[4] if row[4] else 30,
                        "risk": row[6] if row[6] else "low",
                    }

                logger.info(f"Loaded {len(models)} disease models from database")
                return models
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to load models from database: {e}")
            return {}

    async def simulate(
        self, patient_data: Dict, interventions: List[Intervention]
    ) -> SimulationResult:
        """
        模拟干预效果

        Args:
            patient_data: 患者数据
                - disease: 疾病类型 (diabetes/hypertension)
                - current_vitals: 当前生命体征
                - history: 历史数据(可选)
            interventions: 干预方案列表
        """
        print(f"[DEBUG] simulate() called")
        disease = patient_data.get("disease", "diabetes")
        current_vitals = patient_data.get("current_vitals", {})
        print(f"[DEBUG] disease={disease}, current_vitals={current_vitals}")

        logger.info(f"simulate called with disease={disease}, current_vitals={current_vitals}")

        if not current_vitals:
            return SimulationResult(
                intervention=Intervention(
                    type=InterventionType.COMBINED, name="无效干预", description="", duration_days=0
                ),
                status=SimulationStatus.FAILED,
                baseline_values={},
                predicted_values={},
                timeline=[],
                effectiveness=0,
                risk_level="unknown",
                recommendations=["请提供患者当前的生命体征数据"],
            )

        # 确定干预类型
        if len(interventions) > 1:
            intervention_type = InterventionType.COMBINED
        elif interventions:
            intervention_type = interventions[0].type
        else:
            intervention_type = InterventionType.LIFESTYLE

        # 获取模型参数
        model_params = self._get_model_params(disease, intervention_type)

        # 计算预测值
        baseline_values = current_vitals.copy()
        predicted_values = {}
        timeline = []

        for vital_name, current_value in current_vitals.items():
            if vital_name in model_params:
                params = model_params[vital_name]
                effect = params["effect"]

                # 计算预测值
                predicted = current_value * (1 + effect)
                predicted_values[vital_name] = round(predicted, 2)

                # 生成时间线
                days = params["time"]
                for day in range(0, days + 1, 7):
                    progress = day / days
                    value = current_value + (predicted - current_value) * progress
                    timeline.append({"day": day, vital_name: round(value, 2)})

        # 计算有效性
        effectiveness = self._calculate_effectiveness(baseline_values, predicted_values, disease)

        # 评估风险
        risk_level = self._assess_risk(intervention_type, predicted_values, disease)

        # 生成建议
        recommendations = self._generate_recommendations(
            intervention_type, predicted_values, disease
        )

        return SimulationResult(
            intervention=Intervention(
                type=intervention_type,
                name=self._get_intervention_name(intervention_type),
                description=self._get_intervention_description(intervention_type),
                duration_days=model_params.get("time", 30) if model_params else 30,
                parameters={i.type: i.parameters for i in interventions},
            ),
            status=SimulationStatus.COMPLETED,
            baseline_values=baseline_values,
            predicted_values=predicted_values,
            timeline=timeline,
            effectiveness=effectiveness,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def _get_model_params(self, disease: str, intervention_type: InterventionType) -> Dict:
        """获取模型参数"""
        print(f"[DEBUG] _get_model_params called: disease={disease}, intervention_type={intervention_type}")
        print(f"[DEBUG] self.models keys: {list(self.models.keys())}")
        print(f"[DEBUG] self.models: {self.models}")
        
        disease_models = self.models.get(disease, {})
        print(f"[DEBUG] disease_models for '{disease}': {disease_models}")

        type_str = (
            intervention_type.value if intervention_type != InterventionType.LIFESTYLE else "diet"
        )
        print(f"[DEBUG] type_str: {type_str}")

        params = {}
        for vital, interventions in disease_models.items():
            print(f"[DEBUG] Checking vital='{vital}', interventions keys={list(interventions.keys())}")
            if type_str in interventions:
                params[vital] = interventions[type_str]
                print(f"[DEBUG] Found params for {vital}: {params[vital]}")

        print(f"[DEBUG] Final params: {params}")
        return params

    def _calculate_effectiveness(self, baseline: Dict, predicted: Dict, disease: str) -> float:
        """计算干预有效性"""
        if not baseline or not predicted:
            return 0.0

        total_effect = 0
        count = 0

        for vital in baseline:
            if vital in predicted:
                baseline_val = baseline[vital]
                predicted_val = predicted[vital]

                if baseline_val != 0:
                    change = abs(predicted_val - baseline_val) / baseline_val
                    total_effect += change
                    count += 1

        if count == 0:
            return 0.0

        # 转换为0-100的分数
        effectiveness = (total_effect / count) * 100
        return min(round(effectiveness, 1), 100)

    def _assess_risk(
        self, intervention_type: InterventionType, predicted_values: Dict, disease: str
    ) -> str:
        """评估风险等级"""
        # 基于干预类型和预测值评估风险
        if intervention_type == InterventionType.MEDICATION:
            return "medium"

        # 检查是否有异常值
        for vital, value in predicted_values.items():
            if disease == "diabetes":
                if vital == "血糖" and (value < 3.9 or value > 16.7):
                    return "high"
            elif disease == "hypertension":
                if "压" in vital and (value < 90 or value > 180):
                    return "high"

        return "low"

    def _generate_recommendations(
        self, intervention_type: InterventionType, predicted_values: Dict, disease: str
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if intervention_type == InterventionType.DIET:
            recommendations.extend(
                ["坚持低糖低脂饮食", "控制每日碳水化合物摄入", "增加膳食纤维摄入"]
            )
        elif intervention_type == InterventionType.EXERCISE:
            recommendations.extend(
                ["每周至少150分钟中等强度运动", "运动前后监测血糖/血压", "避免空腹运动"]
            )
        elif intervention_type == InterventionType.MEDICATION:
            recommendations.extend(["遵医嘱按时服药", "定期监测血糖/血压", "注意药物副作用"])

        # 基于预测值的建议
        if disease == "diabetes":
            if "血糖" in predicted_values:
                recommendations.append(f"预计血糖可降至{predicted_values['血糖']}mmol/L")
        elif disease == "hypertension":
            if "收缩压" in predicted_values:
                recommendations.append(f"预计收缩压可降至{predicted_values['收缩压']}mmHg")

        return recommendations

    def _get_intervention_name(self, intervention_type: InterventionType) -> str:
        """获取干预名称"""
        names = {
            InterventionType.DIET: "饮食干预方案",
            InterventionType.EXERCISE: "运动干预方案",
            InterventionType.MEDICATION: "药物调整方案",
            InterventionType.LIFESTYLE: "生活方式干预方案",
            InterventionType.COMBINED: "综合干预方案",
        }
        return names.get(intervention_type, "干预方案")

    def _get_intervention_description(self, intervention_type: InterventionType) -> str:
        """获取干预描述"""
        descriptions = {
            InterventionType.DIET: "通过调整饮食结构，控制热量和营养素摄入",
            InterventionType.EXERCISE: "通过规律运动，提高身体代谢水平",
            InterventionType.MEDICATION: "通过药物调整，控制疾病指标",
            InterventionType.LIFESTYLE: "通过改善生活习惯，促进健康",
            InterventionType.COMBINED: "多维度综合干预，全方位改善健康状态",
        }
        return descriptions.get(intervention_type, "")


class SimulatorManager:
    """模拟器管理器"""

    def __init__(self):
        self.simulator = InterventionSimulator()
        self.recommender = None

    def _get_recommender(self):
        """获取建议生成器（懒加载）"""
        if self.recommender is None:
            try:
                from app.services.intervention_recommender import get_recommender

                self.recommender = get_recommender()
            except Exception as e:
                import logging

                logging.warning(f"Failed to load recommender: {e}")
                return None
        return self.recommender

    async def run_simulation(
        self, patient_data: Dict, intervention_type: InterventionType = InterventionType.COMBINED
    ) -> Dict:
        """
        运行模拟

        Args:
            patient_data: 患者数据
            intervention_type: 干预类型
        """
        print(f"[DEBUG] run_simulation called: patient_data={patient_data}, intervention_type={intervention_type}")
        
        # 构建干预方案
        interventions = self._build_interventions(patient_data, intervention_type)
        print(f"[DEBUG] interventions built: {[i.type.value for i in interventions]}")

        # 执行模拟
        result = await self.simulator.simulate(patient_data, interventions)
        print(f"[DEBUG] simulate result: predicted_values={result.predicted_values}")

        # 生成个性化建议（LLM）
        recommendations = result.recommendations
        recommender = self._get_recommender()
        if recommender and result.predicted_values:
            try:
                int_type = (
                    intervention_type.value
                    if hasattr(intervention_type, "value")
                    else str(intervention_type)
                )
                llm_recommendations = await recommender.generate_recommendations(
                    patient_name=patient_data.get("patient_name", "患者"),
                    age=patient_data.get("age", 0),
                    disease=patient_data.get("disease", "diabetes"),
                    baseline=result.baseline_values,
                    predicted=result.predicted_values,
                    intervention_type=int_type,
                    intervention_name=result.intervention.name,
                )
                if llm_recommendations:
                    recommendations = llm_recommendations
            except Exception as e:
                import logging

                logging.warning(f"Failed to generate LLM recommendations: {e}")

        # 转换为字典
        return {
            "intervention": {
                "type": result.intervention.type.value,
                "name": result.intervention.name,
                "description": result.intervention.description,
                "duration_days": result.intervention.duration_days,
            },
            "status": result.status.value,
            "baseline": result.baseline_values,
            "predicted": result.predicted_values,
            "timeline": result.timeline,
            "effectiveness": result.effectiveness,
            "risk_level": result.risk_level,
            "recommendations": recommendations,
        }

    def _build_interventions(
        self, patient_data: Dict, intervention_type: InterventionType
    ) -> List[Intervention]:
        """构建干预方案"""
        interventions = []

        if intervention_type == InterventionType.DIET:
            interventions.append(
                Intervention(
                    type=InterventionType.DIET,
                    name="饮食控制",
                    description="调整饮食结构",
                    duration_days=30,
                    parameters={"calorie_limit": 1800, "carb_ratio": 0.5},
                )
            )
        elif intervention_type == InterventionType.EXERCISE:
            interventions.append(
                Intervention(
                    type=InterventionType.EXERCISE,
                    name="规律运动",
                    description="每周运动150分钟",
                    duration_days=30,
                    parameters={"weekly_minutes": 150, "intensity": "moderate"},
                )
            )
        elif intervention_type == InterventionType.MEDICATION:
            interventions.append(
                Intervention(
                    type=InterventionType.MEDICATION,
                    name="药物调整",
                    description="遵医嘱调整用药",
                    duration_days=14,
                    parameters={"adjustment": "pending"},
                )
            )
        elif intervention_type == InterventionType.COMBINED:
            interventions.extend(
                [
                    Intervention(
                        type=InterventionType.DIET,
                        name="饮食控制",
                        description="调整饮食结构",
                        duration_days=30,
                        parameters={},
                    ),
                    Intervention(
                        type=InterventionType.EXERCISE,
                        name="规律运动",
                        description="每周运动150分钟",
                        duration_days=30,
                        parameters={},
                    ),
                ]
            )

        return interventions

    async def compare_interventions(self, patient_data: Dict) -> List[Dict]:
        """对比不同干预方案"""
        results = []

        for itype in InterventionType:
            if itype == InterventionType.LIFESTYLE:
                continue
            result = await self.run_simulation(patient_data, itype)
            results.append(result)

        # 按有效性排序
        results.sort(key=lambda x: x.get("effectiveness", 0), reverse=True)

        return results


# 全局单例
simulator_manager = SimulatorManager()
