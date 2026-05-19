"""
亲情账号模块数据模型
包括：家庭、家庭成员、关怀消息、记忆存储
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class Family(Base):
    """家庭表"""

    __tablename__ = "families"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系 - 使用relationship而不是Mapped
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    care_messages = relationship(
        "CareMessage", back_populates="family", cascade="all, delete-orphan"
    )


class FamilyMember(Base):
    """家庭成员表"""

    __tablename__ = "family_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient_id: Mapped[Optional[str]] = mapped_column(String(36))

    # 关系
    family = relationship("Family", back_populates="members")


class CareMessage(Base):
    """关怀消息表"""

    __tablename__ = "care_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"))
    from_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_user_name: Mapped[str] = mapped_column(String(100))
    to_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_user_name: Mapped[str] = mapped_column(String(100))
    message_type: Mapped[str] = mapped_column(String(20))  # manual, auto, alert, reminder
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    family = relationship("Family", back_populates="care_messages")


class UserMemory(Base):
    """用户记忆表 - 用于AI陪伴的记忆存储"""

    __tablename__ = "user_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(
        String(20)
    )  # conversation, health, preference, emotion, family
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5)  # 1-10重要性评分
    meta: Mapped[Optional[dict]] = mapped_column(JSON)
    embedding: Mapped[Optional[str]] = mapped_column(Text)  # 向量嵌入存储（可选）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MedicationReminderEnhanced(Base):
    """增强版用药提醒"""

    __tablename__ = "medication_reminders_enhanced"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage: Mapped[str] = mapped_column(String(50))  # 用量，如"1片"
    frequency: Mapped[str] = mapped_column(String(50))  # 频率，如"每日3次"
    times: Mapped[list] = mapped_column(JSON)  # 具体时间点，如["08:00", "12:00", "20:00"]
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_children: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否通知子女
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MedicationRecordEnhanced(Base):
    """增强版服药记录"""

    __tablename__ = "medication_records_enhanced"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    reminder_id: Mapped[str] = mapped_column(String(36), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(100))
    dosage: Mapped[str] = mapped_column(String(50))
    scheduled_time: Mapped[datetime] = mapped_column(DateTime)
    taken_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))  # taken, missed, skipped
    skip_reason: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HealthAlert(Base):
    """健康预警记录"""

    __tablename__ = "health_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(
        String(50)
    )  # data_abnormal, medication_missed, follow_up, general
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, urgent
    vital_type: Mapped[Optional[str]] = mapped_column(String(50))  # blood_pressure, blood_sugar等
    vital_value: Mapped[Optional[dict]] = mapped_column(JSON)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FamilyRecipe(Base):
    """家庭菜谱表"""

    __tablename__ = "family_recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"))
    creator_id: Mapped[str] = mapped_column(String(36))
    creator_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    ingredients: Mapped[list] = mapped_column(JSON)  # 食材列表
    steps: Mapped[list] = mapped_column(JSON)  # 烹饪步骤
    cooking_time: Mapped[Optional[int]] = mapped_column(Integer)  # 烹饪时间（分钟）
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))  # easy, medium, hard
    nutrition: Mapped[Optional[dict]] = mapped_column(JSON)  # 营养成分
    tags: Mapped[Optional[list]] = mapped_column(JSON)  # 标签
    is_legacy: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否传承菜谱
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否家庭共享
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RecipeComment(Base):
    """菜谱评论"""

    __tablename__ = "recipe_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(36), ForeignKey("family_recipes.id"))
    user_id: Mapped[str] = mapped_column(String(36))
    user_name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EncourageCard(Base):
    """鼓励卡片模板"""

    __tablename__ = "encourage_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(30))
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FamilyActivity(Base):
    """家庭动态"""

    __tablename__ = "family_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    family = relationship("Family", backref="activities")


class FamilyInvite(Base):
    """家庭邀请"""

    __tablename__ = "family_invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), nullable=False)
    inviter_id: Mapped[str] = mapped_column(String(36), nullable=False)
    inviter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(20))
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    family = relationship("Family", backref="invites")


class FamilyPrivacySetting(Base):
    """家庭隐私设置"""

    __tablename__ = "family_privacy_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    can_view_health: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_medication: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_cognitive: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_training: Mapped[bool] = mapped_column(Boolean, default=False)
    can_send_encourage: Mapped[bool] = mapped_column(Boolean, default=True)
    can_receive_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    family = relationship("Family", backref="privacy_settings")


class FamilyMemberAlert(Base):
    """家庭成员预警通知"""

    __tablename__ = "family_member_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), ForeignKey("families.id"), nullable=False)
    health_alert_id: Mapped[str] = mapped_column(String(36), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    notify_user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    notify_user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_title: Mapped[str] = mapped_column(String(200), nullable=False)
    alert_content: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    family = relationship("Family", backref="member_alerts")
