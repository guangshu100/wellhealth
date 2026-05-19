"""
卡路里跟踪API
食物识别、营养计算、饮食记录
"""

import uuid
import json
import logging
import re
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException
from fastapi import Form
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["卡路里跟踪"])

# 常见食物营养数据（100g）
FOOD_NUTRITION_DB = {
    "米饭": {"calories": 130, "protein": 2.6, "carbs": 28, "fat": 0.3, "fiber": 0.4},
    "面条": {"calories": 138, "protein": 4.5, "carbs": 25, "fat": 1.1, "fiber": 1.2},
    "馒头": {"calories": 223, "protein": 7.8, "carbs": 47, "fat": 1.0, "fiber": 1.5},
    "面包": {"calories": 265, "protein": 8.0, "carbs": 49, "fat": 3.2, "fiber": 2.7},
    "饺子": {"calories": 253, "protein": 8.1, "carbs": 28, "fat": 11, "fiber": 1.3},
    "炒饭": {"calories": 163, "protein": 4.4, "carbs": 24, "fat": 5.9, "fiber": 0.5},
    "炒面": {"calories": 172, "protein": 5.4, "carbs": 22, "fat": 7.2, "fiber": 1.8},
    "炒菜": {"calories": 89, "protein": 2.1, "carbs": 8, "fat": 5.2, "fiber": 2.3},
    "红烧肉": {"calories": 358, "protein": 18, "carbs": 6, "fat": 30, "fiber": 0.2},
    "糖醋排骨": {"calories": 295, "protein": 16, "carbs": 15, "fat": 19, "fiber": 0.3},
    "宫保鸡丁": {"calories": 195, "protein": 16, "carbs": 6, "fat": 12, "fiber": 1.5},
    "麻婆豆腐": {"calories": 168, "protein": 8.2, "carbs": 5, "fat": 13, "fiber": 0.8},
    "番茄炒蛋": {"calories": 92, "protein": 5.4, "carbs": 3.2, "fat": 6.2, "fiber": 0.5},
    "青椒肉丝": {"calories": 135, "protein": 9.8, "carbs": 6.5, "fat": 8.1, "fiber": 1.2},
    "酸辣土豆丝": {"calories": 95, "protein": 1.8, "carbs": 18, "fat": 1.5, "fiber": 1.4},
    "西蓝花": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6},
    "菠菜": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2},
    "胡萝卜": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8},
    "土豆": {"calories": 77, "protein": 2.0, "carbs": 17, "fat": 0.1, "fiber": 2.2},
    "苹果": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
    "香蕉": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6},
    "橙子": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "fiber": 2.4},
    "葡萄": {"calories": 69, "protein": 0.7, "carbs": 18, "fat": 0.2, "fiber": 0.9},
    "西瓜": {"calories": 30, "protein": 0.6, "carbs": 8, "fat": 0.2, "fiber": 0.4},
    "草莓": {"calories": 32, "protein": 0.7, "carbs": 8, "fat": 0.3, "fiber": 2.0},
    "鸡蛋": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
    "鸡胸肉": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
    "鸡腿": {"calories": 209, "protein": 26, "carbs": 0, "fat": 11, "fiber": 0},
    "牛肉": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0},
    "猪肉": {"calories": 395, "protein": 14, "carbs": 0, "fat": 37, "fiber": 0},
    "鱼肉": {"calories": 113, "protein": 22, "carbs": 0, "fat": 3.0, "fiber": 0},
    "虾": {"calories": 99, "protein": 24, "carbs": 0.2, "fat": 0.3, "fiber": 0},
    "牛奶": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0},
    "酸奶": {"calories": 72, "protein": 2.5, "carbs": 9, "fat": 2.7, "fiber": 0},
    "豆浆": {"calories": 33, "protein": 3.3, "carbs": 1.2, "fat": 1.7, "fiber": 0.5},
    "豆腐": {"calories": 76, "protein": 8.1, "carbs": 1.9, "fat": 4.2, "fiber": 0.3},
    "包子": {"calories": 223, "protein": 7.8, "carbs": 28, "fat": 9, "fiber": 1.5},
    "煎饼": {"calories": 197, "protein": 4.4, "carbs": 26, "fat": 9, "fiber": 1.2},
    "油条": {"calories": 388, "protein": 6.4, "carbs": 31, "fat": 28, "fiber": 1.1},
    "小米粥": {"calories": 46, "protein": 1.4, "carbs": 9, "fat": 0.7, "fiber": 0.8},
    "燕麦": {"calories": 389, "protein": 16.9, "carbs": 66, "fat": 6.9, "fiber": 10.6},
    "玉米": {"calories": 96, "protein": 3.3, "carbs": 20, "fat": 1.4, "fiber": 2.7},
    "红薯": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3.0},
}


class MealType(str, Enum):
    """餐次类型"""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class FoodRecordCreate(BaseModel):
    """食物记录创建请求"""

    patient_id: str
    food_name: str
    calories: float
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    serving_size: float = 100
    meal_type: MealType = MealType.LUNCH
    record_date: Optional[str] = None


class FoodAnalyzeRequest(BaseModel):
    """食物分析请求"""

    patient_id: Optional[str] = None
    food_description: Optional[str] = None


# 模拟数据库
food_records: Dict[str, List[Dict]] = {}


@router.post("/analyze")
async def analyze_food(request: FoodAnalyzeRequest):
    """
    根据食物描述分析营养成分
    """
    try:
        food_desc = request.food_description or ""

        if not food_desc:
            return {
                "success": False,
                "message": "请输入食物描述",
                "foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
            }

        # 匹配营养数据库
        name_list = []
        food_desc_lower = food_desc.lower()

        # 简单匹配：查找已知食物
        for known_food in FOOD_NUTRITION_DB.keys():
            if known_food in food_desc:
                name_list.append(known_food)

        # 如果无法匹配，返回建议
        if not name_list:
            return {
                "success": False,
                "message": "未找到匹配食物，请手动输入",
                "foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
                "suggestions": list(FOOD_NUTRITION_DB.keys())[:10],
            }

        # 计算营养成分
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_fiber = 0

        detected_foods = []
        for name in name_list[:5]:
            nutrition = FOOD_NUTRITION_DB.get(
                name, {"calories": 100, "protein": 3, "carbs": 15, "fat": 2, "fiber": 1}
            )
            serving = 100
            total_calories += nutrition["calories"] * serving / 100
            total_protein += nutrition["protein"] * serving / 100
            total_carbs += nutrition["carbs"] * serving / 100
            total_fat += nutrition["fat"] * serving / 100
            total_fiber += nutrition["fiber"] * serving / 100
            detected_foods.append(
                {
                    "name": name,
                    "serving_size": serving,
                    "calories": round(nutrition["calories"] * serving / 100, 1),
                    "protein": round(nutrition["protein"] * serving / 100, 1),
                    "carbs": round(nutrition["carbs"] * serving / 100, 1),
                    "fat": round(nutrition["fat"] * serving / 100, 1),
                }
            )

        return {
            "success": True,
            "foods": detected_foods,
            "nutrition": {
                "calories": round(total_calories, 1),
                "protein": round(total_protein, 1),
                "carbs": round(total_carbs, 1),
                "fat": round(total_fat, 1),
                "fiber": round(total_fiber, 1),
            },
            "confidence": 0.85,
            "message": f"识别到 {len(detected_foods)} 种食物",
        }

    except Exception as e:
        logger.error(f"食物分析失败: {e}")
        return {
            "success": False,
            "message": f"分析失败: {str(e)}",
            "foods": [],
            "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
        }


FOOD_VISION_PROMPT = """你是一个专业的营养师。请分析这张食物图片：

1. 识别出所有食物项目（中文名称）
2. 估计每种食物的份量（克）
3. 请严格按照以下JSON格式返回，不要有任何额外内容：
```json
{
  "foods": [
    {"name": "食物名称", "serving": 估计的重量(数字), "calories": 热量(数字), "protein": 蛋白质(数字), "carbs": 碳水(数字), "fat": 脂肪(数字), "fiber": 纤维(数字)},
  ]
}
```
注意：
- 只返回JSON，不要有任何解释或额外文字
- 如果无法识别食物，返回 {"foods": []}
- serving 必须是数字（单位：克）
- 所有营养数值必须是数字"""


def parse_vision_response(response: str) -> List[Dict]:
    """解析Vision API返回的食物列表"""
    try:
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            return []

        data = json.loads(json_match.group())
        foods = data.get("foods", [])

        validated_foods = []
        for food in foods:
            if not isinstance(food.get("serving"), (int, float)):
                continue
            validated_foods.append(
                {
                    "name": food.get("name", ""),
                    "serving": int(food.get("serving", 100)),
                    "calories": float(food.get("calories", 0)),
                    "protein": float(food.get("protein", 0)),
                    "carbs": float(food.get("carbs", 0)),
                    "fat": float(food.get("fat", 0)),
                    "fiber": float(food.get("fiber", 0)),
                }
            )
        return validated_foods
    except Exception as e:
        logger.error(f"解析Vision响应失败: {e}, response: {response}")
        return []


@router.post("/analyze-image")
async def analyze_food_image(image: str = Form(...), patient_id: Optional[str] = Form(None)):
    """
    根据食物图片分析营养成分（使用AI Vision）
    """
    try:
        if not image:
            return {
                "success": False,
                "message": "请上传食物图片",
                "foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
            }

        llm = get_llm_client()

        logger.info("开始AI图像分析...")
        ai_response = await llm.chat_with_image(
            image_base64=image, prompt=FOOD_VISION_PROMPT, temperature=0.3, max_tokens=1000
        )

        if not ai_response or "暂时不可用" in ai_response:
            return {
                "success": False,
                "message": ai_response or "AI服务暂时不可用",
                "foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
            }

        foods = parse_vision_response(ai_response)

        if not foods:
            return {
                "success": False,
                "message": "无法识别图片中的食物，请重试或尝试文字描述",
                "foods": [],
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
            }

        total_calories = sum(f["calories"] for f in foods)
        total_protein = sum(f["protein"] for f in foods)
        total_carbs = sum(f["carbs"] for f in foods)
        total_fat = sum(f["fat"] for f in foods)
        total_fiber = sum(f["fiber"] for f in foods)

        return {
            "success": True,
            "foods": foods,
            "nutrition": {
                "calories": round(total_calories, 1),
                "protein": round(total_protein, 1),
                "carbs": round(total_carbs, 1),
                "fat": round(total_fat, 1),
                "fiber": round(total_fiber, 1),
            },
            "total_calories": round(total_calories, 1),
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "total_fat": round(total_fat, 1),
            "total_fiber": round(total_fiber, 1),
            "message": f"识别到 {len(foods)} 种食物",
            "ai_raw_response": ai_response[:200] if len(ai_response) > 200 else ai_response,
        }

    except Exception as e:
        logger.error(f"食物图片分析失败: {e}")
        return {
            "success": False,
            "message": f"分析失败: {str(e)}",
            "foods": [],
            "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
        }


@router.post("/record")
async def add_food_record(record: FoodRecordCreate):
    """添加食物记录"""
    try:
        record_id = f"food_{uuid.uuid4().hex[:12]}"
        record_date = record.record_date or datetime.now().strftime("%Y-%m-%d")

        if record.patient_id not in food_records:
            food_records[record.patient_id] = []

        food_record = {
            "id": record_id,
            "patient_id": record.patient_id,
            "food_name": record.food_name,
            "calories": record.calories,
            "protein": record.protein,
            "carbs": record.carbs,
            "fat": record.fat,
            "fiber": record.fiber,
            "serving_size": record.serving_size,
            "meal_type": record.meal_type.value,
            "record_date": record_date,
            "created_at": datetime.now().isoformat(),
        }

        food_records[record.patient_id].append(food_record)

        return {"success": True, "record_id": record_id, "message": "食物记录已添加"}

    except Exception as e:
        logger.error(f"添加食物记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{patient_id}")
async def get_food_records(patient_id: str, record_date: Optional[str] = None):
    """获取食物记录"""
    try:
        records = food_records.get(patient_id, [])

        if record_date:
            records = [r for r in records if r["record_date"] == record_date]

        grouped = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}

        for r in records:
            meal = r.get("meal_type", "lunch")
            if meal in grouped:
                grouped[meal].append(r)

        nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        for r in records:
            nutrition["calories"] += r.get("calories", 0)
            nutrition["protein"] += r.get("protein", 0)
            nutrition["carbs"] += r.get("carbs", 0)
            nutrition["fat"] += r.get("fat", 0)
            nutrition["fiber"] += r.get("fiber", 0)

        return {
            "success": True,
            "records": records,
            "grouped": grouped,
            "nutrition": nutrition,
            "total_meals": len(records),
        }

    except Exception as e:
        logger.error(f"获取食物记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{patient_id}")
async def get_nutrition_summary(patient_id: str, days: int = 7):
    """获取营养摘要（最近N天）"""
    try:
        from datetime import timedelta

        records = food_records.get(patient_id, [])
        target_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        recent_records = [r for r in records if r.get("record_date", "") >= target_date]

        daily_stats = {}
        for r in recent_records:
            date_key = r.get("record_date", "")
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0,
                    "fiber": 0,
                    "meals": 0,
                }

            daily_stats[date_key]["calories"] += r.get("calories", 0)
            daily_stats[date_key]["protein"] += r.get("protein", 0)
            daily_stats[date_key]["carbs"] += r.get("carbs", 0)
            daily_stats[date_key]["fat"] += r.get("fat", 0)
            daily_stats[date_key]["fiber"] += r.get("fiber", 0)
            daily_stats[date_key]["meals"] += 1

        days_count = len(daily_stats) or 1
        avg_nutrition = {
            "calories": round(sum(d["calories"] for d in daily_stats.values()) / days_count, 1),
            "protein": round(sum(d["protein"] for d in daily_stats.values()) / days_count, 1),
            "carbs": round(sum(d["carbs"] for d in daily_stats.values()) / days_count, 1),
            "fat": round(sum(d["fat"] for d in daily_stats.values()) / days_count, 1),
            "fiber": round(sum(d["fiber"] for d in daily_stats.values()) / days_count, 1),
        }

        targets = {"calories": 2000, "protein": 60, "carbs": 300, "fat": 65, "fiber": 25}

        return {
            "success": True,
            "period_days": days,
            "total_records": len(recent_records),
            "daily_stats": daily_stats,
            "average": avg_nutrition,
            "targets": targets,
            "achievement": {
                k: round(v / targets[k] * 100, 1) for k, v in avg_nutrition.items() if k in targets
            },
        }

    except Exception as e:
        logger.error(f"获取营养摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/record/{record_id}")
async def delete_food_record(patient_id: str, record_id: str):
    """删除食物记录"""
    try:
        records = food_records.get(patient_id, [])
        food_records[patient_id] = [r for r in records if r["id"] != record_id]

        return {"success": True, "message": "记录已删除"}

    except Exception as e:
        logger.error(f"删除食物记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
