"""
亲情账号服务
包括：家庭管理、关怀消息、主动关怀触发器
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy import select, and_

from app.models.family_models import (
    Family,
    FamilyMember,
    CareMessage,
    UserMemory,
    MedicationReminderEnhanced,
    MedicationRecordEnhanced,
    HealthAlert,
    FamilyRecipe,
    EncourageCard,
    FamilyActivity,
    FamilyInvite,
    FamilyPrivacySetting,
    FamilyMemberAlert,
)
from app.utils.database import get_db_session

logger = logging.getLogger(__name__)


class FamilyService:
    """家庭服务"""

    @staticmethod
    def create_family(name: str, owner_id: str, owner_name: str) -> Family:
        """创建家庭"""
        logger.info(f"创建家庭: name={name}, owner_id={owner_id}, owner_name={owner_name}")
        try:
            with get_db_session() as session:
                logger.info("数据库连接成功")
                family = Family(id=str(uuid.uuid4()), name=name, owner_id=owner_id)
                session.add(family)
                session.flush()
                logger.info(f"Family表插入成功, id={family.id}")

                member = FamilyMember(
                    id=str(uuid.uuid4()),
                    family_id=family.id,
                    user_id=owner_id,
                    user_name=owner_name,
                    role="owner",
                    relationship_type="self",
                )
                session.add(member)
                logger.info(f"FamilyMember表插入成功")
                result = {
                    "id": family.id,
                    "name": family.name,
                    "owner_id": family.owner_id,
                    "created_at": family.created_at,
                }
                return result
        except Exception as e:
            logger.error(f"创建家庭失败: {e}", exc_info=True)
            raise

    @staticmethod
    def add_member(
        family_id: str,
        user_id: str,
        user_name: str,
        role: str,
        relationship_type: str,
        patient_id: Optional[str] = None,
    ) -> Dict:
        """添加家庭成员"""
        with get_db_session() as session:
            member = FamilyMember(
                id=str(uuid.uuid4()),
                family_id=family_id,
                user_id=user_id,
                user_name=user_name,
                role=role,
                relationship_type=relationship_type,
                patient_id=patient_id,
            )
            session.add(member)
            session.flush()
            return {
                "id": member.id,
                "family_id": member.family_id,
                "user_id": member.user_id,
                "user_name": member.user_name,
                "role": member.role,
                "relationship_type": member.relationship_type,
                "patient_id": member.patient_id,
            }

    @staticmethod
    def get_family_members(family_id: str) -> List[Dict]:
        """获取家庭成员列表"""
        with get_db_session() as session:
            result = session.execute(
                select(FamilyMember).where(FamilyMember.family_id == family_id)
            )
            members = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "family_id": m.family_id,
                    "user_id": m.user_id,
                    "user_name": m.user_name,
                    "role": m.role,
                    "relationship_type": m.relationship_type,
                    "phone": m.phone,
                    "notification_enabled": m.notification_enabled,
                    "patient_id": m.patient_id,
                }
                for m in members
            ]

    @staticmethod
    def get_user_families(user_id: str) -> List[Dict]:
        """获取用户所属家庭"""
        logger.info(f"查询用户 {user_id} 的家庭")
        with get_db_session() as session:
            result = session.execute(
                select(Family)
                .join(FamilyMember, Family.id == FamilyMember.family_id)
                .where(FamilyMember.user_id == user_id)
            )
            families = result.scalars().all()
            logger.info(f"找到 {len(families)} 个家庭")
            return [
                {
                    "id": f.id,
                    "name": f.name,
                    "owner_id": f.owner_id,
                    "created_at": f.created_at,
                }
                for f in families
            ]

    @staticmethod
    def get_patient_family(patient_id: str) -> Optional[Dict]:
        """获取患者关联的家庭"""
        with get_db_session() as session:
            result = session.execute(
                select(Family)
                .join(FamilyMember, Family.id == FamilyMember.family_id)
                .where(FamilyMember.patient_id == patient_id)
            )
            family = result.scalar_one_or_none()
            if not family:
                return None
            return {
                "id": family.id,
                "name": family.name,
                "owner_id": family.owner_id,
                "created_at": family.created_at,
            }

    def _generate_morning_message(self, context: Dict) -> str:
        template = self.config.time_triggers.get("morning", {}).get("template", "早上好！")
        weather_tip = context.get("weather_tip", "新的一天开始了")
        health_tip = context.get("health_tip", "记得吃早餐")
        return template.format(weather_tip=weather_tip, tip=health_tip)

    def _generate_evening_message(self, context: Dict) -> str:
        return "晚上好！今天辛苦了，记得早点休息~"

    def _generate_medication_message(self, context: Dict) -> str:
        template = self.config.time_triggers.get("medication", {}).get("template", "该{action}了")
        minutes = context.get("minutes", 15)
        action = context.get("action", "吃药")
        encouragement = context.get("encouragement", "坚持就是胜利！")
        return template.format(minutes=minutes, action=action, encouragement=encouragement)

    def _generate_health_alert_message(self, context: Dict) -> str:
        template = self.config.health_triggers.get("data_abnormal", {}).get("template", "")
        metric = context.get("metric", "指标")
        status = context.get("status", "异常")
        suggestion = context.get("suggestion", "要多注意休息")
        return template.format(metric=metric, status=status, suggestion=suggestion)

    def _generate_improved_message(self, context: Dict) -> str:
        template = self.config.health_triggers.get("data_improved", {}).get("template", "")
        metric = context.get("metric", "指标")
        return template.format(metric=metric)

    def _generate_stable_message(self, context: Dict) -> str:
        template = self.config.health_triggers.get("data_stable", {}).get("template", "")
        metric = context.get("metric", "数据")
        return template.format(metric=metric)

    def _generate_not_recorded_message(self, context: Dict) -> str:
        template = self.config.health_triggers.get("not_recorded", {}).get("template", "")
        days = context.get("days", 2)
        return template.format(days=days)

    def _generate_missed_message(self, context: Dict) -> str:
        template = self.config.behavior_triggers.get("medication_missed", {}).get("template", "")
        return template


class CareMessageService:
    """关怀消息服务"""

    @staticmethod
    def send_message(
        family_id: str,
        from_user_id: str,
        from_user_name: str,
        to_user_id: str,
        to_user_name: str,
        content: str,
        message_type: str = "manual",
    ) -> Dict:
        """发送关怀消息"""
        with get_db_session() as session:
            message = CareMessage(
                id=str(uuid.uuid4()),
                family_id=family_id,
                from_user_id=from_user_id,
                from_user_name=from_user_name,
                to_user_id=to_user_id,
                to_user_name=to_user_name,
                message_type=message_type,
                content=content,
            )
            session.add(message)
            session.flush()
            return {
                "id": message.id,
                "family_id": message.family_id,
                "from_user_id": message.from_user_id,
                "from_user_name": message.from_user_name,
                "to_user_id": message.to_user_id,
                "to_user_name": message.to_user_name,
                "content": message.content,
                "message_type": message.message_type,
                "is_read": message.is_read,
                "created_at": message.created_at,
            }

    @staticmethod
    def get_unread_messages(user_id: str) -> List[Dict]:
        """获取未读消息"""
        with get_db_session() as session:
            result = session.execute(
                select(CareMessage)
                .where(and_(CareMessage.to_user_id == user_id, CareMessage.is_read == False))
                .order_by(CareMessage.created_at.desc())
            )
            messages = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "family_id": m.family_id,
                    "from_user_id": m.from_user_id,
                    "from_user_name": m.from_user_name,
                    "to_user_id": m.to_user_id,
                    "to_user_name": m.to_user_name,
                    "content": m.content,
                    "message_type": m.message_type,
                    "is_read": m.is_read,
                    "created_at": m.created_at,
                }
                for m in messages
            ]

    @staticmethod
    def mark_as_read(message_id: str) -> None:
        """标记为已读"""
        with get_db_session() as session:
            result = session.execute(select(CareMessage).where(CareMessage.id == message_id))
            message = result.scalar_one_or_none()
            if message:
                message.is_read = True


class MemoryService:
    """记忆服务 - 用于AI陪伴"""

    @staticmethod
    def remember(
        user_id: str,
        memory_type: str,
        content: str,
        importance: int = 5,
        meta: Optional[Dict] = None,
    ) -> Dict:
        """存储记忆"""
        with get_db_session() as session:
            memory = UserMemory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                importance=importance,
                meta=meta or {},
            )
            session.add(memory)
            session.flush()
            return {
                "id": memory.id,
                "user_id": memory.user_id,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance": memory.importance,
                "meta": memory.meta,
                "created_at": memory.created_at,
                "last_accessed": memory.last_accessed,
            }

    @staticmethod
    def recall(user_id: str, context: str, limit: int = 5) -> List[Dict]:
        """检索记忆"""
        with get_db_session() as session:
            result = session.execute(
                select(UserMemory)
                .where(UserMemory.user_id == user_id)
                .order_by(UserMemory.importance.desc(), UserMemory.last_accessed.desc())
                .limit(limit)
            )
            memories = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "memory_type": m.memory_type,
                    "content": m.content,
                    "importance": m.importance,
                    "meta": m.meta,
                    "created_at": m.created_at,
                    "last_accessed": m.last_accessed,
                }
                for m in memories
            ]

    @staticmethod
    def update_access(memory_id: str) -> None:
        """更新访问时间"""
        with get_db_session() as session:
            result = session.execute(select(UserMemory).where(UserMemory.id == memory_id))
            memory = result.scalar_one_or_none()
            if memory:
                memory.last_accessed = datetime.utcnow()

    @staticmethod
    def get_conversation_summary(user_id: str, days: int = 7) -> str:
        """获取对话摘要（用于上下文）"""
        with get_db_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = session.execute(
                select(UserMemory)
                .where(
                    and_(
                        UserMemory.user_id == user_id,
                        UserMemory.memory_type == "conversation",
                        UserMemory.created_at >= cutoff,
                    )
                )
                .order_by(UserMemory.created_at.desc())
                .limit(10)
            )
            memories = result.scalars().all()

        if not memories:
            return ""

        summary_parts = [m.content[:100] for m in memories[:3]]
        return " | ".join(summary_parts)


class HealthAlertService:
    """健康预警服务"""

    @staticmethod
    def create_alert(
        patient_id: str,
        alert_type: str,
        title: str,
        content: str,
        severity: str = "medium",
        vital_type: Optional[str] = None,
        vital_value: Optional[Dict] = None,
    ) -> Dict:
        """创建预警"""
        with get_db_session() as session:
            alert = HealthAlert(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                alert_type=alert_type,
                title=title,
                content=content,
                severity=severity,
                vital_type=vital_type,
                vital_value=vital_value,
            )
            session.add(alert)
            session.flush()
            return {
                "id": alert.id,
                "patient_id": alert.patient_id,
                "alert_type": alert.alert_type,
                "title": alert.title,
                "content": alert.content,
                "severity": alert.severity,
                "is_resolved": alert.is_resolved,
                "vital_type": alert.vital_type,
                "vital_value": alert.vital_value,
                "created_at": alert.created_at,
            }

    @staticmethod
    def get_patient_alerts(patient_id: str, days: int = 7) -> List[Dict]:
        """获取患者预警列表"""
        with get_db_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = session.execute(
                select(HealthAlert)
                .where(and_(HealthAlert.patient_id == patient_id, HealthAlert.created_at >= cutoff))
                .order_by(HealthAlert.created_at.desc())
            )
            alerts = result.scalars().all()
            return [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "alert_type": a.alert_type,
                    "title": a.title,
                    "content": a.content,
                    "severity": a.severity,
                    "is_resolved": a.is_resolved,
                    "vital_type": a.vital_type,
                    "vital_value": a.vital_value,
                    "created_at": a.created_at,
                }
                for a in alerts
            ]


class MedicationComplianceService:
    """用药依从性服务"""

    @staticmethod
    def calculate_compliance(patient_id: str, days: int = 30) -> Dict[str, Any]:
        """计算用药依从性"""
        with get_db_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)

            result = session.execute(
                select(MedicationRecordEnhanced).where(
                    and_(
                        MedicationRecordEnhanced.patient_id == patient_id,
                        MedicationRecordEnhanced.scheduled_time >= cutoff,
                    )
                )
            )
            records = result.scalars().all()

            if not records:
                return {"compliance_rate": 0, "total": 0, "taken": 0, "missed": 0, "skipped": 0}

            total = len(records)
            taken = sum(1 for r in records if r.status == "taken")
            missed = sum(1 for r in records if r.status == "missed")
            skipped = sum(1 for r in records if r.status == "skipped")

            compliance_rate = (taken / total * 100) if total > 0 else 0

            return {
                "compliance_rate": round(compliance_rate, 1),
                "total": total,
                "taken": taken,
                "missed": missed,
                "skipped": skipped,
                "period_days": days,
            }

    @staticmethod
    def check_and_alert_missed_medication(patient_id: str) -> Optional[HealthAlert]:
        """检查并预警漏服药物"""
        with get_db_session() as session:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_time = datetime.utcnow() - timedelta(hours=2)

            result = session.execute(
                select(MedicationRecordEnhanced).where(
                    and_(
                        MedicationRecordEnhanced.patient_id == patient_id,
                        MedicationRecordEnhanced.status == "missed",
                        MedicationRecordEnhanced.scheduled_time >= today_start,
                        MedicationRecordEnhanced.scheduled_time <= cutoff_time,
                    )
                )
            )
            missed_records = result.scalars().all()

            if missed_records:
                drug_names = [r.drug_name for r in missed_records]
                alert = HealthAlertService.create_alert(
                    patient_id=patient_id,
                    alert_type="medication_missed",
                    title="用药提醒",
                    content=f"您今天还未服用{drug_names[0]}等药物，记得按时服药哦",
                    severity="medium",
                )
                return alert
        return None


class EncourageCardService:
    """鼓励卡片服务"""

    SYSTEM_CARDS = [
        {"name": "你真棒", "icon": "🌻", "content": "你真棒！继续保持，你做得很好！", "category": "praise"},
        {"name": "继续加油", "icon": "💪", "content": "继续加油！每一步都是进步！", "category": "encourage"},
        {"name": "想你了", "icon": "❤️", "content": "想你了！今天也要好好照顾自己哦~", "category": "care"},
        {"name": "今天也要按时吃药", "icon": "🎯", "content": "今天也要按时吃药哦！健康最重要！", "category": "reminder"},
        {"name": "为你骄傲", "icon": "🌟", "content": "为你骄傲！你的坚持让人感动！", "category": "praise"},
        {"name": "一起健康", "icon": "🤝", "content": "我们一起健康生活！你并不孤单！", "category": "care"},
        {"name": "进步明显", "icon": "📈", "content": "最近进步很明显呢！继续加油！", "category": "praise"},
        {"name": "别太累了", "icon": "🌙", "content": "别太累了，注意休息，身体最重要！", "category": "care"},
        {"name": "天气提醒", "icon": "☀️", "content": "今天天气不错，适合出去走走~", "category": "reminder"},
        {"name": "按时测量", "icon": "📊", "content": "记得按时测量血压/血糖哦！", "category": "reminder"},
    ]

    @staticmethod
    def init_system_cards():
        with get_db_session() as session:
            result = session.execute(
                select(EncourageCard).where(EncourageCard.is_system == True)
            )
            existing = result.scalars().all()
            if len(existing) > 0:
                return
            for card_data in EncourageCardService.SYSTEM_CARDS:
                card = EncourageCard(
                    id=str(uuid.uuid4()),
                    name=card_data["name"],
                    icon=card_data["icon"],
                    content=card_data["content"],
                    category=card_data["category"],
                    is_system=True,
                )
                session.add(card)

    @staticmethod
    def get_cards(user_id: Optional[str] = None) -> List[Dict]:
        with get_db_session() as session:
            query = select(EncourageCard).order_by(EncourageCard.is_system.desc(), EncourageCard.created_at.desc())
            result = session.execute(query)
            cards = result.scalars().all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "icon": c.icon,
                    "content": c.content,
                    "category": c.category,
                    "is_system": c.is_system,
                    "created_by": c.created_by,
                }
                for c in cards
            ]

    @staticmethod
    def create_custom_card(name: str, icon: str, content: str, category: str, created_by: str) -> Dict:
        with get_db_session() as session:
            card = EncourageCard(
                id=str(uuid.uuid4()),
                name=name,
                icon=icon,
                content=content,
                category=category,
                is_system=False,
                created_by=created_by,
            )
            session.add(card)
            session.flush()
            return {
                "id": card.id,
                "name": card.name,
                "icon": card.icon,
                "content": card.content,
                "category": card.category,
                "is_system": card.is_system,
            }

    @staticmethod
    def send_encourage_card(
        family_id: str,
        from_user_id: str,
        from_user_name: str,
        to_user_id: str,
        to_user_name: str,
        card_id: str,
    ) -> Dict:
        with get_db_session() as session:
            result = session.execute(select(EncourageCard).where(EncourageCard.id == card_id))
            card = result.scalar_one_or_none()
            if not card:
                raise ValueError("卡片不存在")

            message = CareMessage(
                id=str(uuid.uuid4()),
                family_id=family_id,
                from_user_id=from_user_id,
                from_user_name=from_user_name,
                to_user_id=to_user_id,
                to_user_name=to_user_name,
                message_type="encourage_card",
                content=f"{card.icon} {card.content}",
            )
            session.add(message)
            session.flush()

            FamilyActivityService.add_activity(
                family_id=family_id,
                user_id=from_user_id,
                user_name=from_user_name,
                activity_type="encourage_sent",
                content=f"{from_user_name} 给 {to_user_name} 发送了鼓励卡片 {card.icon} {card.name}",
                meta={"card_id": card_id, "card_name": card.name, "card_icon": card.icon, "to_user_id": to_user_id},
            )

            return {
                "id": message.id,
                "card_name": card.name,
                "card_icon": card.icon,
                "content": message.content,
                "created_at": message.created_at,
            }


class FamilyActivityService:
    """家庭动态服务"""

    @staticmethod
    def add_activity(
        family_id: str,
        user_id: str,
        user_name: str,
        activity_type: str,
        content: str,
        meta: Optional[Dict] = None,
    ) -> Dict:
        with get_db_session() as session:
            activity = FamilyActivity(
                id=str(uuid.uuid4()),
                family_id=family_id,
                user_id=user_id,
                user_name=user_name,
                activity_type=activity_type,
                content=content,
                meta=meta or {},
            )
            session.add(activity)
            session.flush()
            return {
                "id": activity.id,
                "family_id": activity.family_id,
                "user_id": activity.user_id,
                "user_name": activity.user_name,
                "activity_type": activity.activity_type,
                "content": activity.content,
                "meta": activity.meta,
                "created_at": activity.created_at,
            }

    @staticmethod
    def get_family_activities(family_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyActivity)
                .where(FamilyActivity.family_id == family_id)
                .order_by(FamilyActivity.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            activities = result.scalars().all()
            return [
                {
                    "id": a.id,
                    "family_id": a.family_id,
                    "user_id": a.user_id,
                    "user_name": a.user_name,
                    "activity_type": a.activity_type,
                    "content": a.content,
                    "meta": a.meta,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in activities
            ]

    @staticmethod
    def get_user_activities(user_id: str, limit: int = 10) -> List[Dict]:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyActivity)
                .where(FamilyActivity.user_id == user_id)
                .order_by(FamilyActivity.created_at.desc())
                .limit(limit)
            )
            activities = result.scalars().all()
            return [
                {
                    "id": a.id,
                    "family_id": a.family_id,
                    "user_id": a.user_id,
                    "user_name": a.user_name,
                    "activity_type": a.activity_type,
                    "content": a.content,
                    "meta": a.meta,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in activities
            ]


class FamilyInviteService:
    """家庭邀请服务"""

    @staticmethod
    def create_invite(
        family_id: str,
        inviter_id: str,
        inviter_name: str,
        relationship: str = "other",
        expires_hours: int = 72,
    ) -> Dict:
        import random
        import string
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        with get_db_session() as session:
            invite = FamilyInvite(
                id=str(uuid.uuid4()),
                family_id=family_id,
                inviter_id=inviter_id,
                inviter_name=inviter_name,
                invite_code=code,
                relationship_type=relationship,
                max_uses=1,
                used_count=0,
                expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
            )
            session.add(invite)
            session.flush()
            return {
                "id": invite.id,
                "family_id": invite.family_id,
                "invite_code": invite.invite_code,
                "relationship": invite.relationship_type,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                "created_at": invite.created_at.isoformat() if invite.created_at else None,
            }

    @staticmethod
    def accept_invite(invite_code: str, user_id: str, user_name: str) -> Dict:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyInvite).where(FamilyInvite.invite_code == invite_code)
            )
            invite = result.scalar_one_or_none()
            if not invite:
                raise ValueError("邀请码不存在")
            if invite.used_count >= invite.max_uses:
                raise ValueError("邀请码已使用")
            if invite.expires_at and invite.expires_at < datetime.utcnow():
                raise ValueError("邀请码已过期")

            existing = session.execute(
                select(FamilyMember).where(
                    and_(
                        FamilyMember.family_id == invite.family_id,
                        FamilyMember.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                raise ValueError("您已经是该家庭成员")

            member = FamilyMember(
                id=str(uuid.uuid4()),
                family_id=invite.family_id,
                user_id=user_id,
                user_name=user_name,
                role="member",
                relationship_type=invite.relationship_type,
            )
            session.add(member)

            invite.used_count += 1

            privacy = FamilyPrivacySetting(
                id=str(uuid.uuid4()),
                family_id=invite.family_id,
                user_id=user_id,
                can_view_health=True,
                can_view_medication=True,
                can_view_cognitive=False,
                can_view_training=False,
                can_send_encourage=True,
                can_receive_alerts=True,
            )
            session.add(privacy)
            session.flush()

            return {
                "success": True,
                "family_id": invite.family_id,
                "member_id": member.id,
                "role": member.role,
                "relationship": member.relationship_type,
            }


class FamilyPrivacyService:
    """家庭隐私设置服务"""

    @staticmethod
    def get_privacy_settings(family_id: str, user_id: str) -> Dict:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyPrivacySetting).where(
                    and_(
                        FamilyPrivacySetting.family_id == family_id,
                        FamilyPrivacySetting.user_id == user_id,
                    )
                )
            )
            setting = result.scalar_one_or_none()
            if not setting:
                return {
                    "family_id": family_id,
                    "user_id": user_id,
                    "can_view_health": True,
                    "can_view_medication": True,
                    "can_view_cognitive": False,
                    "can_view_training": False,
                    "can_send_encourage": True,
                    "can_receive_alerts": True,
                }
            return {
                "family_id": setting.family_id,
                "user_id": setting.user_id,
                "can_view_health": setting.can_view_health,
                "can_view_medication": setting.can_view_medication,
                "can_view_cognitive": setting.can_view_cognitive,
                "can_view_training": setting.can_view_training,
                "can_send_encourage": setting.can_send_encourage,
                "can_receive_alerts": setting.can_receive_alerts,
            }

    @staticmethod
    def update_privacy_settings(family_id: str, user_id: str, updates: Dict) -> Dict:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyPrivacySetting).where(
                    and_(
                        FamilyPrivacySetting.family_id == family_id,
                        FamilyPrivacySetting.user_id == user_id,
                    )
                )
            )
            setting = result.scalar_one_or_none()
            if not setting:
                setting = FamilyPrivacySetting(
                    id=str(uuid.uuid4()),
                    family_id=family_id,
                    user_id=user_id,
                )
                session.add(setting)
                session.flush()

            bool_fields = [
                "can_view_health", "can_view_medication", "can_view_cognitive",
                "can_view_training", "can_send_encourage", "can_receive_alerts",
            ]
            for field in bool_fields:
                if field in updates:
                    setattr(setting, field, bool(updates[field]))

            return {
                "family_id": setting.family_id,
                "user_id": setting.user_id,
                "can_view_health": setting.can_view_health,
                "can_view_medication": setting.can_view_medication,
                "can_view_cognitive": setting.can_view_cognitive,
                "can_view_training": setting.can_view_training,
                "can_send_encourage": setting.can_send_encourage,
                "can_receive_alerts": setting.can_receive_alerts,
            }

    @staticmethod
    def check_permission(family_id: str, user_id: str, permission: str) -> bool:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyPrivacySetting).where(
                    and_(
                        FamilyPrivacySetting.family_id == family_id,
                        FamilyPrivacySetting.user_id == user_id,
                    )
                )
            )
            setting = result.scalar_one_or_none()
            if not setting:
                return True
            return getattr(setting, permission, True)


class FamilyMemberAlertService:
    """家庭成员预警通知服务"""

    @staticmethod
    def notify_family_members(
        family_id: str,
        health_alert_id: str,
        patient_id: str,
        patient_name: str,
        alert_title: str,
        alert_content: str,
        severity: str = "medium",
    ) -> List[Dict]:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyMember).where(
                    and_(
                        FamilyMember.family_id == family_id,
                        FamilyMember.user_id != patient_id,
                        FamilyMember.notification_enabled == True,
                    )
                )
            )
            members = result.scalars().all()
            notified = []
            for member in members:
                privacy = session.execute(
                    select(FamilyPrivacySetting).where(
                        and_(
                            FamilyPrivacySetting.family_id == family_id,
                            FamilyPrivacySetting.user_id == member.user_id,
                        )
                    )
                ).scalar_one_or_none()

                if privacy and not privacy.can_receive_alerts:
                    continue

                alert = FamilyMemberAlert(
                    id=str(uuid.uuid4()),
                    family_id=family_id,
                    health_alert_id=health_alert_id,
                    patient_id=patient_id,
                    patient_name=patient_name,
                    notify_user_id=member.user_id,
                    notify_user_name=member.user_name,
                    alert_title=alert_title,
                    alert_content=alert_content,
                    severity=severity,
                )
                session.add(alert)
                notified.append({
                    "id": alert.id,
                    "notify_user_id": member.user_id,
                    "notify_user_name": member.user_name,
                })

            session.flush()
            return notified

    @staticmethod
    def get_member_alerts(user_id: str, unread_only: bool = False) -> List[Dict]:
        with get_db_session() as session:
            query = select(FamilyMemberAlert).where(
                FamilyMemberAlert.notify_user_id == user_id
            )
            if unread_only:
                query = query.where(FamilyMemberAlert.is_read == False)
            query = query.order_by(FamilyMemberAlert.created_at.desc())
            result = session.execute(query.limit(50))
            alerts = result.scalars().all()
            return [
                {
                    "id": a.id,
                    "family_id": a.family_id,
                    "patient_id": a.patient_id,
                    "patient_name": a.patient_name,
                    "alert_title": a.alert_title,
                    "alert_content": a.alert_content,
                    "severity": a.severity,
                    "is_read": a.is_read,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ]

    @staticmethod
    def mark_alert_read(alert_id: str) -> None:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyMemberAlert).where(FamilyMemberAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.is_read = True

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyMemberAlert).where(
                    and_(
                        FamilyMemberAlert.notify_user_id == user_id,
                        FamilyMemberAlert.is_read == False,
                    )
                )
            )
            return len(result.scalars().all())


class FamilyMemberService:
    """家庭成员管理增强服务"""

    @staticmethod
    def remove_member(family_id: str, member_id: str, operator_id: str) -> bool:
        with get_db_session() as session:
            family_result = session.execute(select(Family).where(Family.id == family_id))
            family = family_result.scalar_one_or_none()
            if not family:
                raise ValueError("家庭不存在")
            if family.owner_id != operator_id:
                raise ValueError("只有家庭创建者才能移除成员")

            result = session.execute(
                select(FamilyMember).where(
                    and_(
                        FamilyMember.id == member_id,
                        FamilyMember.family_id == family_id,
                    )
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError("成员不存在")
            if member.role == "owner":
                raise ValueError("不能移除家庭创建者")

            session.delete(member)
            return True

    @staticmethod
    def update_member(family_id: str, member_id: str, updates: Dict) -> Dict:
        with get_db_session() as session:
            result = session.execute(
                select(FamilyMember).where(
                    and_(
                        FamilyMember.id == member_id,
                        FamilyMember.family_id == family_id,
                    )
                )
            )
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError("成员不存在")

            for field in ["role", "relationship_type", "phone", "notification_enabled", "patient_id"]:
                if field in updates:
                    setattr(member, field, updates[field])

            return {
                "id": member.id,
                "user_id": member.user_id,
                "user_name": member.user_name,
                "role": member.role,
                "relationship_type": member.relationship_type,
                "phone": member.phone,
                "notification_enabled": member.notification_enabled,
                "patient_id": member.patient_id,
            }

    @staticmethod
    def get_family_stats(family_id: str) -> Dict:
        with get_db_session() as session:
            members_result = session.execute(
                select(FamilyMember).where(FamilyMember.family_id == family_id)
            )
            members = members_result.scalars().all()

            activities_result = session.execute(
                select(FamilyActivity)
                .where(FamilyActivity.family_id == family_id)
                .order_by(FamilyActivity.created_at.desc())
                .limit(100)
            )
            activities = activities_result.scalars().all()

            encourage_count = sum(1 for a in activities if a.activity_type == "encourage_sent")
            training_count = sum(1 for a in activities if a.activity_type == "training_completed")
            medication_count = sum(1 for a in activities if a.activity_type == "medication_taken")

            return {
                "member_count": len(members),
                "patient_count": sum(1 for m in members if m.patient_id),
                "recent_activities": len(activities),
                "encourage_count": encourage_count,
                "training_count": training_count,
                "medication_count": medication_count,
            }
