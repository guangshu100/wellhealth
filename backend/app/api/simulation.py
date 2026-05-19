"""
干预效果模拟API
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.intervention_simulator import (
    simulator_manager,
    InterventionType,
    InterventionSimulator,
)

router = APIRouter()


class SimulationRequest(BaseModel):
    """模拟请求"""

    patient_id: str
    patient_name: Optional[str] = None
    age: Optional[int] = None
    disease: str
    current_vitals: Dict[str, float]
    intervention_type: str = "combined"
    history: Optional[List[Dict]] = None


class CompareRequest(BaseModel):
    """对比请求"""

    patient_id: str
    patient_name: Optional[str] = None
    age: Optional[int] = None
    disease: str
    current_vitals: Dict[str, float]


@router.post("/run")
async def run_simulation(request: SimulationRequest):
    """
    运行干预效果模拟
    """
    try:
        # 转换干预类型
        intervention_type = InterventionType(request.intervention_type)

        # 构建患者数据
        patient_data = {
            "patient_id": request.patient_id,
            "patient_name": request.patient_name or "患者",
            "age": request.age or 0,
            "disease": request.disease,
            "current_vitals": request.current_vitals,
            "history": request.history or [],
        }

        # 运行模拟
        result = await simulator_manager.run_simulation(
            patient_data=patient_data, intervention_type=intervention_type
        )

        return {"success": True, "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_interventions(request: CompareRequest):
    """
    对比不同干预方案
    """
    try:
        patient_data = {
            "patient_id": request.patient_id,
            "patient_name": request.patient_name or "患者",
            "age": request.age or 0,
            "disease": request.disease,
            "current_vitals": request.current_vitals,
            "history": [],
        }

        results = await simulator_manager.compare_interventions(patient_data)

        return {"success": True, "results": results, "best_option": results[0] if results else None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervention-types")
async def get_intervention_types():
    """
    获取可用的干预类型
    """
    return {
        "types": [
            {"value": it.value, "name": it.name.lower().replace("_", " ").title()}
            for it in InterventionType
        ]
    }


@router.get("/effectiveness/{disease}")
async def get_effectiveness_info(disease: str):
    """
    获取疾病干预效果信息
    """
    info = {
        "diabetes": {
            "name": "糖尿病",
            "vitals": ["血糖", "HbA1c"],
            "interventions": {
                "diet": {"effect_range": "10-20%", "time_range": "2-4周"},
                "exercise": {"effect_range": "8-15%", "time_range": "2-4周"},
                "medication": {"effect_range": "20-30%", "time_range": "1-2周"},
                "combined": {"effect_range": "30-40%", "time_range": "4-8周"},
            },
        },
        "hypertension": {
            "name": "高血压",
            "vitals": ["收缩压", "舒张压"],
            "interventions": {
                "diet": {"effect_range": "5-10 mmHg", "time_range": "2-4周"},
                "exercise": {"effect_range": "4-8 mmHg", "time_range": "4-6周"},
                "medication": {"effect_range": "10-15 mmHg", "time_range": "1-2周"},
                "combined": {"effect_range": "12-20 mmHg", "time_range": "4-8周"},
            },
        },
    }

    return info.get(disease, {"error": "Unknown disease"})


@router.get("/interventions")
async def get_interventions(disease: Optional[str] = None):
    """
    获取干预方案列表（带详细信息）
    """
    from app.utils.database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        if disease:
            # 映射疾病名称
            disease_map = {"diabetes": "2型糖尿病", "hypertension": "高血压"}
            disease_cn = disease_map.get(disease, disease)
            result = db.execute(
                text("""
                    SELECT id, name, type, target_disease, description, 
                           duration_days, effectiveness, risk_level
                    FROM interventions 
                    WHERE status = 'active' AND target_disease = :disease
                """),
                {"disease": disease_cn},
            )
        else:
            result = db.execute(
                text("""
                    SELECT id, name, type, target_disease, description, 
                           duration_days, effectiveness, risk_level
                    FROM interventions 
                    WHERE status = 'active'
                """)
            )

        rows = result.fetchall()
        interventions = []

        for row in rows:
            interventions.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "disease": row[3],
                    "description": row[4],
                    "duration_days": row[5],
                    "effectiveness": row[6],
                    "risk_level": row[7],
                    "steps": _get_intervention_steps(row[2]),  # 添加执行步骤
                    "precautions": _get_intervention_precautions(row[2]),  # 添加注意事项
                }
            )

        return {"interventions": interventions}
    finally:
        db.close()


def _get_intervention_steps(intervention_type: str) -> list:
    """获取干预方案执行步骤"""
    steps = {
        "diet": [
            "计算每日所需热量",
            "制定个性化食谱",
            "准备低GI食材",
            "记录每日饮食",
            "每周复盘调整",
        ],
        "exercise": [
            "进行体能评估",
            "制定运动计划",
            "选择合适运动项目",
            "循序渐进开始运动",
            "记录运动数据",
            "定期评估调整",
        ],
        "medication": ["遵医嘱用药", "按时服药", "观察药物效果", "记录不良反应", "定期复查"],
        "combined": [
            "综合评估身体状况",
            "制定综合干预计划",
            "执行饮食方案",
            "执行运动计划",
            "定期监测指标",
            "每月复盘调整",
        ],
    }
    return steps.get(intervention_type, ["按计划执行"])


def _get_intervention_precautions(intervention_type: str) -> list:
    """获取干预方案注意事项"""
    precautions = {
        "diet": ["避免极端节食", "注意营养均衡", "控制碳水化合物摄入", "定时定量用餐"],
        "exercise": ["运动前热身", "避免空腹运动", "注意运动强度", "如有不适停止运动"],
        "medication": ["遵医嘱用药", "不要自行调整药量", "注意药物相互作用", "定期复查"],
        "combined": ["循序渐进", "坚持规律", "定期监测", "如有不适及时就医"],
    }
    return precautions.get(intervention_type, ["遵医嘱执行"])
