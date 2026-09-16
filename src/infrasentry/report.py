from __future__ import annotations

from infrasentry.diagnosis import diagnose
from infrasentry.models import Evidence, IncidentReport


def build_report(incident: str, evidence: list[Evidence]) -> IncidentReport:
    return IncidentReport(
        incident=incident,
        evidence=evidence,
        diagnosis=diagnose(evidence),
    )
