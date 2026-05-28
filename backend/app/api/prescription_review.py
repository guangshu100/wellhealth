"""处方前置审核API"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class MedicationItem(BaseModel):
    """药品项"""
    drug_name: str
    dosage: str
    frequency: str
    route: str = "口服"


class PrescriptionReviewRequest(BaseModel):
    """处方审核请求"""
    patient_id: str
    medications: List[MedicationItem]
    diagnosis: List[str] = []
    patient_context: Dict[str, Any] = {}


class PrescriptionReviewResponse(BaseModel):
    """处方审核响应"""
    review_id: str
    status: str
    layers: Dict[str, Any]
    all_issues: List[Dict[str, Any]]
    all_suggestions: List[Dict[str, Any]]
    summary: str
    reviewed_at: str


@router.post("/review", response_model=PrescriptionReviewResponse)
async def review_prescription(
    request: PrescriptionReviewRequest,
    db: Session = Depends(get_db),
):
    """执行三层处方审核"""
    try:
        from app.services.prescription_review_service import get_prescription_review_service

        service = get_prescription_review_service()
        result = await service.review_prescription(
            db=db,
            patient_id=request.patient_id,
            medications=[m.model_dump() for m in request.medications],
            diagnosis=request.diagnosis,
            patient_context=request.patient_context,
        )
        return PrescriptionReviewResponse(**result)
    except Exception as e:
        logger.error(f"Prescription review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{review_id}")
async def get_review_result(review_id: str, db: Session = Depends(get_db)):
    """查询审核结果"""
    try:
        from app.models.extension_models import PrescriptionReviewResult
        results = db.query(PrescriptionReviewResult).filter(
            PrescriptionReviewResult.review_id == review_id
        ).all()

        if not results:
            raise HTTPException(status_code=404, detail="审核结果不存在")

        return {
            "review_id": review_id,
            "results": [
                {
                    "reviewer_type": r.reviewer_type,
                    "status": r.status,
                    "issues": r.issues,
                    "suggestions": r.suggestions,
                    "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                }
                for r in results
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review result: {e}")
        raise HTTPException(status_code=500, detail=str(e))
