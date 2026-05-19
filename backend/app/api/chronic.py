"""
深度慢病管理API
包含：食物GI/GL查询、碳水计算、血糖分析、食谱推荐
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from app.services.chronic_disease_manager import (
    food_database,
    carb_calculator,
    glucose_analyzer,
    recipe_generator,
    MealType,
    GlucoseLevel,
)

router = APIRouter()


# ========== 食物数据库API ==========


class FoodSearchRequest(BaseModel):
    keyword: str


class FoodSearchResponse(BaseModel):
    foods: List[Dict]
    total: int


@router.get("/food/search")
async def search_food(keyword: str = Query(..., description="搜索关键词")):
    """搜索食物"""
    results = food_database.search(keyword)
    return {"foods": results, "total": len(results)}


@router.get("/food/category/{category}")
async def get_foods_by_category(category: str):
    """按类别获取食物"""
    results = food_database.get_by_category(category)
    return {"category": category, "foods": results, "total": len(results)}


@router.get("/food/low-gi")
async def get_low_gi_foods(limit: int = Query(20, description="返回数量")):
    """获取低GI食物"""
    results = food_database.get_low_gi_foods(limit)
    return {"foods": results, "total": len(results)}


@router.get("/food/categories")
async def get_food_categories():
    """获取食物分类列表"""
    categories = ["主食", "蔬菜", "水果", "奶类", "坚果", "豆类", "蛋白质", "饮料", "甜点", "点心"]
    return {"categories": categories}


@router.get("/food/{food_name}")
async def get_food_detail(food_name: str):
    """获取食物详细信息"""
    foods = food_database.search(food_name)
    if not foods:
        raise HTTPException(status_code=404, detail="食物不存在")
    return foods[0]


# ========== 碳水化合物计算API ==========


class FoodItemInput(BaseModel):
    name: str
    weight: float  # 克


class MealCarbsRequest(BaseModel):
    foods: List[FoodItemInput]


@router.post("/carbs/meal")
async def calculate_meal_carbs(request: MealCarbsRequest):
    """计算餐食碳水化合物"""
    foods_data = [f.dict() for f in request.foods]
    result = carb_calculator.calculate_meal_carbs(foods_data)
    return result


class DailyRequirementRequest(BaseModel):
    weight: float
    activity_level: str = "moderate"  # sedentary, light, moderate, active, very_active


@router.post("/carbs/daily-requirement")
async def calculate_daily_carbs(request: DailyRequirementRequest):
    """计算每日碳水化合物需求"""
    result = carb_calculator.calculate_daily_requirement(request.weight, request.activity_level)
    return result


class InsulinRatioRequest(BaseModel):
    total_daily_insulin: float
    activity_level: str = "moderate"


@router.post("/carbs/insulin-ratio")
async def calculate_icr(request: InsulinRatioRequest):
    """计算胰岛素碳水比(ICR)"""
    result = carb_calculator.calculate_insulin_to_carb_ratio(
        request.total_daily_insulin, request.activity_level
    )
    return result


class CorrectionFactorRequest(BaseModel):
    total_daily_insulin: float


@router.post("/carbs/correction-factor")
async def calculate_isf(request: CorrectionFactorRequest):
    """计算胰岛素敏感因子(ISF)"""
    result = carb_calculator.calculate_correction_factor(request.total_daily_insulin)
    return result


class MealInsulinRequest(BaseModel):
    pre_meal_glucose: float
    target_glucose: float
    total_carbs: float
    icr: float
    isf: float


@router.post("/carbs/meal-insulin")
async def calculate_meal_insulin(request: MealInsulinRequest):
    """计算餐时胰岛素剂量"""
    result = carb_calculator.calculate_meal_insulin(
        request.pre_meal_glucose,
        request.target_glucose,
        request.total_carbs,
        request.icr,
        request.isf,
    )
    return result


# ========== 血糖分析API ==========


class GlucoseDataPoint(BaseModel):
    time: str
    value: float  # mmol/L
    type: Optional[str] = "fasting"  # fasting, postprandial, random


class GlucoseTrendRequest(BaseModel):
    glucose_data: List[GlucoseDataPoint]


@router.post("/glucose/trend")
async def analyze_glucose_trend(request: GlucoseTrendRequest):
    """分析血糖趋势"""
    data = [d.dict() for d in request.glucose_data]
    result = glucose_analyzer.analyze_trend(data)
    return result


@router.post("/glucose/patterns")
async def detect_glucose_patterns(request: GlucoseTrendRequest):
    """检测血糖模式"""
    data = [d.dict() for d in request.glucose_data]
    result = glucose_analyzer.detect_patterns(data)
    return result


# ========== 食谱推荐API ==========


class PatientInfo(BaseModel):
    weight: float
    activity: str = "moderate"  # sedentary, light, moderate, active, very_active
    prefer_foods: Optional[List[str]] = []


class MealPlanRequest(BaseModel):
    patient_info: PatientInfo
    meal_type: str  # breakfast, lunch, dinner, snack
    target_carbs: float


@router.post("/recipe/meal")
async def generate_meal_plan(request: MealPlanRequest):
    """生成餐食计划"""
    result = recipe_generator.generate_meal_plan(
        request.patient_info.dict(), request.meal_type, request.target_carbs
    )
    return {
        "meal_type": result.meal_type,
        "foods": result.foods,
        "total_carbs": result.total_carbs,
        "total_calories": result.total_calories,
        "gi": result.gi,
        "gl": result.gl,
        "recommendation": result.recommendation,
    }


class DailyPlanRequest(BaseModel):
    patient_info: PatientInfo


@router.post("/recipe/daily")
async def generate_daily_plan(request: DailyPlanRequest):
    """生成每日食谱"""
    result = recipe_generator.generate_daily_plan(request.patient_info.dict())
    return result


# ========== 综合健康建议API ==========


@router.get("/health/tips")
async def get_health_tips():
    """获取糖尿病健康建议"""
    tips = [
        {
            "category": "饮食",
            "tips": [
                "控制每日总热量，保持合理体重",
                "选择低GI、低GL食物",
                "粗细搭配，增加膳食纤维摄入",
                "少盐少油，戒烟限酒",
                "规律进餐，避免暴饮暴食",
            ],
        },
        {
            "category": "运动",
            "tips": [
                "每周至少150分钟中等强度运动",
                "餐后30-60分钟适度运动",
                "运动前后监测血糖",
                "避免空腹运动",
            ],
        },
        {
            "category": "监测",
            "tips": [
                "定期监测空腹和餐后血糖",
                "每3个月检测HbA1c",
                "关注血糖波动趋势",
                "记录每日饮食和运动",
            ],
        },
        {
            "category": "用药",
            "tips": [
                "按时按量服用降糖药物",
                "了解药物副作用",
                "不随意调整用药方案",
                "定期复查肝肾功能",
            ],
        },
    ]
    return {"tips": tips}


@router.get("/glucose/target-ranges")
async def get_glucose_targets():
    """获取血糖控制目标"""
    return {
        "targets": {
            "fasting": {"min": 4.4, "max": 7.0, "unit": "mmol/L"},
            "postprandial": {"min": 4.4, "max": 10.0, "unit": "mmol/L"},
            "bedtime": {"min": 6.0, "max": 8.0, "unit": "mmol/L"},
            "hba1c": {"min": None, "max": 7.0, "unit": "%"},
        },
        "remarks": {
            "general": "一般成人2型糖尿病患者血糖控制目标",
            "elderly": "老年患者可适当放宽目标",
            "pregnant": "妊娠期糖尿病控制更严格",
        },
    }


@router.get("/carbs/portion-guide")
async def get_portion_guide():
    """获取食物份量指南"""
    return {
        "guide": [
            {
                "food_type": "主食",
                "portion": "50-75g(生重)",
                "examples": "米饭(150g)、馒头(70g)、面条(75g)",
            },
            {"food_type": "蔬菜", "portion": "300-500g", "examples": "叶菜类、瓜茄类"},
            {"food_type": "水果", "portion": "200g以内", "examples": "苹果1个、橙子1个"},
            {"food_type": "蛋白质", "portion": "120-200g", "examples": "鸡蛋1个、瘦肉100g、鱼100g"},
            {"food_type": "奶类", "portion": "250ml", "examples": "牛奶、酸奶"},
            {"food_type": "油脂", "portion": "25-30g", "examples": "植物油"},
        ],
        "tips": "手掌法则：一个手掌大小的蛋白质、一个拳头的主食、一把蔬菜、一指尖的油脂",
    }
