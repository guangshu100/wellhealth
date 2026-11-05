"""Versioned contracts: identity is never accepted from request JSON."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

AGENTS = {
    "diabetes": "糖尿病健康顾问", "hypertension": "血压管理顾问",
    "nutrition": "营养顾问", "coach": "运动健康顾问", "medication": "用药信息顾问",
}
DISCLAIMER = "AI 多专家角色仅提供健康信息，不代表真实医生会诊，不作诊断或替代专业医疗建议。用药调整请咨询医生。"
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class PatientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_range: str = Field(default="", max_length=20)
    gender: Literal["", "male", "female", "other"] = ""
    diseases: list[ShortText] = Field(default_factory=list, max_length=10)
    medications: list[ShortText] = Field(default_factory=list, max_length=10)


class CreateSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="新会诊", max_length=60)


class CreateRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    agent_types: list[str] = Field(default_factory=lambda: ["diabetes", "nutrition", "coach"],
                                  min_length=2, max_length=3)
    rounds: int = Field(default=2, ge=1, le=2)
    patient_context: PatientContext = Field(default_factory=PatientContext)

    @field_validator("message")
    @classmethod
    def trim_message(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()

    @field_validator("agent_types")
    @classmethod
    def validate_agents(cls, value):
        if len(set(value)) != len(value) or any(a not in AGENTS for a in value):
            raise ValueError("Unsupported or duplicate consultation agent")
        return value
