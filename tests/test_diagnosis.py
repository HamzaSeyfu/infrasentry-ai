from infrasentry.diagnosis import diagnose
from infrasentry.models import Evidence, EvidenceStatus


def test_dns_failure_is_prioritized() -> None:
    evidence = [
        Evidence(
            key="target_service",
            status=EvidenceStatus.OK,
            summary="Service exists",
        ),
        Evidence(
            key="dns_resolution",
            status=EvidenceStatus.FAIL,
            summary="Lookup failed",
            details={"hostname": "db.internal"},
        ),
        Evidence(
            key="tcp_connectivity",
            status=EvidenceStatus.FAIL,
            summary="Connection failed",
        ),
    ]

    diagnosis = diagnose(evidence)

    assert diagnosis.title == "DNS resolution failure"
    assert "db.internal" in diagnosis.probable_root_cause
    assert diagnosis.confidence >= 0.9


def test_unavailable_service_is_detected() -> None:
    evidence = [
        Evidence(
            key="target_service",
            status=EvidenceStatus.FAIL,
            summary="No ready endpoints",
        ),
        Evidence(
            key="tcp_connectivity",
            status=EvidenceStatus.FAIL,
            summary="Connection refused",
        ),
    ]

    diagnosis = diagnose(evidence)

    assert diagnosis.title == "Target service unavailable"
    assert set(diagnosis.supporting_evidence) == {"target_service", "tcp_connectivity"}


def test_unknown_case_requests_more_evidence() -> None:
    diagnosis = diagnose(
        [
            Evidence(
                key="pod_status",
                status=EvidenceStatus.OK,
                summary="Pod is ready",
            )
        ]
    )

    assert diagnosis.title == "Cause not yet isolated"
    assert diagnosis.confidence < 0.5
