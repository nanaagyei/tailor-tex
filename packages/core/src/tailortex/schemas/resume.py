"""Resume plan and generated bullet schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SectionPlan(BaseModel):
    type: Literal["experience", "project", "education", "skills", "certifications"]
    source_ids: list[str] = Field(default_factory=list)
    selected_bullet_ids: list[str] = Field(default_factory=list)
    reason: str | None = None


class DoNotInsert(BaseModel):
    keyword: str
    reason: str


class KeywordStrategy(BaseModel):
    covered: list[str] = Field(default_factory=list)
    not_covered: list[str] = Field(default_factory=list)
    do_not_insert: list[DoNotInsert] = Field(default_factory=list)


class ResumePlan(BaseModel):
    resume_id: str
    target_job_id: str
    template_id: str = "ats-modern"
    sections: list[SectionPlan] = Field(default_factory=list)
    keyword_strategy: KeywordStrategy = Field(default_factory=KeywordStrategy)


class GeneratedBullet(BaseModel):
    id: str
    text: str
    source_bullet_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    jd_keywords_used: list[str] = Field(default_factory=list)
    validation_status: Literal["supported", "needs_confirmation", "rejected"] = "needs_confirmation"
    validation_notes: list[str] = Field(default_factory=list)


class TailoringOptions(BaseModel):
    mode: Literal["conservative", "impact_focused", "technical_depth", "research_focused"] = (
        "conservative"
    )
    target_role_family: str = "software_engineering"
    max_pages: int = 1
    allow_bold_keywords: bool = True
    allow_summary: bool = True
    llm_provider: str = "none"
    redaction_enabled: bool = False
    require_user_confirmation_for_metrics: bool = True
