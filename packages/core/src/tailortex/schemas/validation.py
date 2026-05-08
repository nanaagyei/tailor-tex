"""Validation report schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClaimResult(BaseModel):
    claim: str
    status: Literal["supported", "needs_confirmation", "rejected"]
    evidence_ids: list[str] = Field(default_factory=list)


class Warning(BaseModel):
    type: str
    message: str


class ValidationSummary(BaseModel):
    supported_claims: int = 0
    needs_confirmation: int = 0
    rejected_claims: int = 0
    latex_errors: int = 0
    warnings: int = 0


class ValidationReport(BaseModel):
    resume_id: str
    status: Literal["passed", "passed_with_warnings", "failed"] = "passed"
    summary: ValidationSummary = Field(default_factory=ValidationSummary)
    claims: list[ClaimResult] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
