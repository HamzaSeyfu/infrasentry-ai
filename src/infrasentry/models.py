from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceStatus(StrEnum):
    OK = "ok"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    key: str
    status: EvidenceStatus
    summary: str
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    title: str
    probable_root_cause: str
    remediation: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    incident: str
    evidence: list[Evidence]
    diagnosis: Diagnosis
