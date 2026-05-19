"""
亲情账号API
包括：家庭管理、关怀消息、家人健康查看
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from app.utils.auth import get_current_user, CurrentUser
from app.services.family_service import (
    FamilyService,
    CareMessageService,
    MemoryService,
    HealthAlertService,
    MedicationComplianceService,
    EncourageCardService,
    FamilyActivityService,
    FamilyInviteService,
    FamilyPrivacyService,
    FamilyMemberAlertService,
    FamilyMemberService,
)
from app.services.health_prediction_service import (
    HealthTrendAnalysisService,
    HealthRiskPredictionService,
)

router = APIRouter(prefix="/api/v1/family", tags=["亲情账号"])


# ========== 数据模型 ==========


class CreateFamilyRequest(BaseModel):
    name: str
    owner_id: str
    owner_name: str


class AddMemberRequest(BaseModel):
    family_id: str
    user_id: str
    user_name: str
    role: str  # owner, parent, child
    relationship: str  # father, mother, son, daughter
    patient_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    family_id: str
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    content: str


class MemoryRequest(BaseModel):
    user_id: str
    memory_type: str  # conversation, health, preference, emotion
    content: str
    importance: int = 5


class MemoryRecallRequest(BaseModel):
    user_id: str
    context: str
    limit: int = 5


class ComplianceQueryRequest(BaseModel):
    patient_id: str
    days: int = 30


class RiskPredictionRequest(BaseModel):
    patient_data: Dict[str, Any]
    risk_type: str = "diabetes"


class TrendAnalysisRequest(BaseModel):
    patient_id: str
    vital_type: str
    days: int = 30


# ========== 家庭管理API ==========


@router.post("/create")
async def create_family(request: CreateFamilyRequest):
    """创建家庭"""
    try:
        family = FamilyService.create_family(
            name=request.name, owner_id=request.owner_id, owner_name=request.owner_name
        )
        return {
            "success": True,
            "family": {
                "id": family["id"],
                "name": family["name"],
                "owner_id": family["owner_id"],
                "created_at": family["created_at"].isoformat() if family["created_at"] else None,
            },
        }
    except Exception as e:
        logger.error(f"创建家庭失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/member/add")
async def add_member(request: AddMemberRequest):
    """添加家庭成员"""
    try:
        member = FamilyService.add_member(
            family_id=request.family_id,
            user_id=request.user_id,
            user_name=request.user_name,
            role=request.role,
            relationship_type=request.relationship,
            patient_id=request.patient_id,
        )
        return {
            "success": True,
            "member": {
                "id": member["id"],
                "user_id": member["user_id"],
                "user_name": member["user_name"],
                "role": member["role"],
                "relationship": member["relationship_type"],
                "patient_id": member["patient_id"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{family_id}/members")
async def get_family_members(family_id: str):
    """获取家庭成员列表"""
    try:
        members = FamilyService.get_family_members(family_id)
        return {
            "success": True,
            "members": [
                {
                    "id": m["id"],
                    "user_id": m["user_id"],
                    "user_name": m["user_name"],
                    "role": m["role"],
                    "relationship": m["relationship_type"],
                    "phone": m["phone"],
                    "notification_enabled": m["notification_enabled"],
                    "patient_id": m["patient_id"],
                }
                for m in members
            ],
        }
    except Exception as e:
        logger.error(f"添加家庭成员失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/families")
async def get_user_families(user_id: str):
    """获取用户所属家庭"""
    try:
        logger.info(f"获取用户 {user_id} 的家庭列表")
        families = FamilyService.get_user_families(user_id)
        return {
            "success": True,
            "families": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "owner_id": f["owner_id"],
                    "created_at": f["created_at"].isoformat() if f["created_at"] else None,
                }
                for f in families
            ],
        }
    except Exception as e:
        logger.error(f"获取用户家庭列表失败 user_id={user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-families")
async def get_my_families(current_user: CurrentUser = Depends(get_current_user)):
    try:
        families = FamilyService.get_user_families(current_user.user_id)
        return {
            "success": True,
            "families": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "owner_id": f["owner_id"],
                    "created_at": f["created_at"].isoformat() if f["created_at"] else None,
                }
                for f in families
            ],
        }
    except Exception as e:
        logger.error(f"获取我的家庭列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}/family")
async def get_patient_family(patient_id: str):
    """获取患者关联的家庭"""
    try:
        family = FamilyService.get_patient_family(patient_id)
        if not family:
            return {"success": True, "family": None}

        members = FamilyService.get_family_members(family["id"])
        return {
            "success": True,
            "family": {
                "id": family["id"],
                "name": family["name"],
                "members": [
                    {
                        "user_id": m["user_id"],
                        "user_name": m["user_name"],
                        "role": m["role"],
                        "relationship": m["relationship"],
                        "patient_id": m["patient_id"],
                    }
                    for m in members
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 关怀消息API ==========


@router.post("/message/send")
async def send_message(request: SendMessageRequest):
    """发送关怀消息"""
    try:
        message = CareMessageService.send_message(
            family_id=request.family_id,
            from_user_id=request.from_user_id,
            from_user_name=request.from_user_name,
            to_user_id=request.to_user_id,
            to_user_name=request.to_user_name,
            content=request.content,
            message_type="manual",
        )
        return {
            "success": True,
            "message_id": message["id"],
            "created_at": message["created_at"].isoformat() if message["created_at"] else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/message/{user_id}/unread")
async def get_unread_messages(user_id: str):
    """获取未读关怀消息"""
    try:
        messages = CareMessageService.get_unread_messages(user_id)
        return {
            "success": True,
            "messages": [
                {
                    "id": m["id"],
                    "from_user_name": m["from_user_name"],
                    "content": m["content"],
                    "message_type": m["message_type"],
                    "created_at": m["created_at"].isoformat() if m["created_at"] else None,
                }
                for m in messages
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/{message_id}/read")
async def mark_message_read(message_id: str):
    """标记消息为已读"""
    try:
        CareMessageService.mark_as_read(message_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 健康数据查看API ==========


@router.get("/patient/{patient_id}/health-summary")
async def get_patient_health_summary(patient_id: str, days: int = 7):
    """获取患者健康摘要（供家人查看）"""
    try:
        # 获取近期健康数据趋势
        trends = {}

        # 血糖趋势
        glucose_trend = await HealthTrendAnalysisService.analyze_trend(
            patient_id, "blood_sugar_fasting", days
        )
        trends["blood_sugar"] = {
            "trend": glucose_trend.trend,
            "avg_value": glucose_trend.avg_value,
            "alerts": glucose_trend.alerts,
        }

        # 血压趋势
        bp_trend = await HealthTrendAnalysisService.analyze_trend(
            patient_id, "blood_pressure_systolic", days
        )
        trends["blood_pressure"] = {
            "trend": bp_trend.trend,
            "avg_value": bp_trend.avg_value,
            "alerts": bp_trend.alerts,
        }

        # 用药依从性
        compliance = MedicationComplianceService.calculate_compliance(patient_id, days)

        # 获取预警
        alerts = HealthAlertService.get_patient_alerts(patient_id, days)

        return {
            "success": True,
            "summary": {
                "patient_id": patient_id,
                "period_days": days,
                "trends": trends,
                "medication_compliance": compliance,
                "alerts": [
                    {
                        "title": a["title"],
                        "content": a["content"],
                        "severity": a["severity"],
                        "created_at": a["created_at"].isoformat() if a["created_at"] else None,
                    }
                    for a in alerts
                    if not a["is_resolved"]
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 用药依从性API ==========


@router.post("/medication/compliance")
async def get_medication_compliance(request: ComplianceQueryRequest):
    """获取用药依从性"""
    try:
        compliance = MedicationComplianceService.calculate_compliance(
            request.patient_id, request.days
        )
        return {"success": True, "compliance": compliance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 健康预测API ==========


@router.post("/health/trend")
async def analyze_health_trend(request: TrendAnalysisRequest):
    """分析健康趋势"""
    try:
        trend = await HealthTrendAnalysisService.analyze_trend(
            request.patient_id, request.vital_type, request.days
        )
        return {
            "success": True,
            "trend": {
                "metric": trend.metric,
                "trend": trend.trend,
                "change_rate": trend.change_rate,
                "avg_value": trend.avg_value,
                "min_value": trend.min_value,
                "max_value": trend.max_value,
                "prediction": trend.prediction,
                "alerts": trend.alerts,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/risk-prediction")
async def predict_health_risk(request: RiskPredictionRequest):
    """预测健康风险"""
    try:
        prediction = await HealthRiskPredictionService().predict_risk(
            request.patient_data, request.risk_type
        )
        return {
            "success": True,
            "prediction": {
                "risk_type": prediction.risk_type,
                "risk_level": prediction.risk_level.value,
                "probability": prediction.probability,
                "factors": prediction.factors,
                "recommendations": prediction.recommendations,
                "suggested_actions": prediction.suggested_actions,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 记忆API ==========


@router.post("/memory/remember")
async def remember(request: MemoryRequest):
    """存储记忆"""
    try:
        memory = MemoryService.remember(
            user_id=request.user_id,
            memory_type=request.memory_type,
            content=request.content,
            importance=request.importance,
        )
        return {"success": True, "memory_id": memory["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/recall")
async def recall(request: MemoryRecallRequest):
    """检索记忆"""
    try:
        memories = MemoryService.recall(
            user_id=request.user_id, context=request.context, limit=request.limit
        )
        return {
            "success": True,
            "memories": [
                {
                    "id": m["id"],
                    "memory_type": m["memory_type"],
                    "content": m["content"],
                    "importance": m["importance"],
                    "created_at": m["created_at"].isoformat() if m["created_at"] else None,
                }
                for m in memories
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{user_id}/summary")
async def get_memory_summary(user_id: str, days: int = 7):
    """获取对话摘要"""
    try:
        summary = MemoryService.get_conversation_summary(user_id, days)
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 鼓励卡片API ==========


class SendEncourageCardRequest(BaseModel):
    family_id: str
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    card_id: str


class CreateCustomCardRequest(BaseModel):
    name: str
    icon: str
    content: str
    category: str
    created_by: str


@router.get("/encourage-cards")
async def get_encourage_cards():
    try:
        EncourageCardService.init_system_cards()
        cards = EncourageCardService.get_cards()
        return {"success": True, "cards": cards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encourage-card/create")
async def create_custom_card(request: CreateCustomCardRequest):
    try:
        card = EncourageCardService.create_custom_card(
            name=request.name,
            icon=request.icon,
            content=request.content,
            category=request.category,
            created_by=request.created_by,
        )
        return {"success": True, "card": card}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encourage-card/send")
async def send_encourage_card(request: SendEncourageCardRequest):
    try:
        result = EncourageCardService.send_encourage_card(
            family_id=request.family_id,
            from_user_id=request.from_user_id,
            from_user_name=request.from_user_name,
            to_user_id=request.to_user_id,
            to_user_name=request.to_user_name,
            card_id=request.card_id,
        )
        return {"success": True, "message": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家庭动态API ==========


class AddActivityRequest(BaseModel):
    family_id: str
    user_id: str
    user_name: str
    activity_type: str
    content: str
    meta: Optional[Dict[str, Any]] = None


@router.get("/{family_id}/activities")
async def get_family_activities(family_id: str, limit: int = 20, offset: int = 0):
    try:
        activities = FamilyActivityService.get_family_activities(family_id, limit, offset)
        return {"success": True, "activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activity/add")
async def add_family_activity(request: AddActivityRequest):
    try:
        activity = FamilyActivityService.add_activity(
            family_id=request.family_id,
            user_id=request.user_id,
            user_name=request.user_name,
            activity_type=request.activity_type,
            content=request.content,
            meta=request.meta,
        )
        return {"success": True, "activity": activity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家庭邀请API ==========


class CreateInviteRequest(BaseModel):
    family_id: str
    inviter_id: str
    inviter_name: str
    relationship: str = "other"
    expires_hours: int = 72


class AcceptInviteRequest(BaseModel):
    invite_code: str
    user_id: str
    user_name: str


@router.post("/invite/create")
async def create_invite(request: CreateInviteRequest):
    try:
        invite = FamilyInviteService.create_invite(
            family_id=request.family_id,
            inviter_id=request.inviter_id,
            inviter_name=request.inviter_name,
            relationship=request.relationship,
            expires_hours=request.expires_hours,
        )
        return {"success": True, "invite": invite}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invite/accept")
async def accept_invite(request: AcceptInviteRequest):
    try:
        result = FamilyInviteService.accept_invite(
            invite_code=request.invite_code,
            user_id=request.user_id,
            user_name=request.user_name,
        )
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 隐私设置API ==========


class UpdatePrivacyRequest(BaseModel):
    family_id: str
    user_id: str
    can_view_health: Optional[bool] = None
    can_view_medication: Optional[bool] = None
    can_view_cognitive: Optional[bool] = None
    can_view_training: Optional[bool] = None
    can_send_encourage: Optional[bool] = None
    can_receive_alerts: Optional[bool] = None


@router.get("/{family_id}/privacy/{user_id}")
async def get_privacy_settings(family_id: str, user_id: str):
    try:
        settings = FamilyPrivacyService.get_privacy_settings(family_id, user_id)
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{family_id}/privacy/{user_id}")
async def update_privacy_settings(family_id: str, user_id: str, request: UpdatePrivacyRequest):
    try:
        updates = {k: v for k, v in request.model_dump().items() if v is not None and k not in ["family_id", "user_id"]}
        settings = FamilyPrivacyService.update_privacy_settings(family_id, user_id, updates)
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家庭成员预警通知API ==========


@router.get("/alerts/{user_id}")
async def get_member_alerts(user_id: str, unread_only: bool = False):
    try:
        alerts = FamilyMemberAlertService.get_member_alerts(user_id, unread_only)
        unread_count = FamilyMemberAlertService.get_unread_count(user_id)
        return {"success": True, "alerts": alerts, "unread_count": unread_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/read")
async def mark_member_alert_read(alert_id: str):
    try:
        FamilyMemberAlertService.mark_alert_read(alert_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 家庭成员管理增强API ==========


class RemoveMemberRequest(BaseModel):
    family_id: str
    member_id: str
    operator_id: str


class UpdateMemberRequest(BaseModel):
    family_id: str
    member_id: str
    role: Optional[str] = None
    relationship_type: Optional[str] = None
    phone: Optional[str] = None
    notification_enabled: Optional[bool] = None
    patient_id: Optional[str] = None


@router.delete("/{family_id}/member/{member_id}")
async def remove_member(family_id: str, member_id: str, operator_id: str):
    try:
        FamilyMemberService.remove_member(family_id, member_id, operator_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{family_id}/member/{member_id}")
async def update_member(family_id: str, member_id: str, request: UpdateMemberRequest):
    try:
        updates = {k: v for k, v in request.model_dump().items() if v is not None and k not in ["family_id", "member_id"]}
        member = FamilyMemberService.update_member(family_id, member_id, updates)
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{family_id}/stats")
async def get_family_stats(family_id: str):
    try:
        stats = FamilyMemberService.get_family_stats(family_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
