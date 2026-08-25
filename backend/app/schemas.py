from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchCreate(BaseModel):
    question: str = Field(min_length=12, max_length=1200)
    depth: Literal["quick", "standard", "deep"] = "standard"

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        return " ".join(value.split())


class SourceOut(BaseModel):
    source_key: str
    title: str
    url: str
    domain: str
    snippet: str | None
    fetch_status: str

    model_config = {"from_attributes": True}


class ClaimOut(BaseModel):
    claim_text: str
    verdict: str
    confidence: float
    grounding_score: float
    source_keys: list[str]
    note: str | None

    model_config = {"from_attributes": True}


class ResearchRunOut(BaseModel):
    id: str
    question: str
    depth: str
    status: str
    stage: str
    progress: int
    plan: list[str] | None
    summary: str | None
    report_markdown: str | None
    warnings: list[str] | None
    model_name: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    sources: list[SourceOut] = Field(default_factory=list)
    claims: list[ClaimOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ResearchListItem(BaseModel):
    id: str
    question: str
    depth: str
    status: str
    stage: str
    progress: int
    summary: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    total_sources: int
