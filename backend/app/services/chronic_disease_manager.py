"""
深度慢病管理服务
包含：碳水化合物计算、GI/GL食物库、血糖趋势分析、食谱推荐
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class MealType(str, Enum):
    """餐次类型"""
    BREAKFAST = "breakfast"      # 早餐
    LUNCH = "lunch"              # 午餐
    DINNER = "dinner"            # 晚餐
    SNACK = "snack"              # 零食


class GlucoseLevel(str, Enum):
    """血糖水平"""
    LOW = "low"          # 低血糖 <3.9
    NORMAL = "normal"    # 正常 3.9-6.1
    PREDIABETES = "prediabetes"  # 糖尿病前期 6.1-7.0
    DIABETES = "diabetes"  # 糖尿病 >7.0


@dataclass
class FoodItem:
    """食物项目"""
    name: str
    category: str
    gi: int           # 升糖指数
    carbs_per_100g: float  # 每100g碳水化合物(g)
    serving_size: float     # 常见份量(g)
    calories: int          # 热量(kcal)
    fiber: float = 0      # 膳食纤维
    protein: float = 0     # 蛋白质
    fat: float = 0        # 脂肪
    
    
@dataclass
class MealPlan:
    """餐食计划"""
    meal_type: str
    foods: List[Dict]
    total_carbs: float
    total_calories: int
    gi: float
    gl: float
    recommendation: str


def get_foods_from_db() -> List[Dict]:
    """从数据库获取食物数据"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT name, category, gi, carbs_per_100g, serving_size, 
                       COALESCE(fiber, 0) as fiber, 
                       COALESCE(protein, 0) as protein, COALESCE(fat, 0) as fat,
                       calories
                FROM food_database 
                ORDER BY category, name
            """))
            rows = result.fetchall()
            
            return [
                {
                    "name": row[0],
                    "category": row[1],
                    "gi": row[2],
                    "carbs_per_100g": float(row[3]),
                    "serving_size": float(row[4]),
                    "fiber": float(row[5]),
                    "protein": float(row[6]),
                    "fat": float(row[7]),
                    "calories": int(row[8])
                }
                for row in rows
            ]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to load foods from database: {e}")
        return []


class FoodDatabase:
    """
    GI/GL食物数据库
    从数据库加载食物数据，支持Fallback到内置数据
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FoodDatabase._initialized:
            self._foods: Dict[str, FoodItem] = {}
            self._db_loaded = False
            FoodDatabase._initialized = True
    
    def load_from_database(self) -> bool:
        """从数据库加载食物数据"""
        if self._db_loaded:
            return True
            
        try:
            foods_data = get_foods_from_db()
            if foods_data:
                for food in foods_data:
                    self._foods[food["name"]] = FoodItem(
                        name=food["name"],
                        category=food["category"],
                        gi=food["gi"],
                        carbs_per_100g=food["carbs_per_100g"],
                        serving_size=food["serving_size"],
                        calories=food["calories"],
                        fiber=food.get("fiber", 0),
                        protein=food.get("protein", 0),
                        fat=food.get("fat", 0)
                    )
                self._db_loaded = True
                logger.info(f"Loaded {len(self._foods)} foods from database")
                return True
        except Exception as e:
            logger.warning(f"Failed to load foods from database: {e}")
        
        return False
    
    def _ensure_loaded(self):
        """确保数据已加载（优先从数据库，失败则用内置数据）"""
        if not self._foods:
            if not self.load_from_database():
                self._init_database()
    
    def _init_database(self):
        """初始化食物数据库"""
        # 谷物类
        foods = [
            # 谷物 (GI值, 碳水/100g, 份量g, 热量)
            ("白米饭", "主食", 73, 28.2, 150, 174),
            ("糙米饭", "主食", 68, 23.5, 150, 152),
            ("黑米饭", "主食", 55, 23.0, 150, 151),
            ("燕麦片", "主食", 55, 12.0, 40, 150),
            ("燕麦粥", "主食", 55, 11.0, 250, 68),
            ("全麦面包", "主食", 50, 41.0, 30, 81),
            ("白面包", "主食", 75, 49.0, 30, 79),
            ("荞麦面", "主食", 59, 25.0, 150, 172),
            ("意面(白)", "主食", 49, 31.0, 180, 220),
            ("意面(全麦)", "主食", 48, 26.5, 180, 185),
            ("米粉", "主食", 61, 28.0, 150, 170),
            ("粉丝", "主食", 65, 26.0, 150, 150),
            ("挂面", "主食", 55, 28.0, 150, 170),
            ("馒头", "主食", 85, 47.0, 100, 223),
            ("花卷", "主食", 88, 45.6, 100, 215),
            ("烙饼", "主食", 80, 51.0, 100, 266),
            ("油条", "主食", 75, 50.0, 100, 316),
            ("包子(肉)", "主食", 70, 28.0, 100, 223),
            ("包子(素)", "主食", 70, 32.0, 100, 224),
            ("饺子(肉)", "主食", 70, 25.0, 100, 215),
            ("饺子(素)", "主食", 70, 28.0, 100, 225),
            
            # 蔬菜类
            ("土豆", "蔬菜", 62, 17.0, 100, 77),
            ("红薯", "蔬菜", 54, 20.0, 100, 86),
            ("南瓜", "蔬菜", 65, 5.0, 100, 26),
            ("山药", "蔬菜", 51, 12.0, 100, 56),
            ("芋头", "蔬菜", 48, 13.0, 100, 56),
            ("莲藕", "蔬菜", 38, 11.0, 100, 47),
            ("胡萝卜", "蔬菜", 39, 8.0, 100, 41),
            ("白萝卜", "蔬菜", 26, 4.0, 100, 20),
            ("番茄", "蔬菜", 15, 3.0, 100, 15),
            ("黄瓜", "蔬菜", 15, 2.0, 100, 12),
            ("茄子", "蔬菜", 15, 3.0, 100, 15),
            ("青椒", "蔬菜", 15, 4.0, 100, 18),
            ("西葫芦", "蔬菜", 15, 3.0, 100, 14),
            ("菠菜", "蔬菜", 15, 2.0, 100, 14),
            ("生菜", "蔬菜", 15, 2.0, 100, 12),
            ("白菜", "蔬菜", 15, 2.0, 100, 14),
            ("油菜", "蔬菜", 15, 2.0, 100, 14),
            ("西兰花", "蔬菜", 15, 3.0, 100, 24),
            ("菜花", "蔬菜", 15, 3.0, 100, 21),
            ("豆角", "蔬菜", 15, 4.0, 100, 20),
            
            # 水果类
            ("苹果", "水果", 36, 14.0, 200, 104),
            ("梨", "水果", 38, 13.0, 200, 100),
            ("桃", "水果", 42, 12.0, 200, 96),
            ("橙子", "水果", 43, 12.0, 200, 88),
            ("柚子", "水果", 25, 9.0, 200, 72),
            ("葡萄", "水果", 46, 17.0, 100, 69),
            ("葡萄柚", "水果", 25, 8.0, 200, 82),
            ("草莓", "水果", 40, 8.0, 150, 45),
            ("蓝莓", "水果", 53, 14.0, 100, 57),
            ("猕猴桃", "水果", 50, 14.0, 100, 61),
            ("菠萝", "水果", 66, 13.0, 100, 50),
            ("芒果", "水果", 51, 15.0, 100, 65),
            ("西瓜", "水果", 72, 6.0, 200, 60),
            ("哈密瓜", "水果", 70, 8.0, 200, 66),
            ("香蕉", "水果", 51, 23.0, 100, 89),
            ("火龙果", "水果", 50, 13.0, 100, 55),
            ("荔枝", "水果", 57, 16.0, 100, 70),
            ("龙眼", "水果", 53, 17.0, 100, 71),
            ("樱桃", "水果", 22, 10.0, 100, 63),
            ("杏", "水果", 57, 10.0, 100, 48),
            
            # 奶类
            ("牛奶", "奶类", 27, 5.0, 250, 135),
            ("酸奶", "奶类", 48, 12.0, 200, 118),
            ("低脂牛奶", "奶类", 26, 5.0, 250, 122),
            ("豆奶", "奶类", 34, 6.0, 250, 75),
            ("奶粉", "奶类", 31, 5.0, 30, 151),
            ("奶酪", "奶类", 31, 4.0, 30, 120),
            
            # 坚果类
            ("花生", "坚果", 14, 4.0, 30, 170),
            ("杏仁", "坚果", 15, 5.0, 30, 173),
            ("核桃", "坚果", 15, 4.0, 30, 185),
            ("腰果", "坚果", 25, 8.0, 30, 175),
            ("榛子", "坚果", 15, 5.0, 30, 179),
            ("开心果", "坚果", 15, 5.0, 30, 159),
            ("巴西坚果", "坚果", 10, 4.0, 30, 186),
            
            # 豆类
            ("黄豆", "豆类", 15, 6.0, 30, 51),
            ("黑豆", "豆类", 15, 8.0, 30, 55),
            ("红豆", "豆类", 26, 12.0, 30, 52),
            ("绿豆", "豆类", 27, 12.0, 30, 52),
            ("豆腐", "豆类", 15, 2.0, 100, 76),
            ("豆浆", "豆类", 34, 6.0, 250, 75),
            
            # 肉类/蛋白质
            ("鸡蛋", "蛋白质", 0, 1.0, 50, 78),
            ("鸡胸肉", "蛋白质", 0, 0, 100, 165),
            ("鱼肉", "蛋白质", 0, 0, 100, 113),
            ("虾", "蛋白质", 0, 1.0, 100, 99),
            ("牛肉", "蛋白质", 0, 0, 100, 250),
            ("猪肉", "蛋白质", 0, 0, 100, 143),
            
            # 饮料类
            ("可乐", "饮料", 60, 11.0, 330, 140),
            ("橙汁", "饮料", 50, 10.0, 250, 110),
            ("苹果汁", "饮料", 41, 11.0, 250, 114),
            ("奶茶", "饮料", 41, 10.0, 350, 266),
            
            # 甜点/零食
            ("冰淇淋", "甜点", 51, 24.0, 100, 207),
            ("巧克力", "甜点", 49, 60.0, 30, 170),
            ("饼干", "甜点", 72, 70.0, 30, 155),
            ("蛋糕", "甜点", 73, 58.0, 50, 224),
            ("蜂蜜", "甜点", 61, 75.0, 20, 64),
            ("白砂糖", "甜点", 65, 100.0, 10, 39),
            
            # 面点类
            ("汤圆", "点心", 87, 44.0, 100, 280),
            ("月饼", "点心", 52, 40.0, 100, 411),
            ("麻团", "点心", 75, 44.0, 100, 311),
            ("粽子", "点心", 87, 44.0, 100, 232),
        ]
        
        for name, category, gi, carbs, serving, calories in foods:
            self._foods[name] = FoodItem(
                name=name,
                category=category,
                gi=gi,
                carbs_per_100g=carbs,
                serving_size=serving,
                calories=calories
            )
    
    def search(self, keyword: str) -> List[Dict]:
        """搜索食物"""
        results = []
        keyword_lower = keyword.lower()
        for food in self._foods.values():
            if keyword_lower in food.name.lower():
                results.append(self._to_dict(food))
        return results[:20]
    
    def get_by_category(self, category: str) -> List[Dict]:
        """按类别获取食物"""
        results = []
        for food in self._foods.values():
            if food.category == category:
                results.append(self._to_dict(food))
        return results
    
    def get_low_gi_foods(self, limit: int = 20) -> List[Dict]:
        """获取低GI食物"""
        sorted_foods = sorted(self._foods.values(), key=lambda x: x.gi)
        return [self._to_dict(f) for f in sorted_foods[:limit]]
    
    def calculate_gl(self, gi: int, carbs: float) -> float:
        """计算GL = GI × 碳水 ÷ 100"""
        return round(gi * carbs / 100, 1)
    
    def _to_dict(self, food: FoodItem) -> Dict:
        return {
            "name": food.name,
            "category": food.category,
            "gi": food.gi,
            "carbs_per_100g": food.carbs_per_100g,
            "serving_size": food.serving_size,
            "calories": food.calories,
            "gl_per_serving": self.calculate_gl(food.gi, food.carbs_per_100g * food.serving_size / 100)
        }


class CarbohydrateCalculator:
    """
    碳水化合物计算器
    用于计算餐食中的碳水化合物含量
    """
    
    def __init__(self):
        self.food_db = food_database  # 使用全局实例
    
    def calculate_meal_carbs(self, foods: List[Dict]) -> Dict:
        """
        计算餐食碳水化合物
        输入: [{"name": "米饭", "weight": 150}, {"name": "鸡胸肉", "weight": 100}]
        """
        total_carbs = 0
        total_calories = 0
        result_foods = []
        
        for item in foods:
            food_name = item.get("name", "")
            weight = item.get("weight", 100)  # 默认100g
            
            # 查找食物
            found_food = self.food_db._foods.get(food_name)
            if found_food:
                # 按重量比例计算
                ratio = weight / 100
                carbs = found_food.carbs_per_100g * ratio
                calories = found_food.calories * ratio
                gi = found_food.gi
                gl = self.food_db.calculate_gl(gi, carbs)
                
                total_carbs += carbs
                total_calories += calories
                
                result_foods.append({
                    "name": food_name,
                    "weight": weight,
                    "carbs": round(carbs, 1),
                    "calories": round(calories, 0),
                    "gi": gi,
                    "gl": round(gl, 1)
                })
        
        return {
            "foods": result_foods,
            "total_carbs": round(total_carbs, 1),
            "total_calories": round(total_calories, 0),
            "gi": round(sum(f["gi"] for f in result_foods) / len(result_foods) if result_foods else 0, 0),
            "gl": round(sum(f["gl"] for f in result_foods), 1)
        }
    
    def calculate_daily_requirement(self, 
                                   weight: float, 
                                   activity_level: str = "moderate") -> Dict:
        """
        计算每日碳水化合物需求
        根据体重和活动水平
        """
        # 基础代谢率估算 (简单公式)
        bmr = weight * 24
        
        # 活动系数
        activity_multipliers = {
            "sedentary": 1.2,    # 久坐
            "light": 1.375,       # 轻度活动
            "moderate": 1.55,      # 中度活动
            "active": 1.725,      # 活跃
            "very_active": 2.0    # 非常活跃
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.55)
        tdee = bmr * multiplier
        
        # 碳水化合物供能占比45-60%
        carbs_calories_min = tdee * 0.45
        carbs_calories_max = tdee * 0.60
        
        # 碳水化合物克数 (1g碳水 = 4kcal)
        carbs_min = carbs_calories_min / 4
        carbs_max = carbs_calories_max / 4
        
        return {
            "weight": weight,
            "activity_level": activity_level,
            "estimated_calories": round(tdee),
            "carbs_grams_min": round(carbs_min),
            "carbs_grams_max": round(carbs_max),
            "carbs_grams_typical": round((carbs_min + carbs_max) / 2)
        }
    
    def calculate_insulin_to_carb_ratio(self, 
                                        total_daily_insulin: float,
                                        activity_level: str = "moderate") -> Dict:
        """
        计算胰岛素碳水比 (ICR)
        500法则: 500 / 总胰岛素日剂量 = 1U胰岛素覆盖的碳水克数
        """
        if total_daily_insulin <= 0:
            return {"error": "胰岛素剂量必须大于0"}
        
        # 基础ICR
        icr = 500 / total_daily_insulin
        
        # 根据活动水平调整
        activity_adjustments = {
            "sedentary": 1.0,
            "light": 0.85,
            "moderate": 0.75,
            "active": 0.65,
            "very_active": 0.5
        }
        
        adjustment = activity_adjustments.get(activity_level, 1.0)
        adjusted_icr = icr * adjustment
        
        return {
            "total_daily_insulin": total_daily_insulin,
            "basic_icr": round(icr, 1),
            "activity_level": activity_level,
            "adjusted_icr": round(adjusted_icr, 1),
            "description": f"1U胰岛素可覆盖 {round(adjusted_icr, 1)}g 碳水化合物"
        }
    
    def calculate_correction_factor(self, 
                                   total_daily_insulin: float) -> Dict:
        """
        计算胰岛素敏感因子 (ISF)
        1700法则: 1700 / 总胰岛素日剂量
        """
        if total_daily_insulin <= 0:
            return {"error": "胰岛素剂量必须大于0"}
        
        isf = 1700 / total_daily_insulin
        
        return {
            "total_daily_insulin": total_daily_insulin,
            "isf": round(isf, 1),
            "description": f"1U胰岛素可降低血糖 {round(isf, 1)} mmol/L"
        }
    
    def calculate_meal_insulin(self,
                             pre_meal_glucose: float,
                             target_glucose: float,
                             total_carbs: float,
                             icr: float,
                             isf: float) -> Dict:
        """
        计算餐时胰岛素剂量
        公式: 碳水剂量 + 校正剂量
        """
        # 碳水剂量
        carb_dose = total_carbs / icr if icr > 0 else 0
        
        # 校正剂量
        glucose_diff = pre_meal_glucose - target_glucose
        correction_dose = glucose_diff / isf if isf > 0 else 0
        
        # 总剂量
        total_dose = carb_dose + correction_dose
        
        return {
            "pre_meal_glucose": pre_meal_glucose,
            "target_glucose": target_glucose,
            "total_carbs": total_carbs,
            "carb_dose": round(carb_dose, 1),
            "correction_dose": round(correction_dose, 1),
            "total_dose": round(total_dose, 1),
            "recommendation": f"建议注射 {round(total_dose, 1)} 单位胰岛素"
        }


class BloodSugarAnalyzer:
    """
    血糖趋势分析器
    分析血糖数据趋势、波动、异常模式
    """
    
    def __init__(self):
        pass
    
    def analyze_trend(self, glucose_data: List[Dict]) -> Dict:
        """
        分析血糖趋势
        输入: [{"time": "2024-03-15 08:00", "value": 6.5, "type": "fasting"}]
        """
        if not glucose_data:
            return {"error": "无数据"}
        
        values = [d["value"] for d in glucose_data]
        times = [d["time"] for d in glucose_data]
        
        # 基本统计
        avg = sum(values) / len(values)
        max_val = max(values)
        min_val = min(values)
        
        # 趋势判断 (简单线性回归斜率)
        n = len(values)
        if n >= 2:
            # 简化: 比较前半和后半的平均值
            mid = n // 2
            first_half_avg = sum(values[:mid]) / mid if mid > 0 else values[0]
            second_half_avg = sum(values[mid:]) / (n - mid)
            slope = "rising" if second_half_avg > first_half_avg * 1.1 else "falling" if second_half_avg < first_half_avg * 0.9 else "stable"
        else:
            slope = "insufficient_data"
        
        # 波动性 (标准差)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        volatility = "high" if std_dev > 2.0 else "moderate" if std_dev > 1.0 else "low"
        
        # TIR (Time in Range) 时间范围内占比
        in_range = sum(1 for v in values if 3.9 <= v <= 10.0)
        tir = in_range / len(values) * 100 if values else 0
        
        # 异常检测
        anomalies = []
        for i, d in enumerate(glucose_data):
            if d["value"] < 3.9:
                anomalies.append({"time": d["time"], "value": d["value"], "type": "hypoglycemia"})
            elif d["value"] > 13.9:
                anomalies.append({"time": d["time"], "value": d["value"], "type": "severe_hyperglycemia"})
        
        return {
            "data_points": len(values),
            "average": round(avg, 1),
            "max": max_val,
            "min": min_val,
            "std_dev": round(std_dev, 1),
            "trend": slope,
            "volatility": volatility,
            "tir": round(tir, 1),
            "anomalies": anomalies,
            "recommendations": self._generate_recommendations(avg, tir, slope, volatility)
        }
    
    def detect_patterns(self, glucose_data: List[Dict]) -> Dict:
        """检测血糖模式"""
        patterns = []
        
        # 提取空腹血糖
        fasting = [d["value"] for d in glucose_data if d.get("type") == "fasting"]
        # 提取餐后血糖
        postprandial = [d["value"] for d in glucose_data if d.get("type") == "postprandial"]
        
        # 黎明现象: 空腹血糖持续升高
        if len(fasting) >= 3:
            if all(fasting[i] < fasting[i+1] for i in range(len(fasting)-1)):
                patterns.append({
                    "type": "dawn_phenomenon",
                    "description": "黎明现象: 空腹血糖持续升高",
                    "severity": "medium"
                })
        
        # 苏木杰效应: 夜间低血糖后空腹高血糖
        night_low = any(d["value"] < 3.9 for d in glucose_data if "night" in d.get("time", "").lower())
        if night_low and fasting and max(fasting) > 10:
            patterns.append({
                "type": "somogyi_effect",
                "description": "苏木杰效应: 夜间低血糖后反弹性高血糖",
                "severity": "high"
            })
        
        # 餐后血糖波动大
        if postprandial and len(postprandial) >= 2:
            variance = sum((x - sum(postprandial)/len(postprandial))**2 for x in postprandial) / len(postprandial)
            if variance ** 0.5 > 3:
                patterns.append({
                    "type": "postprandial_volatility",
                    "description": "餐后血糖波动较大",
                    "severity": "medium"
                })
        
        return {
            "patterns": patterns,
            "has_issues": len(patterns) > 0
        }
    
    def _generate_recommendations(self, avg: float, tir: float, trend: str, volatility: str) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if avg > 10:
            recommendations.append("血糖整体偏高，建议调整治疗方案")
        elif avg < 4:
            recommendations.append("血糖偏低，注意低血糖风险")
        
        if tir < 50:
            recommendations.append("时间范围内血糖占比不足50%，需加强控制")
        elif tir > 70:
            recommendations.append("血糖控制良好，继续保持")
        
        if trend == "rising":
            recommendations.append("血糖呈上升趋势，需关注")
        elif trend == "falling":
            recommendations.append("血糖呈下降趋势，注意预防低血糖")
        
        if volatility == "high":
            recommendations.append("血糖波动较大，建议减少高GI食物摄入")
        
        if not recommendations:
            recommendations.append("血糖控制稳定，请继续保持")
        
        return recommendations


class RecipeGenerator:
    """
    个性化食谱生成器
    根据患者情况生成糖尿病友好食谱
    """
    
    def __init__(self):
        self.food_db = food_database  # 使用全局实例
    
    def generate_meal_plan(self,
                          patient_info: Dict,
                          meal_type: str,
                          target_carbs: float) -> MealPlan:
        """
        生成餐食计划
        patient_info: {"weight": 70, "activity": "moderate", "prefer_foods": []}
        """
        # 根据目标碳水选择食物
        main_carbs = target_carbs * 0.5  # 主食占50%
        protein_carbs = target_carbs * 0.25  # 蛋白质配菜占25%
        vegetable_carbs = target_carbs * 0.25  # 蔬菜占25%
        
        # 选择低GI主食
        main_foods = self.food_db.get_low_gi_foods(10)
        main_foods = [f for f in main_foods if f["category"] == "主食"]
        
        # 选择蔬菜
        vegetables = self.food_db.get_by_category("蔬菜")[:10]
        
        # 选择蛋白质
        proteins = self.food_db.get_by_category("蛋白质")[:5]
        
        # 生成餐食
        foods = []
        total_carbs = 0
        
        # 添加主食 (假设150g)
        if main_foods:
            rice = main_foods[0]
            rice_weight = min(150, main_carbs / rice["carbs_per_100g"] * 100)
            foods.append({
                "name": rice["name"],
                "weight": round(rice_weight),
                "carbs": round(rice["carbs_per_100g"] * rice_weight / 100, 1)
            })
            total_carbs += rice["carbs_per_100g"] * rice_weight / 100
        
        # 添加蔬菜
        if vegetables:
            veg = vegetables[0]
            veg_weight = min(200, protein_carbs / veg["carbs_per_100g"] * 100) if veg["carbs_per_100g"] > 0 else 150
            foods.append({
                "name": veg["name"],
                "weight": round(veg_weight),
                "carbs": round(veg["carbs_per_100g"] * veg_weight / 100, 1)
            })
            total_carbs += veg["carbs_per_100g"] * veg_weight / 100
        
        # 添加蛋白质
        if proteins:
            protein = proteins[0]
            foods.append({
                "name": protein["name"],
                "weight": 100,
                "carbs": 0
            })
        
        # 计算GL
        gi_total = sum(f.get("gi", 0) * f.get("carbs", 0) for f in foods)
        gl = gi_total / total_carbs if total_carbs > 0 else 0
        
        # 生成建议
        if gl < 10:
            recommendation = "低GL餐食，适合血糖控制"
        elif gl < 20:
            recommendation = "中等GL餐食，适量食用"
        else:
            recommendation = "高GL餐食，建议减少主食量或替换为低GI食物"
        
        return MealPlan(
            meal_type=meal_type,
            foods=foods,
            total_carbs=round(total_carbs, 1),
            total_calories=sum(f.get("calories", 0) for f in foods),
            gi=round(gi_total / total_carbs if total_carbs > 0 else 0, 0),
            gl=round(gl, 1),
            recommendation=recommendation
        )
    
    def generate_daily_plan(self, patient_info: Dict) -> Dict:
        """生成每日食谱"""
        weight = patient_info.get("weight", 70)
        activity = patient_info.get("activity", "moderate")
        
        # 计算每日碳水需求
        calc = CarbohydrateCalculator()
        daily_req = calc.calculate_daily_requirement(weight, activity)
        daily_carbs = daily_req["carbs_grams_typical"]
        
        # 分配到各餐
        meal_distribution = {
            "breakfast": daily_carbs * 0.25,
            "lunch": daily_carbs * 0.35,
            "dinner": daily_carbs * 0.30,
            "snack": daily_carbs * 0.10
        }
        
        meals = {}
        for meal_type, carbs in meal_distribution.items():
            if carbs > 5:
                meal_plan = self.generate_meal_plan(patient_info, meal_type, carbs)
                meals[meal_type] = {
                    "foods": meal_plan.foods,
                    "target_carbs": carbs,
                    "actual_carbs": meal_plan.total_carbs,
                    "gl": meal_plan.gl,
                    "recommendation": meal_plan.recommendation
                }
        
        return {
            "daily_carbs_target": daily_carbs,
            "meals": meals,
            "tips": [
                "餐餐有蔬菜，天天有豆制品",
                "先吃菜后吃饭，先喝汤后吃饭",
                "细嚼慢咽，每餐20分钟以上",
                "餐后半小时内适度运动"
            ]
        }


# 全局实例
food_database = FoodDatabase()
food_database._ensure_loaded()  # 优先从数据库加载
carb_calculator = CarbohydrateCalculator()
glucose_analyzer = BloodSugarAnalyzer()
recipe_generator = RecipeGenerator()
