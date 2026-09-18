from __future__ import annotations

from infrasentry.diagnosis import diagnose
from infrasentry.models import Evidence, EvidenceCompleteness, EvidenceStatus, IncidentReport


def score_evidence_completeness(evidence: list[Evidence]) -> EvidenceCompleteness:
    """Measure how much of the supplied evidence has a known observation."""
    unknown = [item.key for item in evidence if item.status is EvidenceStatus.UNKNOWN]
    total = len(evidence)
    observed = total - len(unknown)
    score = observed / total if total else 0.0
    return EvidenceCompleteness(
        score=score,
        observed=observed,
        total=total,
        unknown_evidence=unknown,
    )


def build_report(incident: str, evidence: list[Evidence]) -> IncidentReport:
    return IncidentReport(
        incident=incident,
        evidence=evidence,
        diagnosis=diagnose(evidence),
        evidence_completeness=score_evidence_completeness(evidence),
    )
