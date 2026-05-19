from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.utils.auth import get_current_user, CurrentUser
from app.services.cognitive_service import CognitiveService

router = APIRouter(tags=["认知健康"])

cognitive_service = CognitiveService()


class TextAnalysisRequest(BaseModel):
    text: str


class ExerciseGenerateRequest(BaseModel):
    exercise_type: str
    difficulty: str = "intermediate"


class TrainingSubmitRequest(BaseModel):
    exercise_type: str
    difficulty: str = "intermediate"
    score: Optional[int] = None
    accuracy: Optional[float] = None
    duration_seconds: Optional[int] = None
    details: Optional[dict] = None


@router.post("/analyze-text")
async def analyze_text(request: TextAnalysisRequest, current_user: CurrentUser = Depends(get_current_user)):
    try:
        result = await cognitive_service.analyze_text(request.text, current_user.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-speech")
async def analyze_speech(
    current_user: CurrentUser = Depends(get_current_user),
    audio_file: UploadFile = File(None),
):
    try:
        result = await cognitive_service.analyze_speech(audio_file, current_user.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/generate")
async def generate_exercise(request: ExerciseGenerateRequest, current_user: CurrentUser = Depends(get_current_user)):
    try:
        result = await cognitive_service.generate_exercise(request.exercise_type, request.difficulty)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/submit")
async def submit_training(request: TrainingSubmitRequest, current_user: CurrentUser = Depends(get_current_user)):
    try:
        session_data = {
            "difficulty": request.difficulty,
            "score": request.score,
            "accuracy": request.accuracy,
            "duration_seconds": request.duration_seconds,
            "details": request.details,
        }
        result = await cognitive_service.evaluate_session(request.exercise_type, session_data, current_user.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/progress")
async def get_progress(current_user: CurrentUser = Depends(get_current_user)):
    try:
        result = await cognitive_service.get_progress_metrics(current_user.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments")
async def get_assessments(limit: int = 10, current_user: CurrentUser = Depends(get_current_user)):
    try:
        result = await cognitive_service.get_assessment_history(current_user.user_id, limit)
        return {"assessments": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
