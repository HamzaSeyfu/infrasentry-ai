from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceStatus(StrEnum):
    OK = "ok"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    key: str
    status: EvidenceStatus
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)


class IncidentInput(BaseModel):
    incident: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class Diagnosis(BaseModel):
    title: str
    probable_root_cause: str
    remediation: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)


class EvidenceCompleteness(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    observed: int = Field(ge=0)
    total: int = Field(ge=0)
    unknown_evidence: list[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    incident: str
    evidence: list[Evidence]
    diagnosis: Diagnosis
    evidence_completeness: EvidenceCompleteness
