"""Parsed job description schema."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class JDSource(BaseModel):
    type: Literal["pasted_text", "url", "file"]
    url: str | None = None


class RoleSignals(BaseModel):
    backend: float = 0.0
    frontend: float = 0.0
    machine_learning: float = 0.0
    qa: float = 0.0
    leadership: float = 0.0


class ParsedJobDescription(BaseModel):
    job_id: str
    source: JDSource
    company: str | None = None
    role_title: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    domain_keywords: list[str] = Field(default_factory=list)
    role_signals: RoleSignals = Field(default_factory=RoleSignals)
    prompt_injection_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class JDRecord(BaseModel):
    jd: ParsedJobDescription
    raw_text: str
    warnings: list[str] = Field(default_factory=list)
