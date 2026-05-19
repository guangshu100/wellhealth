"""
拍照做菜增强API
包括：食材识别、菜谱生成、家庭菜谱
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import base64
import uuid

from app.services.recipe_service import (
    FoodDetectionService,
    RecipeGenerationService,
    FamilyRecipeService,
    NutritionCalculationService,
)
from app.services.family_service import FamilyService

router = APIRouter(prefix="/api/v1/recipe", tags=["拍照做菜"])


# ========== 数据模型 ==========


class DetectIngredientsRequest(BaseModel):
    image: str  # base64编码的图片
    user_id: Optional[str] = None


class DetectFromTextRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


class GenerateRecipeRequest(BaseModel):
    ingredients: List[str]
    preferences: Optional[Dict[str, Any]] = None
    family_context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class CreateRecipeRequest(BaseModel):
    family_id: str
    creator_id: str
    creator_name: str
    title: str
    description: Optional[str] = None
    ingredients: Optional[List[Dict]] = None
    steps: Optional[List[Dict]] = None
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None
    nutrition: Optional[Dict] = None
    tags: Optional[List[str]] = None
    is_legacy: bool = False
    is_shared: bool = True


class AddRecipeCommentRequest(BaseModel):
    recipe_id: str
    user_id: str
    user_name: str
    content: str


class CalculateNutritionRequest(BaseModel):
    ingredients: List[Dict[str, Any]]


# ========== 食材识别API ==========


@router.post("/detect-image")
async def detect_ingredients_from_image(request: DetectIngredientsRequest):
    """从图片识别食材"""
    try:
        service = FoodDetectionService()

        ingredients = await service.detect_from_image(request.image)

        if not ingredients:
            return {"success": False, "message": "无法识别图片中的食材", "ingredients": []}

        return {
            "success": True,
            "ingredients": [
                {"name": i.name, "confidence": i.confidence, "category": i.category}
                for i in ingredients
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-text")
async def detect_ingredients_from_text(request: DetectFromTextRequest):
    """从文字描述识别食材"""
    try:
        service = FoodDetectionService()

        ingredients = await service.detect_from_text(request.text)

        return {
            "success": True,
            "ingredients": [
                {"name": i.name, "confidence": i.confidence, "category": i.category}
                for i in ingredients
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 菜谱生成API ==========


@router.post("/generate")
async def generate_recipe(request: GenerateRecipeRequest):
    """生成菜谱"""
    try:
        service = RecipeGenerationService()

        recipe = await service.generate_recipe(
            ingredients=request.ingredients,
            preferences=request.preferences,
            family_context=request.family_context,
        )

        if not recipe:
            return {"success": False, "message": "菜谱生成失败", "recipe": None}

        return {
            "success": True,
            "recipe": {
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": recipe.ingredients,
                "steps": recipe.steps,
                "cooking_time": recipe.cooking_time,
                "difficulty": recipe.difficulty,
                "nutrition": recipe.nutrition,
                "tips": recipe.tips,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-weekly")
async def generate_weekly_plan(preferences: Dict[str, Any]):
    """生成一周食谱"""
    try:
        service = RecipeGenerationService()

        recipes = await service.generate_weekly_plan(preferences)

        return {
            "success": True,
            "recipes": [
                {
                    "title": r.title,
                    "description": r.description,
                    "cooking_time": r.cooking_time,
                    "difficulty": r.difficulty,
                    "nutrition": r.nutrition,
                }
                for r in recipes
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家庭菜谱API ==========


@router.post("/family/create")
async def create_family_recipe(request: CreateRecipeRequest):
    """创建家庭菜谱"""
    try:
        recipe = await FamilyRecipeService.create_recipe(
            family_id=request.family_id,
            creator_id=request.creator_id,
            creator_name=request.creator_name,
            title=request.title,
            description=request.description,
            ingredients=request.ingredients,
            steps=request.steps,
            cooking_time=request.cooking_time,
            difficulty=request.difficulty,
            nutrition=request.nutrition,
            tags=request.tags,
            is_legacy=request.is_legacy,
            is_shared=request.is_shared,
        )
        return {
            "success": True,
            "recipe_id": recipe.id,
            "created_at": recipe.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/family/{family_id}/list")
async def get_family_recipes(family_id: str, include_legacy: bool = True):
    """获取家庭菜谱列表"""
    try:
        recipes = await FamilyRecipeService.get_family_recipes(family_id, include_legacy)
        return {
            "success": True,
            "recipes": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "cooking_time": r.cooking_time,
                    "difficulty": r.difficulty,
                    "is_legacy": r.is_legacy,
                    "tags": r.tags,
                    "creator_name": r.creator_name,
                    "created_at": r.created_at.isoformat(),
                }
                for r in recipes
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{recipe_id}")
async def get_recipe_detail(recipe_id: str):
    """获取菜谱详情"""
    try:
        recipe = await FamilyRecipeService.get_recipe_by_id(recipe_id)

        if not recipe:
            raise HTTPException(status_code=404, detail="菜谱不存在")

        return {
            "success": True,
            "recipe": {
                "id": recipe.id,
                "family_id": recipe.family_id,
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": recipe.ingredients,
                "steps": recipe.steps,
                "cooking_time": recipe.cooking_time,
                "difficulty": recipe.difficulty,
                "nutrition": recipe.nutrition,
                "tags": recipe.tags,
                "is_legacy": recipe.is_legacy,
                "creator_name": recipe.creator_name,
                "created_at": recipe.created_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment")
async def add_recipe_comment(request: AddRecipeCommentRequest):
    """添加菜谱评论"""
    try:
        comment = await FamilyRecipeService.add_comment(
            recipe_id=request.recipe_id,
            user_id=request.user_id,
            user_name=request.user_name,
            content=request.content,
        )
        return {
            "success": True,
            "comment_id": comment.id,
            "created_at": comment.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recipe_id}/mark-legacy")
async def mark_recipe_as_legacy(recipe_id: str):
    """标记为传承菜谱"""
    try:
        await FamilyRecipeService.mark_as_legacy(recipe_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 营养计算API ==========


@router.post("/nutrition/calculate")
async def calculate_nutrition(request: CalculateNutritionRequest):
    """计算营养成分"""
    try:
        nutrition = NutritionCalculationService.calculate_nutrition(request.ingredients)
        return {"success": True, "nutrition": nutrition}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 拍照识别完整流程API ==========


@router.post("/capture-and-cook")
async def capture_and_cook(
    image: str = Form(...),
    user_id: Optional[str] = Form(None),
    family_id: Optional[str] = Form(None),
    preferences: Optional[str] = Form(None),
):
    """拍照识别食材并生成菜谱（完整流程）"""
    try:
        # 1. 识别食材
        detection_service = FoodDetectionService()
        ingredients = await detection_service.detect_from_image(image)

        if not ingredients:
            return {"success": False, "message": "无法识别图片中的食材", "stage": "detection"}

        ingredient_names = [i.name for i in ingredients]

        # 2. 生成菜谱
        recipe_service = RecipeGenerationService()
        pref_dict = {}
        if preferences:
            import json

            pref_dict = json.loads(preferences)

        recipe = await recipe_service.generate_recipe(
            ingredients=ingredient_names, preferences=pref_dict
        )

        if not recipe:
            return {
                "success": False,
                "message": "菜谱生成失败",
                "stage": "generation",
                "ingredients": ingredient_names,
            }

        # 3. 如果指定了family_id，可以保存到家庭菜谱
        saved_recipe_id = None
        if family_id and user_id:
            saved_recipe = await FamilyRecipeService.create_recipe(
                family_id=family_id,
                creator_id=user_id,
                creator_name="AI",
                title=recipe.title,
                description=recipe.description,
                ingredients=[{"name": i.name} for i in ingredients],
                steps=recipe.steps,
                cooking_time=recipe.cooking_time,
                difficulty=recipe.difficulty,
                nutrition=recipe.nutrition,
                tags=["AI生成"],
            )
            saved_recipe_id = saved_recipe.id

        return {
            "success": True,
            "stage": "completed",
            "detected_ingredients": [
                {"name": i.name, "confidence": i.confidence, "category": i.category}
                for i in ingredients
            ],
            "recipe": {
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": recipe.ingredients,
                "steps": recipe.steps,
                "cooking_time": recipe.cooking_time,
                "difficulty": recipe.difficulty,
                "nutrition": recipe.nutrition,
                "tips": recipe.tips,
            },
            "saved_recipe_id": saved_recipe_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
