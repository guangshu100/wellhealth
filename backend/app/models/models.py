"""
数据库模型定义
使用SQLAlchemy 2.0
"""

import hashlib
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class Patient(Base):
    """患者表"""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    diseases = relationship("PatientDisease", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    vitals = relationship("VitalRecord", back_populates="patient")
    conversations = relationship("Conversation", back_populates="patient")


class Disease(Base):
    """疾病表"""

    __tablename__ = "diseases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # diabetes, hypertension等
    icd_code: Mapped[Optional[str]] = mapped_column(String(20))  # ICD编码
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patients = relationship("PatientDisease", back_populates="disease")


class PatientDisease(Base):
    """患者-疾病关联表"""

    __tablename__ = "patient_diseases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    disease_id: Mapped[str] = mapped_column(String(36), ForeignKey("diseases.id"))
    diagnosed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    stage: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient", back_populates="diseases")
    disease = relationship("Disease", back_populates="patients")


class Medication(Base):
    """用药记录表"""

    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient", back_populates="medications")


class VitalRecord(Base):
    """体征记录表"""

    __tablename__ = "vital_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    vital_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[dict] = mapped_column(JSON)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # 关系
    patient = relationship("Patient", back_populates="vitals")


class Conversation(Base):
    """对话记录表"""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("patients.id"))
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50))
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient", back_populates="conversations")


class Agent(Base):
    """Agent配置表"""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Evaluation(Base):
    """评估记录表"""

    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    test_suite: Mapped[str] = mapped_column(String(50))  # 测试套件名称
    total_cases: Mapped[int] = mapped_column(Integer)
    passed_cases: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    login_type: Mapped[str] = mapped_column(String(20), default="password")  # password, wechat
    wx_openid: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    wx_session_key: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(
        String(20), default="patient"
    )  # patient, family, doctor, admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        if not self.password_hash:
            return False
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Permission(Base):
    """权限表"""

    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    """用户角色关联表"""

    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RolePermission(Base):
    """角色权限关联表"""

    __tablename__ = "role_permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"))
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeItem(Base):
    """知识条目表"""

    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50))  # disease, drug, food等
    tags: Mapped[list[str]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AgentLLMConfigModel(Base):
    __tablename__ = "agent_llm_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="default")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    temperature: Mapped[Optional[float]] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=2000)
    timeout: Mapped[Optional[int]] = mapped_column(Integer, default=120)
    fallback_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fallback_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config_source: Mapped[str] = mapped_column(String(20), default="database")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CognitiveAssessment(Base):
    __tablename__ = "cognitive_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    input_text: Mapped[Optional[str]] = mapped_column(Text)
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    overall_score: Mapped[Optional[int]] = mapped_column()
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))
    language_score: Mapped[Optional[int]] = mapped_column()
    memory_score: Mapped[Optional[int]] = mapped_column()
    executive_function_score: Mapped[Optional[int]] = mapped_column()
    attention_score: Mapped[Optional[int]] = mapped_column()
    confidence: Mapped[Optional[float]] = mapped_column()
    recommendations: Mapped[Optional[str]] = mapped_column(JSON)
    linguistic_features: Mapped[Optional[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CognitiveTrainingSession(Base):
    __tablename__ = "cognitive_training_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="intermediate")
    score: Mapped[Optional[int]] = mapped_column()
    accuracy: Mapped[Optional[float]] = mapped_column()
    duration_seconds: Mapped[Optional[int]] = mapped_column()
    details: Mapped[Optional[str]] = mapped_column(JSON)
    cognitive_domains: Mapped[Optional[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
