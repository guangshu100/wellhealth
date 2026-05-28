"""
数据模型统一导出
"""

from app.models.models import (
    Patient,
    Disease,
    PatientDisease,
    Medication,
    VitalRecord,
    Conversation,
    Agent,
    Evaluation,
    KnowledgeItem,
    CognitiveAssessment,
    CognitiveTrainingSession,
)

from app.models.family_models import (
    Family,
    FamilyMember,
    CareMessage,
    UserMemory,
    MedicationReminderEnhanced,
    MedicationRecordEnhanced,
    HealthAlert,
    FamilyRecipe,
    RecipeComment,
    EncourageCard,
    FamilyActivity,
    FamilyInvite,
    FamilyPrivacySetting,
    FamilyMemberAlert,
)

from app.models.extension_models import (
    InsuranceMedicineCatalog,
    DrugInteraction,
    MedicineDosageRange,
    PatientExtension,
    ClosedLoopRecord,
    ElderlyCareRecord,
    ChildHealthRecord,
    MiningResultCache,
    PrescriptionReviewResult,
    HealthPlan,
)

__all__ = [
    # 基础模型
    "Patient",
    "Disease",
    "PatientDisease",
    "Medication",
    "VitalRecord",
    "Conversation",
    "Agent",
    "Evaluation",
    "KnowledgeItem",
    "CognitiveAssessment",
    "CognitiveTrainingSession",
    # 家庭模块模型
    "Family",
    "FamilyMember",
    "CareMessage",
    "UserMemory",
    "MedicationReminderEnhanced",
    "MedicationRecordEnhanced",
    "HealthAlert",
    "FamilyRecipe",
    "RecipeComment",
    "EncourageCard",
    "FamilyActivity",
    "FamilyInvite",
    "FamilyPrivacySetting",
    "FamilyMemberAlert",
    # 扩展模型 (Phase 0)
    "InsuranceMedicineCatalog",
    "DrugInteraction",
    "MedicineDosageRange",
    "PatientExtension",
    "ClosedLoopRecord",
    "ElderlyCareRecord",
    "ChildHealthRecord",
    "MiningResultCache",
    "PrescriptionReviewResult",
    "HealthPlan",
]
