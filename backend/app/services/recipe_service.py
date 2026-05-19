"""
拍照做菜增强服务
包括：食材识别、菜谱生成、家庭菜谱
"""

import uuid
import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.services.llm_client import get_llm_client
from app.models.family_models import FamilyRecipe, RecipeComment
from app.utils.database import get_db_session

logger = logging.getLogger(__name__)


# 常见食材数据库
FOOD_INGREDIENTS_DB = {
    "蔬菜类": [
        "白菜", "菠菜", "油菜", "芹菜", "黄瓜", "西红柿", "番茄",
        "土豆", "胡萝卜", "青椒", "洋葱", "茄子", "豆角",
        "西兰花", "生菜", "冬瓜", "丝瓜", "南瓜", "玉米",
        "莲藕", "山药", "红薯", "紫薯", "莴笋", "芦笋",
        "苦瓜", "西葫芦", "香菜", "韭菜", "蒜苗", "豆芽",
    ],
    "肉类": [
        "猪肉", "牛肉", "鸡肉", "鸭肉", "鱼肉", "虾", "鸡蛋",
        "排骨", "五花肉", "里脊", "鸡翅", "鸡腿", "牛腩",
        "羊肉", "鸭血", "猪肝", "肥牛", "培根", "火腿",
    ],
    "主食类": [
        "米饭", "面条", "馒头", "面包", "饺子", "包子",
        "花卷", "烙饼", "年糕", "米粉", "馄饨", "粥",
    ],
    "豆制品": ["豆腐", "豆浆", "豆芽", "腐竹", "豆腐皮", "豆腐干", "千张"],
    "菌类": ["蘑菇", "木耳", "香菇", "金针菇", "杏鲍菇", "平菇", "茶树菇"],
    "水果类": [
        "苹果", "香蕉", "橙子", "西瓜", "葡萄", "草莓",
        "梨", "桃子", "芒果", "猕猴桃", "柚子", "荔枝",
    ],
    "奶类": ["牛奶", "酸奶", "奶酪", "黄油", "奶油"],
    "调味料": [
        "盐", "糖", "酱油", "醋", "料酒", "蚝油", "豆瓣酱",
        "番茄酱", "淀粉", "花椒", "八角", "桂皮", "姜", "蒜", "葱",
    ],
}

FOOD_SYNONYMS: Dict[str, str] = {
    "番茄": "西红柿",
    "土豆": "马铃薯",
    "红薯": "地瓜",
    "西兰花": "花椰菜",
    "排骨": "猪肉",
    "五花肉": "猪肉",
    "里脊": "猪肉",
    "鸡翅": "鸡肉",
    "鸡腿": "鸡肉",
    "牛腩": "牛肉",
    "肥牛": "牛肉",
    "千张": "豆腐皮",
}


@dataclass
class DetectedIngredient:
    name: str
    confidence: float
    category: str


@dataclass
class GeneratedRecipe:
    title: str
    description: str
    ingredients: List[Dict]
    steps: List[Dict]
    cooking_time: int
    difficulty: str
    nutrition: Dict[str, Any]
    tips: List[str]


class FoodDetectionService:
    """食材识别服务"""

    def __init__(self):
        self.vision_prompt = """你是一个专业的食材识别专家。请分析这张食物图片：

1. 识别出所有可见的食材（中文名称）
2. 对每种食材给出置信度（0-1之间）
3. 请严格按照以下JSON格式返回，不要有任何额外内容：
```json
{
  "ingredients": [
    {"name": "食材名称", "confidence": 0.95, "category": "分类"}
  ]
}
```
注意：
- 只返回JSON，不要有任何解释或额外文字
- category可以是：蔬菜类、肉类、主食类、豆制品、菌类、水果类、奶类、其他
- 如果无法识别，返回 {"ingredients": []}"""

    async def detect_from_image(self, image_base64: str) -> List[DetectedIngredient]:
        """从图片识别食材"""
        try:
            llm = get_llm_client()

            response = await llm.chat_with_image(
                image_base64=image_base64,
                prompt=self.vision_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            if not response or "暂时不可用" in response:
                return []

            # 解析JSON响应
            ingredients = self._parse_response(response)
            return ingredients

        except Exception as e:
            logger.error(f"食材识别失败: {e}")
            return []

    def _parse_response(self, response: str) -> List[DetectedIngredient]:
        """解析LLM响应"""
        try:
            # 提取JSON
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return []

            data = json.loads(json_match.group())
            ingredients_list = data.get("ingredients", [])

            results = []
            for item in ingredients_list:
                name = item.get("name", "")
                confidence = item.get("confidence", 0.5)
                category = item.get("category", "其他")

                # 分类
                category = self._categorize_ingredient(name, category)

                results.append(
                    DetectedIngredient(name=name, confidence=confidence, category=category)
                )

            return results

        except Exception as e:
            logger.error(f"解析食材响应失败: {e}")
            return []

    def _categorize_ingredient(self, name: str, default_category: str) -> str:
        """对食材进行分类"""
        for category, foods in FOOD_INGREDIENTS_DB.items():
            if any(food in name for food in foods):
                return category
        return default_category

    async def detect_from_text(self, text: str) -> List[DetectedIngredient]:
        """从文字描述识别食材"""
        try:
            llm = get_llm_client()
            prompt = f"""你是一个专业的食材识别专家。请从以下文字中识别出所有食材：

"{text}"

请严格按照以下JSON格式返回，不要有任何额外内容：
```json
{{
  "ingredients": [
    {{"name": "食材名称", "confidence": 0.95, "category": "分类"}}
  ]
}}
```
注意：
- 只返回JSON，不要有任何解释或额外文字
- category可以是：蔬菜类、肉类、主食类、豆制品、菌类、水果类、奶类、调味料、其他
- 识别出所有提到的食材，不要遗漏
- 如果无法识别，返回 {{"ingredients": []}}"""

            response = await llm.chat_with_system(
                system_prompt="你是一个专业的食材识别专家，只返回JSON格式的结果。",
                user_message=prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            if response and "暂时不可用" not in response:
                ingredients = self._parse_response(response)
                if ingredients:
                    return ingredients

            return self._keyword_fallback(text)

        except Exception as e:
            logger.error(f"文字识别失败: {e}")
            return self._keyword_fallback(text)

    def _keyword_fallback(self, text: str) -> List[DetectedIngredient]:
        """关键词匹配降级方案"""
        detected = []
        text_lower = text.lower()

        for category, foods in FOOD_INGREDIENTS_DB.items():
            for food in foods:
                if food in text_lower:
                    display_name = food
                    for syn, standard in FOOD_SYNONYMS.items():
                        if food == standard and syn in text_lower:
                            display_name = syn
                            break
                    detected.append(
                        DetectedIngredient(name=display_name, confidence=1.0, category=category)
                    )

        return detected


class RecipeGenerationService:
    """菜谱生成服务"""

    def __init__(self):
        self.recipe_prompt = """你是一个专业的中餐厨师。根据用户提供的食材，生成美味的家常菜谱。

请严格按照以下JSON格式返回：
```json
{
  "title": "菜谱名称",
  "description": "简短描述",
  "ingredients": [
    {"name": "食材名称", "amount": "用量", "note": "备注"}
  ],
  "steps": [
    {"step": 1, "description": "步骤描述", "tip": "小技巧(可选)"}
  ],
  "cooking_time": 30,
  "difficulty": "easy",
  "nutrition": {"calories": 500, "protein": 20, "carbs": 30, "fat": 15},
  "tips": ["烹饪小贴士1", "烹饪小贴士2"]
}
```
注意：
- cooking_time单位是分钟
- difficulty可以是：easy, medium, hard
- 请根据食材特点选择合适的烹饪方式"""

    async def generate_recipe(
        self,
        ingredients: List[str],
        preferences: Optional[Dict[str, Any]] = None,
        family_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[GeneratedRecipe]:
        """生成菜谱"""
        try:
            llm = get_llm_client()

            # 构建prompt
            ingredients_str = "、".join(ingredients)
            prompt = f"食材：{ingredients_str}\n\n"

            if preferences:
                if preferences.get("difficulty"):
                    prompt += f"难度偏好：{preferences['difficulty']}\n"
                if preferences.get("cooking_time"):
                    prompt += f"希望烹饪时间：{preferences['cooking_time']}分钟以内\n"
                if preferences.get("dietary_restrictions"):
                    prompt += f"饮食限制：{preferences['dietary_restrictions']}\n"

            if family_context:
                prompt += f"\n家庭背景：{family_context.get('description', '')}\n"

            prompt += f"\n{self.recipe_prompt}"

            response = await llm.chat(prompt=prompt, temperature=0.7, max_tokens=2000)

            if not response:
                return None

            # 解析响应
            recipe = self._parse_response(response)
            return recipe

        except Exception as e:
            logger.error(f"菜谱生成失败: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[GeneratedRecipe]:
        """解析菜谱响应"""
        try:
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            return GeneratedRecipe(
                title=data.get("title", ""),
                description=data.get("description", ""),
                ingredients=data.get("ingredients", []),
                steps=data.get("steps", []),
                cooking_time=data.get("cooking_time", 30),
                difficulty=data.get("difficulty", "easy"),
                nutrition=data.get("nutrition", {}),
                tips=data.get("tips", []),
            )

        except Exception as e:
            logger.error(f"解析菜谱失败: {e}")
            return None

    async def generate_weekly_plan(self, preferences: Dict[str, Any]) -> List[GeneratedRecipe]:
        """生成一周食谱"""
        recipes = []

        # 简化实现：生成7天的简单食谱
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day in days:
            # 实际应该调用generate_recipe
            recipes.append(
                GeneratedRecipe(
                    title=f"{day}健康餐",
                    description=f"{day}的营养均衡餐",
                    ingredients=[],
                    steps=[],
                    cooking_time=30,
                    difficulty="easy",
                    nutrition={"calories": 600, "protein": 25, "carbs": 50, "fat": 20},
                    tips=["注意营养均衡"],
                )
            )

        return recipes


class FamilyRecipeService:
    """家庭菜谱服务"""

    @staticmethod
    async def create_recipe(
        family_id: str,
        creator_id: str,
        creator_name: str,
        title: str,
        description: Optional[str] = None,
        ingredients: Optional[List[Dict]] = None,
        steps: Optional[List[Dict]] = None,
        cooking_time: Optional[int] = None,
        difficulty: Optional[str] = None,
        nutrition: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        is_legacy: bool = False,
        is_shared: bool = True,
    ) -> FamilyRecipe:
        """创建家庭菜谱"""
        async with get_db_session() as session:
            recipe = FamilyRecipe(
                id=str(uuid.uuid4()),
                family_id=family_id,
                creator_id=creator_id,
                creator_name=creator_name,
                title=title,
                description=description,
                ingredients=ingredients or [],
                steps=steps or [],
                cooking_time=cooking_time,
                difficulty=difficulty,
                nutrition=nutrition or {},
                tags=tags or [],
                is_legacy=is_legacy,
                is_shared=is_shared,
            )
            session.add(recipe)
            await session.commit()
            await session.refresh(recipe)
            return recipe

    @staticmethod
    async def get_family_recipes(family_id: str, include_legacy: bool = True) -> List[FamilyRecipe]:
        """获取家庭菜谱列表"""
        async with get_db_session() as session:
            from sqlalchemy import select, or_

            query = select(FamilyRecipe).where(FamilyRecipe.family_id == family_id)

            if not include_legacy:
                query = query.where(FamilyRecipe.is_shared == True)

            result = await session.execute(query.order_by(FamilyRecipe.created_at.desc()))
            return result.scalars().all()

    @staticmethod
    async def get_recipe_by_id(recipe_id: str) -> Optional[FamilyRecipe]:
        """获取菜谱详情"""
        async with get_db_session() as session:
            from sqlalchemy import select

            result = await session.execute(select(FamilyRecipe).where(FamilyRecipe.id == recipe_id))
            return result.scalars().first()

    @staticmethod
    async def add_comment(
        recipe_id: str, user_id: str, user_name: str, content: str
    ) -> RecipeComment:
        """添加评论"""
        async with get_db_session() as session:
            comment = RecipeComment(
                id=str(uuid.uuid4()),
                recipe_id=recipe_id,
                user_id=user_id,
                user_name=user_name,
                content=content,
            )
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            return comment

    @staticmethod
    async def mark_as_legacy(recipe_id: str) -> None:
        """标记为传承菜谱"""
        async with get_db_session() as session:
            from sqlalchemy import select

            result = await session.execute(select(FamilyRecipe).where(FamilyRecipe.id == recipe_id))
            recipe = result.scalars().first()
            if recipe:
                recipe.is_legacy = True
                await session.commit()


class NutritionCalculationService:
    """营养计算服务"""

    # 基础营养数据（每100g）
    NUTRITION_DB = {
        "米饭": {"calories": 130, "protein": 2.6, "carbs": 28, "fat": 0.3, "fiber": 0.4},
        "猪肉": {"calories": 395, "protein": 14, "carbs": 0, "fat": 37, "fiber": 0},
        "牛肉": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0},
        "鸡肉": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
        "鸡蛋": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
        "白菜": {"calories": 18, "protein": 1.6, "carbs": 3.2, "fat": 0.2, "fiber": 1},
        "土豆": {"calories": 77, "protein": 2.0, "carbs": 17, "fat": 0.1, "fiber": 2.2},
        "西红柿": {"calories": 20, "protein": 0.9, "carbs": 4, "fat": 0.2, "fiber": 1.2},
        "豆腐": {"calories": 76, "protein": 8.1, "carbs": 1.9, "fat": 4.2, "fiber": 0.3},
    }

    @staticmethod
    def calculate_nutrition(ingredients: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算总营养成分"""
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}

        for ingredient in ingredients:
            name = ingredient.get("name", "")
            amount = ingredient.get("amount", 100)  # 默认100g

            # 查找营养数据
            nutrition_data = None
            for food_name, data in NutritionCalculationService.NUTRITION_DB.items():
                if food_name in name:
                    nutrition_data = data
                    break

            if nutrition_data:
                factor = amount / 100
                total["calories"] += nutrition_data.get("calories", 0) * factor
                total["protein"] += nutrition_data.get("protein", 0) * factor
                total["carbs"] += nutrition_data.get("carbs", 0) * factor
                total["fat"] += nutrition_data.get("fat", 0) * factor
                total["fiber"] += nutrition_data.get("fiber", 0) * factor

        return {k: round(v, 1) for k, v in total.items()}
