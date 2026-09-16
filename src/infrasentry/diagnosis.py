from __future__ import annotations

from collections.abc import Iterable

from infrasentry.models import Diagnosis, Evidence, EvidenceStatus


def _index(evidence: Iterable[Evidence]) -> dict[str, Evidence]:
    return {item.key: item for item in evidence}


def diagnose(evidence: list[Evidence]) -> Diagnosis:
    """Return a deterministic first-pass diagnosis from collected evidence.

    AI reasoning will later sit *after* this layer, never in place of raw fact collection.
    """
    facts = _index(evidence)

    dns = facts.get("dns_resolution")
    target = facts.get("target_service")
    connectivity = facts.get("tcp_connectivity")

    if dns and dns.status is EvidenceStatus.FAIL:
        hostname = str(dns.details.get("hostname", "the configured service hostname"))
        return Diagnosis(
            title="DNS resolution failure",
            probable_root_cause=f"The application cannot resolve {hostname}.",
            remediation=(
                "Verify the configured service hostname, Kubernetes Service name, namespace, "
                "and cluster DNS health before restarting workloads."
            ),
            confidence=0.92,
            supporting_evidence=[dns.key],
        )

    if (
        target
        and target.status is EvidenceStatus.FAIL
        and connectivity
        and connectivity.status is EvidenceStatus.FAIL
    ):
        return Diagnosis(
            title="Target service unavailable",
            probable_root_cause="The dependency is unavailable and TCP connectivity fails.",
            remediation=(
                "Inspect the target workload, Service selectors and endpoints, then validate "
                "network policy and port configuration."
            ),
            confidence=0.86,
            supporting_evidence=[target.key, connectivity.key],
        )

    failed = [item.key for item in evidence if item.status is EvidenceStatus.FAIL]
    return Diagnosis(
        title="Cause not yet isolated",
        probable_root_cause="The current evidence is insufficient for a specific root cause.",
        remediation="Collect additional logs, events, DNS and connectivity evidence.",
        confidence=0.30 if failed else 0.15,
        supporting_evidence=failed,
    )
