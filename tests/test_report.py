from infrasentry.models import Evidence, EvidenceStatus
from infrasentry.report import build_report, score_evidence_completeness


def test_completeness_counts_known_evidence() -> None:
    evidence = [
        Evidence(key="pod_status", status=EvidenceStatus.OK, summary="Pod ready"),
        Evidence(key="dns_resolution", status=EvidenceStatus.FAIL, summary="Lookup failed"),
        Evidence(key="container_logs", status=EvidenceStatus.UNKNOWN, summary="Not collected"),
    ]

    completeness = score_evidence_completeness(evidence)

    assert completeness.score == 2 / 3
    assert completeness.observed == 2
    assert completeness.total == 3
    assert completeness.unknown_evidence == ["container_logs"]


def test_report_exposes_completeness() -> None:
    report = build_report(
        "API outage",
        [Evidence(key="pod_status", status=EvidenceStatus.UNKNOWN, summary="Not collected")],
    )

    assert report.evidence_completeness.score == 0.0
    assert report.evidence_completeness.unknown_evidence == ["pod_status"]


def test_empty_evidence_has_zero_completeness() -> None:
    completeness = score_evidence_completeness([])

    assert completeness.score == 0.0
    assert completeness.observed == 0
    assert completeness.total == 0
