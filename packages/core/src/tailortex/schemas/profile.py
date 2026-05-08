"""Canonical profile schema — the source of truth for resume generation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Link(BaseModel):
    label: str
    url: str


class Owner(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[Link] = Field(default_factory=list)


class Summary(BaseModel):
    source_text: str
    approved: bool = False


class SourceRef(BaseModel):
    document_id: str
    line_range: tuple[int, int] | None = None


class Source(BaseModel):
    type: Literal["resume_import", "manual", "linkedin_import"]
    path: str | None = None
    line_range: tuple[int, int] | None = None


class Bullet(BaseModel):
    id: str
    text: str
    skills: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    approved: bool = False


class Experience(BaseModel):
    id: str
    organization: str
    title: str
    location: str | None = None
    start_date: str  # ISO 8601 partial date, e.g. "2024-11"
    end_date: str | None = None
    is_current: bool = False
    source: Source | None = None
    approved: bool = False
    bullets: list[Bullet] = Field(default_factory=list)


class Project(BaseModel):
    id: str
    name: str
    description: str | None = None
    url: str | None = None
    skills: list[str] = Field(default_factory=list)
    bullets: list[Bullet] = Field(default_factory=list)
    approved: bool = False


class Education(BaseModel):
    id: str
    institution: str
    degree: str
    field: str
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    approved: bool = False


class Skill(BaseModel):
    name: str
    category: str | None = None
    proficiency: Literal["beginner", "intermediate", "advanced"] | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    approved: bool = False


class Certification(BaseModel):
    id: str
    name: str
    issuer: str
    date: str | None = None
    url: str | None = None
    approved: bool = False


class Publication(BaseModel):
    id: str
    title: str
    venue: str | None = None
    date: str | None = None
    url: str | None = None
    approved: bool = False


class Award(BaseModel):
    id: str
    title: str
    issuer: str | None = None
    date: str | None = None
    approved: bool = False


class EvidenceLedgerEntry(BaseModel):
    id: str
    claim_type: Literal["experience", "project", "education", "skill", "certification"]
    source_text: str
    normalized_claim: str
    source_ref: SourceRef
    allowed_transformations: list[str] = Field(default_factory=list)
    blocked_transformations: list[str] = Field(default_factory=list)
    requires_user_confirmation: bool = False


class CanonicalProfile(BaseModel):
    profile_id: str = "default"
    version: str = "1.0.0"
    owner: Owner
    summary: Summary | None = None
    experiences: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    evidence_ledger: list[EvidenceLedgerEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
