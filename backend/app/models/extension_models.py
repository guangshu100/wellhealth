"""
Phase 0 扩展数据库模型定义
包含医保目录、药物相互作用、剂量范围、患者扩展、闭环管理、
老年护理、儿童健康、数据挖掘缓存、处方审核、健康计划等表
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.utils.database import Base


class InsuranceMedicineCatalog(Base):
    """医保药品目录表"""

    __tablename__ = "insurance_medicine_catalog"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    drug_code: Mapped[str] = mapped_column(String(20), index=True)
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specification: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(10), nullable=False)  # 甲类/乙类
    reimbursement_rate: Mapped[float] = mapped_column(Float, nullable=False)
    restrictions: Mapped[Optional[str]] = mapped_column(Text)
    dosage_form: Mapped[str] = mapped_column(String(50), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DrugInteraction(Base):
    """药物相互作用表"""

    __tablename__ = "drug_interaction"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    drug_a_code: Mapped[str] = mapped_column(String(20), index=True)
    drug_a_name: Mapped[str] = mapped_column(String(100), nullable=False)
    drug_b_code: Mapped[str] = mapped_column(String(20), index=True)
    drug_b_name: Mapped[str] = mapped_column(String(100), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical/major/moderate/minor
    mechanism: Mapped[Optional[str]] = mapped_column(Text)
    clinical_effect: Mapped[Optional[str]] = mapped_column(Text)
    management: Mapped[Optional[str]] = mapped_column(Text)
    evidence_source: Mapped[Optional[str]] = mapped_column(String(200))
    evidence_level: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MedicineDosageRange(Base):
    """药品剂量范围表"""

    __tablename__ = "medicine_dosage_range"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    drug_code: Mapped[str] = mapped_column(String(20), index=True)
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    indication: Mapped[Optional[str]] = mapped_column(String(200))
    age_group: Mapped[Optional[str]] = mapped_column(String(50))
    renal_function: Mapped[Optional[str]] = mapped_column(String(50))
    min_dose: Mapped[Optional[float]] = mapped_column(Float)
    max_dose: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    frequency: Mapped[Optional[str]] = mapped_column(String(50))
    route: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PatientExtension(Base):
    """患者扩展信息表"""

    __tablename__ = "patient_extension"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    ethnicity: Mapped[Optional[str]] = mapped_column(String(20))
    region: Mapped[Optional[str]] = mapped_column(String(50))
    region_type: Mapped[Optional[str]] = mapped_column(String(20))
    diet_type: Mapped[Optional[str]] = mapped_column(String(50))
    smoking_status: Mapped[Optional[str]] = mapped_column(String(20))
    drinking_status: Mapped[Optional[str]] = mapped_column(String(20))
    occupation: Mapped[Optional[str]] = mapped_column(String(50))
    education_level: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    patient = relationship("Patient")


class ClosedLoopRecord(Base):
    """闭环管理记录表"""

    __tablename__ = "closed_loop_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    triage_id: Mapped[Optional[str]] = mapped_column(String(36))
    internet_hospital_session_id: Mapped[Optional[str]] = mapped_column(String(100))
    prescription_id: Mapped[Optional[str]] = mapped_column(String(36))
    follow_up_plan_id: Mapped[Optional[str]] = mapped_column(String(36))
    loop_status: Mapped[str] = mapped_column(String(20), index=True)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False)
    step_history: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient")


class ElderlyCareRecord(Base):
    """老年护理评估记录表"""

    __tablename__ = "elderly_care_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    fall_risk_score: Mapped[Optional[float]] = mapped_column(Float)
    fall_risk_level: Mapped[Optional[str]] = mapped_column(String(10))
    cognitive_score: Mapped[Optional[int]] = mapped_column(Integer)
    cognitive_level: Mapped[Optional[str]] = mapped_column(String(10))
    polypharmacy_count: Mapped[Optional[int]] = mapped_column(Integer)
    polypharmacy_review_status: Mapped[Optional[str]] = mapped_column(String(20))
    living_alone: Mapped[Optional[bool]] = mapped_column(Boolean)
    assistive_devices: Mapped[Optional[dict]] = mapped_column(JSON)
    assessment_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    patient = relationship("Patient")


class ChildHealthRecord(Base):
    """儿童健康评估记录表"""

    __tablename__ = "child_health_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    height_percentile: Mapped[Optional[float]] = mapped_column(Float)
    weight_percentile: Mapped[Optional[float]] = mapped_column(Float)
    bmi_percentile: Mapped[Optional[float]] = mapped_column(Float)
    vaccination_records: Mapped[Optional[dict]] = mapped_column(JSON)
    vaccination_next_due: Mapped[Optional[datetime]] = mapped_column(DateTime)
    screening_results: Mapped[Optional[dict]] = mapped_column(JSON)
    growth_standard_source: Mapped[Optional[str]] = mapped_column(String(20))
    assessment_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    patient = relationship("Patient")


class MiningResultCache(Base):
    """数据挖掘结果缓存表"""

    __tablename__ = "mining_result_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_type: Mapped[str] = mapped_column(String(50))
    parameters: Mapped[Optional[str]] = mapped_column(String(500))
    result_data: Mapped[Optional[str]] = mapped_column(Text)
    data_range_start: Mapped[Optional[datetime]] = mapped_column(Date)
    data_range_end: Mapped[Optional[datetime]] = mapped_column(Date)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_mock: Mapped[Optional[int]] = mapped_column(Integer)
    create_time: Mapped[Optional[datetime]] = mapped_column(DateTime)


class PrescriptionReviewResult(Base):
    """处方审核结果表"""

    __tablename__ = "prescription_review_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(String(36), index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    reviewer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    issues: Mapped[Optional[dict]] = mapped_column(JSON)
    suggestions: Mapped[Optional[dict]] = mapped_column(JSON)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient")


class HealthPlan(Base):
    """健康计划表"""

    __tablename__ = "health_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    plan_type: Mapped[str] = mapped_column(String(30), nullable=False)
    goals: Mapped[Optional[dict]] = mapped_column(JSON)
    milestones: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    patient = relationship("Patient")
