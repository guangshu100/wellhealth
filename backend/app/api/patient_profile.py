"""患者全景画像API"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class PatientPanoramaResponse(BaseModel):
    """患者全景画像响应"""
    patient_id: str
    patient_name: str
    generated_at: str
    chronic_diseases: list
    current_medications: list
    vital_trends: dict
    interventions: list
    missing_indicators: list
    risk_prediction: dict


@router.get("/{patient_id}/panorama", response_model=PatientPanoramaResponse)
async def get_patient_panorama(
    patient_id: str,
    db: Session = Depends(get_db),
):
    """获取患者全景画像"""
    try:
        from app.services.patient_profile_service import get_patient_profile_service
        service = get_patient_profile_service()
        result = service.generate_panorama(db, patient_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return PatientPanoramaResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate patient panorama: {e}")
        raise HTTPException(status_code=500, detail=str(e))
